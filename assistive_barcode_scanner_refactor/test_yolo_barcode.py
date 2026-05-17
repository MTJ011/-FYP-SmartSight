import cv2
import msvcrt
from ultralytics import YOLO

from services.camera_service import open_camera, read_frame, release_camera

model = YOLO("services/models/barcode_model.pt")

cap = open_camera(
    camera_index=0,
    width=1280,
    height=720
)

print("YOLO crop test running.")
print("Show barcode.")
print("Press s to save barcode crop.")
print("Press q to quit.")

last_crop = None

while True:
    frame = read_frame(cap)

    if frame is None:
        print("No frame")
        break

    results = model(frame, verbose=False)

    for r in results:
        if r.boxes is None:
            continue

        boxes = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()

        for i, box in enumerate(boxes):
            conf = float(confs[i])

            if conf < 0.20:
                continue

            x1, y1, x2, y2 = map(int, box)

            padding = 60
            h, w = frame.shape[:2]

            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)

            last_crop = frame[y1:y2, x1:x2].copy()

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"barcode {conf:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

    cv2.imshow("YOLO Crop Test", frame)

    if last_crop is not None:
        cv2.imshow("Latest Barcode Crop", last_crop)

    key = cv2.waitKey(1) & 0xFF

    if msvcrt.kbhit():
        pressed = msvcrt.getch().decode("utf-8", errors="ignore").lower()
        if pressed:
            key = ord(pressed)

    if key == ord("s"):
        if last_crop is not None:
            cv2.imwrite("barcode_crop_debug.jpg", last_crop)
            print("Saved barcode_crop_debug.jpg")
        else:
            print("No crop available yet")

    elif key == ord("q"):
        break

release_camera(cap)