# kalo mau run dan liat tracking nya di kode ini

import cv2
from ultralytics import YOLO

import cv2
from ultralytics import YOLO
from pathlib import Path

base_dir = Path(__file__).parent

# 2. Gabungkan path untuk model dan video
MODEL_PATH = base_dir / "models" / "best.pt"

VIDEO_PATH = base_dir / "videos" / "gate1.mp4"


# Load model hasil training kita
model = YOLO(MODEL_PATH)

# Buka video
cap = cv2.VideoCapture(VIDEO_PATH)

while True:

    # Baca satu frame
    ret, frame = cap.read()

    # Kalau video sudah habis / gagal dibaca
    if not ret:
        break

    # YOLO detection + ByteTrack
    results = model.track(
        source=frame,
        conf=0.3,
        tracker="bytetrack.yaml",
        persist=True
    )

    # Buat frame yang sudah diberi bounding box + tracking ID
    annotated_frame = results[0].plot()

    # Tampilkan
    cv2.imshow("Road Damage Tracking", annotated_frame)

    # Tekan Q untuk berhenti
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Selesai menggunakan video
cap.release()
cv2.destroyAllWindows()