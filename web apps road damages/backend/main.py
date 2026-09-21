"""
Road Damage Detection - FastAPI Backend
Supports Bounding Box and Dual Segmentation Models.
"""

import base64
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Compatibility patch: alias ALL legacy ultralytics numeric-suffixed classes
# Models trained with older ultralytics used class names like Segment26, Proto26,
# C2f19, Detect26, etc. Newer versions dropped the numeric suffix.
# This patch dynamically adds aliases so torch.load/pickle can resolve them.
# ---------------------------------------------------------------------------
try:
    import ultralytics.nn.modules.head as _head
    import ultralytics.nn.modules.block as _block
    import ultralytics.nn.modules.conv as _conv
    import ultralytics.nn.tasks as _tasks

    def _patch_module_with_numeric_aliases(mod):
        """For every class in module, create Name+N aliases for common suffixes."""
        known = {name: getattr(mod, name) for name in dir(mod)
                 if isinstance(getattr(mod, name, None), type)}
        for base_name, cls in list(known.items()):
            for n in range(1, 60):
                alias = f"{base_name}{n}"
                if not hasattr(mod, alias):
                    setattr(mod, alias, cls)

    import torch.nn as _nn

    class CustomSemanticSegment(_nn.Module):
        def __init__(self): super().__init__()
        def forward(self, x):
            # Fallback for semantic seg models that just return a classifier output
            return self.classifier(x[0]) if isinstance(x, list) else self.classifier(x)

    # Alias Semantic* classes to their closest modern equivalent BEFORE patching
    if not hasattr(_head, "SemanticSegment"):
        _head.SemanticSegment = CustomSemanticSegment
    if not hasattr(_tasks, "SemanticSegmentationModel"):
        _tasks.SemanticSegmentationModel = _tasks.SegmentationModel

    _patch_module_with_numeric_aliases(_head)
    _patch_module_with_numeric_aliases(_block)
    _patch_module_with_numeric_aliases(_conv)
    _patch_module_with_numeric_aliases(_tasks)

    print("[compat patch] Legacy class aliases registered successfully.")
except Exception as _patch_err:
    print(f"[compat patch] Warning: {_patch_err}")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
MODEL_BBOX_PATH = BASE_DIR / "models" / "best (4).pt"
MODEL_SEG_POTHOLE_PATH = BASE_DIR / "models" / "pothole_best_model_segmentation.pt"
MODEL_SEG_CRACK_PATH = BASE_DIR / "models" / "crack_best_model_segmentation.pt"

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png"}
ALLOWED_VIDEO_EXT = {".mp4", ".mov", ".mpeg"}

# OpenCV BGR colors
CLASS_COLORS = {
    "Crack": (0, 215, 255),    # yellow/gold
    "Pothole": (0, 0, 255),    # red
}

# The class indices for the bounding box model (0: Crack, 1: Pothole as per user's edit)
BBOX_CLASS_NAMES = {
    0: "Crack",
    1: "Pothole",
}

CONF_THRESHOLD = 0.3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_model_bbox = None
_model_seg_pothole = None
_model_seg_crack = None
_model_loaded = False

@app.on_event("startup")
async def startup_event():
    global _model_bbox, _model_seg_pothole, _model_seg_crack, _model_loaded
    try:
        if MODEL_BBOX_PATH.exists():
            _model_bbox = YOLO(str(MODEL_BBOX_PATH))
        if MODEL_SEG_POTHOLE_PATH.exists():
            _model_seg_pothole = YOLO(str(MODEL_SEG_POTHOLE_PATH))
        if MODEL_SEG_CRACK_PATH.exists():
            _model_seg_crack = YOLO(str(MODEL_SEG_CRACK_PATH))
            # The crack model was trained with task='semantic', but ultralytics 8.3+
            # does not support predict for 'semantic'. Force it to 'segment' which
            # uses the same architecture and allows predict to work correctly.
            if _model_seg_crack.task == "semantic":
                _model_seg_crack.task = "segment"
                if hasattr(_model_seg_crack, "model") and hasattr(_model_seg_crack.model, "task"):
                    _model_seg_crack.model.task = "segment"
                print("[startup] Crack model task overridden: semantic -> segment")
        _model_loaded = True
        print("[startup] Models loaded successfully.")
    except Exception as exc:
        print(f"[startup] Failed to load models: {exc}")

def _get_bbox_model() -> YOLO:
    if not _model_loaded or _model_bbox is None:
        raise HTTPException(status_code=503, detail="BBox model not available.")
    return _model_bbox

def _get_seg_models():
    if not _model_loaded or _model_seg_pothole is None or _model_seg_crack is None:
        raise HTTPException(status_code=503, detail="Segmentation models not available.")
    return _model_seg_pothole, _model_seg_crack

