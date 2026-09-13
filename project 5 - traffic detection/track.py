import cv2
from ultralytics import YOLO
from pathlib import Path

base_dir = Path(__file__).parent

# model n video path
MODEL_PATH = base_dir / "models" / "best.pt"
VIDEO_PATH = base_dir / "videos" / "traffic2.mp4"

# load model
model = YOLO(MODEL_PATH)

# open video
cap = cv2.VideoCapture(VIDEO_PATH)

while True:
    # baca 1 frame
    ret, frame = cap.read()

    # kl video hbis / gagal baca
    if not ret:
        break

    # yolo detect n bytreTrack
    results = model.track(
        source=frame,
        conf=0.5,
        tracker="bytetrack.yaml",
        persist=True
    )

    # buat frame yg udah di bbox n tracking
    annotated_frame = results[0].plot()

    # tampilin
    cv2.imshow("traffic trackers", annotated_frame)

    # press q utk berenti
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# kelar
cap.release()
cv2.destroyAllWindows()