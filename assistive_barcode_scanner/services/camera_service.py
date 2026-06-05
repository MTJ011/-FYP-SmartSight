import cv2
import time


def open_camera(camera_index=0, width=640, height=480, fps=30):
    backends = [
        cv2.CAP_DSHOW,
        cv2.CAP_ANY
    ]

    for backend in backends:
        cap = cv2.VideoCapture(camera_index, backend)

        if not cap.isOpened():
            cap.release()
            continue

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        for _ in range(5):
            ret, frame = cap.read()
            time.sleep(0.03)

            if ret and frame is not None:
                print(f"✅ Camera opened at index {camera_index}")
                return cap

        cap.release()

    raise RuntimeError(f"Cannot access camera at index {camera_index}")