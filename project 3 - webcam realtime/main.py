from ultralytics import YOLO
import cv2
import time

model = YOLO("yolo11n.pt")

# buka webcam
# Angka 0 biasanya berarti kamera default/pertama.
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Tidak dapat membuka webcam")
    exit() 


prev_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    results = model.predict(
        source=frame,
        conf=0.25,
        imgsz=640,
        verbose=False
    )
    annotated_frame = results[0].plot()
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time
    cv2.putText(
        annotated_frame, # Frame yang mau kita kasih tulisan.
        f"FPS: {fps:.1f}", # teks yg mo ditulis
        (20, 40), # posisi teks di frame (x, y)
        cv2.FONT_HERSHEY_COMPLEX, # font yg dipake
        1, # ukuran font
        (0, 255, 0), # warna font (BGR)
        2 # ketebalan font
    )
    cv2.imshow("YOLO Webcam", annotated_frame)

    # menunggu input keyboard selama 1 milidetik.
    # Kalau tombol yang ditekan adalah: q
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
# tutup semua window OpenCV yang kita buat dengan imshow()
cv2.destroyAllWindows()