from ultralytics import YOLO
import cv2

# Load pretrained YOLO model
model = YOLO("yolov8n.pt")

# Open webcam
cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()

    if not success:
        break

    # Run detection
    results = model(frame)

    # Draw detections
    annotated_frame = results[0].plot()

    # Show frame
    cv2.imshow("YOLO Detection", annotated_frame)

    key = cv2.waitKey(1)

    if key == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()