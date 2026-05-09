from ultralytics import YOLO
import cv2

# load model
model = YOLO("services/models/barcode_model.pt")

# load test image
img = cv2.imread("test.jpeg")

if img is None:
    print("❌ Image not found. Put test.jpg in project root.")
    exit()

# run detection
results = model(img, conf=0.25)

# print boxes
print("Detections:", results[0].boxes)

# show output
annotated = results[0].plot()
cv2.imshow("YOLO Test", annotated)
cv2.waitKey(0)
cv2.destroyAllWindows()