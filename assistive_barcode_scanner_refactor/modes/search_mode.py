import time

from services.barcode_service import detect_barcode
from services.ocr_service import capture_product_ocr
from services.scan_context import scan_context
from services.voice_service import speak

OCR_CAPTURE_DELAY = 2.0
ROTATION_TIMEOUT = 8.0
PROMPT_INTERVAL = 4.0

start_time = None
last_prompt_time = 0


def reset():
    global start_time, last_prompt_time
    start_time = None
    last_prompt_time = 0


def run(frame):
    global start_time, last_prompt_time

    now = time.time()

    if start_time is None:
        start_time = now
        speak("Hold the product in front of the camera.")
        return "SEARCH", None

    # Capture OCR once near the beginning
    if not scan_context.ocr_captured and now - start_time > OCR_CAPTURE_DELAY:
        print("Capturing initial OCR fallback...")
        text = capture_product_ocr(frame)

        scan_context.ocr_captured = True
        scan_context.ocr_text = text

        if text:
            print("Saved OCR fallback:", text)
        else:
            print("No OCR fallback saved.")

    # Try barcode
    codes = detect_barcode(frame)

    if codes:
        scan_context.detected_barcode = codes[0]
        speak("Barcode found. Hold still.")
        reset()
        return "ALIGNMENT", codes[0]

    # Prompt user while searching
    if now - last_prompt_time > PROMPT_INTERVAL:
        speak("Move camera slowly around the product.")
        last_prompt_time = now

    # If no barcode after timeout, rotate product
    if now - start_time > ROTATION_TIMEOUT:
        reset()
        return "ROTATION", None

    return "SEARCH", None