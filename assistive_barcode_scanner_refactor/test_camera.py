import cv2
from services.camera_service import open_camera, read_frame, release_camera

cap = open_camera(camera_index=0)

print("Camera test running. Press q in the camera window to quit.")

while True:
    frame = read_frame(cap)

    if frame is None:
        print("No frame received")
        break

    cv2.imshow("Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        print("Closing camera test")
        break

release_camera(cap)