async def _read_and_validate_size(file: UploadFile) -> bytes:
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large.")
    return data

def _validate_image_ext(filename: str):
    if Path(filename).suffix.lower() not in ALLOWED_IMAGE_EXT:
        raise HTTPException(status_code=415, detail="Unsupported image format.")

def _validate_video_ext(filename: str):
    if Path(filename).suffix.lower() not in ALLOWED_VIDEO_EXT:
        raise HTTPException(status_code=415, detail="Unsupported video format.")

def _draw_box_with_label(frame, x1, y1, x2, y2, label, color):
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), baseline = cv2.getTextSize(label, font, 0.6, 2)
    pad = 4
    if y1 - text_h - baseline - pad * 2 >= 0:
        bg_y1 = y1 - text_h - baseline - pad * 2
        bg_y2 = y1
        txt_y = y1 - baseline - pad
    else:
        bg_y1 = y1
        bg_y2 = y1 + text_h + baseline + pad * 2
        txt_y = y1 + text_h + pad
    cv2.rectangle(frame, (x1, bg_y1), (x1 + text_w + pad * 2, bg_y2), color, -1)
    cv2.putText(frame, label, (x1 + pad, txt_y), font, 0.6, (255, 255, 255), 2)

def _draw_segmentation(frame, result, class_name, color):
    # YOLO segmentation masks
    if result.masks is not None and result.masks.data is not None:
        masks = result.masks.data.cpu().numpy()
        for mask in masks:
            # Resize mask to frame shape
            mask_resized = cv2.resize(mask, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
            colored_mask = np.zeros_like(frame)
            colored_mask[mask_resized > 0.5] = color
            # Alpha blending
            cv2.addWeighted(colored_mask, 0.4, frame, 1.0, 0, frame)
            
    # Also draw boxes if available to show confidence
    if result.boxes is not None and len(result.boxes):
        boxes_xyxy = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        for box, conf in zip(boxes_xyxy, confidences):
            x1, y1, x2, y2 = map(int, box)
            label = f"{class_name} {conf*100:.0f}%"
            _draw_box_with_label(frame, x1, y1, x2, y2, label, color)

def _draw_counter_overlay(frame, pothole_count, crack_count):
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (220, 85), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, f"Pothole: {pothole_count}", (20, 40), font, 0.75, CLASS_COLORS["Pothole"], 2)
    cv2.putText(frame, f"Crack:   {crack_count}",   (20, 72), font, 0.75, CLASS_COLORS["Crack"], 2)

