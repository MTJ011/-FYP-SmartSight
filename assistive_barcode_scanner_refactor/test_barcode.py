import cv2
import msvcrt
import time

from services.camera_service import open_camera, read_frame, release_camera
from services.barcode_service import detect_barcode
from services.voice_service import speak

cap = open_camera(
    camera_index=0,
    width=640,
    height=480
)

print("Barcode decoder test running.")
print("Show barcode clearly.")
print("Press q to quit.")

last_code = None
last_seen_time = 0
CLEAR_AFTER_SECONDS = 1.5

while True:
    frame = read_frame(cap)

    if frame is None:
        print("No frame")
        break

    codes = detect_barcode(frame)
    now = time.time()

    if codes:
        code = codes[0]
        last_seen_time = now

        if code != last_code:
            last_code = code
            print("BARCODE DETECTED:", code)
            speak(f"Barcode detected {code}")

    else:
        if now - last_seen_time > CLEAR_AFTER_SECONDS:
            last_code = None

    cv2.imshow("Barcode Decoder Test", frame)

    key = cv2.waitKey(1) & 0xFF

    if msvcrt.kbhit():
        pressed = msvcrt.getch().decode("utf-8", errors="ignore").lower()
        if pressed:
            key = ord(pressed)

    if key == ord("q"):
        break

release_camera(cap)