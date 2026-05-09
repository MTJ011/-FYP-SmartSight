import cv2

# Replace with your DroidCam IP or Device Index (0 or 1)
cap = cv2.VideoCapture(0) 

while True:
    ret, frame = cap.read()
    if not ret: break

    cv2.imshow('SmartSight Demo', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()