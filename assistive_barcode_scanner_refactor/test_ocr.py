import cv2
import msvcrt

from services.camera_service import open_camera, read_frame, release_camera
from services.ocr_service import capture_product_ocr
from services.voice_service import speak

cap = open_camera(camera_index=0)

print("Camera started.")
print("Press c in PowerShell to capture OCR.")
print("Press q in PowerShell to quit.")

while True:
    frame = read_frame(cap)

    if frame is None:
        print("No frame received")
        break

    cv2.imshow("OCR Test", frame)

    key = cv2.waitKey(1) & 0xFF

    if msvcrt.kbhit():
        pressed = msvcrt.getch().decode("utf-8", errors="ignore").lower()
        if pressed:
            key = ord(pressed)

    if key == ord("c"):
        print("Capturing OCR now...")
        text = capture_product_ocr(frame)

        if text:
            print("OCR:", text)
            speak(text)
        else:
            print("No readable text found")
            speak("No readable text found")

    elif key == ord("q"):
        print("Closing")
        break

release_camera(cap)