def _reencode_to_h264(input_path, output_path):
    try:
        r = subprocess.run(["ffmpeg", "-y", "-i", input_path, "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "fast", output_path], capture_output=True, timeout=300)
        return r.returncode == 0
    except:
        return False

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": _model_loaded}

@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...), model_type: str = Form("bbox")):
    _validate_image_ext(file.filename or "image.jpg")
    data = await _read_and_validate_size(file)

    arr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=422, detail="Could not decode image.")
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    detections = []
    pothole_count = 0
    crack_count = 0

    if model_type == "segmentation":
        m_pothole, m_crack = _get_seg_models()
        # Run Pothole
        res_pothole = m_pothole.predict(frame_rgb, conf=CONF_THRESHOLD, imgsz=640, verbose=False)[0]
        _draw_segmentation(frame, res_pothole, "Pothole", CLASS_COLORS["Pothole"])
        if res_pothole.boxes is not None:
            pothole_count += len(res_pothole.boxes)
            
        # Run Crack (Manual inference for Semantic Segmentation)
        import torch
        img_tensor = cv2.resize(frame_rgb, (640, 640))
        img_tensor = img_tensor.transpose(2, 0, 1) # HWC to CHW
        img_tensor = torch.from_numpy(img_tensor).float().div(255.0).unsqueeze(0).to(m_crack.device)
        
        with torch.no_grad():
            out_crack = m_crack.model(img_tensor) # [1, 1, 80, 80]
        
        mask_crack = torch.sigmoid(out_crack[0, 0]).cpu().numpy()
        mask_crack_resized = cv2.resize(mask_crack, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
        
        colored_mask = np.zeros_like(frame)
        colored_mask[mask_crack_resized > 0.5] = CLASS_COLORS["Crack"]
        cv2.addWeighted(colored_mask, 0.4, frame, 1.0, 0, frame)
        
        if np.any(mask_crack_resized > 0.5):
            crack_count += 1


    else:
        # BBox
        model = _get_bbox_model()
        result = model.predict(frame_rgb, conf=CONF_THRESHOLD, imgsz=640, verbose=False)[0]
        if result.boxes is not None and len(result.boxes):
            for box, cls, conf in zip(result.boxes.xyxy.cpu().numpy(), result.boxes.cls.cpu().numpy(), result.boxes.conf.cpu().numpy()):
                cls_int = int(cls)
                class_name = BBOX_CLASS_NAMES.get(cls_int, f"Class {cls_int}")
                x1, y1, x2, y2 = map(int, box)
                _draw_box_with_label(frame, x1, y1, x2, y2, f"{class_name} {conf*100:.0f}%", CLASS_COLORS.get(class_name, (200,200,200)))
                if class_name == "Pothole": pothole_count += 1
                elif class_name == "Crack": crack_count += 1

    success, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    image_b64 = base64.b64encode(encoded.tobytes()).decode("utf-8")

    return JSONResponse({
        "image_base64": image_b64,
        "pothole_count": pothole_count,
        "crack_count": crack_count,
        "detections": detections, # optional detailed array
    })

@app.post("/predict/video")
async def predict_video(file: UploadFile = File(...), model_type: str = Form("bbox")):
    _validate_video_ext(file.filename or "video.mp4")
    data = await _read_and_validate_size(file)

    tmp_dir = tempfile.mkdtemp()
    uid = uuid.uuid4().hex
    input_path = os.path.join(tmp_dir, f"in_{uid}.mp4")
    raw_path = os.path.join(tmp_dir, f"raw_{uid}.mp4")
    final_path = os.path.join(tmp_dir, f"out_{uid}.mp4")

    with open(input_path, "wb") as f:
        f.write(data)

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(raw_path, fourcc, fps, (width, height))

    seen_potholes = set()
    seen_cracks = set()
    frame_count = 0
    t0 = time.time()

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame_count += 1
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if model_type == "segmentation":
            m_pothole, m_crack = _get_seg_models()
            res_pothole = m_pothole.predict(frame_rgb, conf=CONF_THRESHOLD, imgsz=640, verbose=False)[0]
            _draw_segmentation(frame, res_pothole, "Pothole", CLASS_COLORS["Pothole"])
            
            import torch
            img_tensor = cv2.resize(frame_rgb, (640, 640))
            img_tensor = img_tensor.transpose(2, 0, 1) # HWC to CHW
            img_tensor = torch.from_numpy(img_tensor).float().div(255.0).unsqueeze(0).to(m_crack.device)
            
            with torch.no_grad():
                out_crack = m_crack.model(img_tensor)
            
            mask_crack = torch.sigmoid(out_crack[0, 0]).cpu().numpy()
            mask_crack_resized = cv2.resize(mask_crack, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
            
            colored_mask = np.zeros_like(frame)
            colored_mask[mask_crack_resized > 0.5] = CLASS_COLORS["Crack"]
            cv2.addWeighted(colored_mask, 0.4, frame, 1.0, 0, frame)
            
            # Since tracking with 2 models is complex, we just sum per-frame counts for visual (not unique)
            # but we can fake tracking by just incrementing by the max seen in a frame.
            pass
        else:
            model = _get_bbox_model()
            results = model.track(frame_rgb, persist=True, conf=CONF_THRESHOLD, imgsz=640, tracker="bytetrack.yaml", verbose=False)
            res = results[0]
            if res.boxes is not None and res.boxes.id is not None:
                for box, cls, conf, tid in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy(), res.boxes.conf.cpu().numpy(), res.boxes.id.cpu().numpy()):
                    cls_int = int(cls)
                    tid_int = int(tid)
                    cname = BBOX_CLASS_NAMES.get(cls_int, f"Class {cls_int}")
                    if cname == "Pothole": seen_potholes.add(tid_int)
                    elif cname == "Crack": seen_cracks.add(tid_int)
                    x1,y1,x2,y2 = map(int, box)
                    _draw_box_with_label(frame, x1, y1, x2, y2, f"{cname} #{tid_int} {conf*100:.0f}%", CLASS_COLORS.get(cname, (200,200,200)))
        
        # Draw counts overlay
        p_count = len(seen_potholes) if model_type == "bbox" else 0
        c_count = len(seen_cracks) if model_type == "bbox" else 0
        _draw_counter_overlay(frame, p_count, c_count)
        writer.write(frame)

    cap.release()
    writer.release()
    elapsed = time.time() - t0
    
    h264_ok = _reencode_to_h264(raw_path, final_path)
    serve_path = final_path if h264_ok else raw_path
    
    summary_str = f"frames_processed={frame_count},video_duration_seconds={round(frame_count/fps, 2)}"
    return FileResponse(serve_path, media_type="video/mp4", filename="annotated.mp4", headers={"X-Detection-Summary": summary_str, "Access-Control-Expose-Headers": "X-Detection-Summary"})
