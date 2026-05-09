import cv2


def open_camera():

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise Exception("Cannot access camera")

    return cap