import cv2
from ultralytics import YOLO
from pathlib import Path
import time

base_dir = Path(__file__).parent

# 2. Gabungkan path untuk model dan video
MODEL_PATH = base_dir / "models" / "best.pt"

VIDEO_PATH = base_dir / "videos" / "gate1.mp4"

OUTPUT_PATH = base_dir / "output/road_damage_tracked.mp4"


CLASS_NAMES = {
    0: "Pothole",
    1: "Crack",
}


# Load Model n video
# 3. Gunakan str() untuk memastikan YOLO dan OpenCV membaca path dengan benar

model = YOLO(str(MODEL_PATH))

cap = cv2.VideoCapture(str(VIDEO_PATH))
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

fps_video = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"video FPS: ", fps_video)
print("Resolution:", width, "x", height)


# video writer
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

fourcc = cv2.VideoWriter_fourcc(*"mp4v")

writer = cv2.VideoWriter(
    OUTPUT_PATH,
    fourcc,
    fps_video,
    (width, height)
)

# tracking
seen_track_ids = {
    0: set(),
    1: set()
}

frame_count = 0

start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # yolo + bytrack
    results = model.track(
        frame,
        persist=True,
        conf=0.3,
        tracker="bytetrack.yaml",
        verbose=False
    )
    result = results[0]

    # get detection
    if result.boxes.id is not None:
        boxes = result.boxes.xyxy.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        track_ids = result.boxes.id.cpu().numpy()

        for box, cls, conf, track_id in zip(boxes, classes,confidences, track_ids):
            cls = int(cls)
            track_id = int(track_id)

            x1, y1, x2, y2 = map(int, box)

            # simpan id yg pernah terlihat
            if cls in seen_track_ids:
                seen_track_ids[cls].add(track_id)

            class_name = CLASS_NAMES.get(
                cls,
                f"Class {cls}"
            )

            label = (
                f"{class_name}"
                f"ID:{track_id}"
                f"{conf:.2f}"
            )

            # bbox
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (255,0,0),
                2
            )

            # label
            cv2.putText(
                frame,
                label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2
            )

    # counter overlay
    pothole_count = len(seen_track_ids[0])
    crack_count = len(seen_track_ids[1])

    cv2.putText(
        frame,
        f"Pothole: {pothole_count}",
        (20,40),
        cv2.FONT_HERSHEY_COMPLEX,
        0.9,
        (255,0,0),
        2
    )

    cv2.putText(
        frame,
        f"Crack: {crack_count}",
        (20,80),
        cv2.FONT_HERSHEY_COMPLEX,
        0.9,
        (255,0,0),
        2
    )

    # save frame
    writer.write(frame)


# clean up
cap.release()
writer.release()

elapsed_time = time.time() - start_time

processing_fps = frame_count / elapsed_time


print("\n========== RESULT ==========")
print("Frames processed :", frame_count)
print("Processing time  :", round(elapsed_time, 2), "seconds")
print("Processing FPS   :", round(processing_fps, 2))

print(
    "Unique Potholes  :",
    len(seen_track_ids[0])
)

print(
    "Unique Cracks    :",
    len(seen_track_ids[1])
)

print(
    "Output video     :",
    OUTPUT_PATH
)