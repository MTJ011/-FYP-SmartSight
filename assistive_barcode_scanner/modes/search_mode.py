import time
import cv2
from services.barcode_service import detect_barcode
from services.voice_service import speak
from services.guidance_service import find_barcode_region, get_guidance
from services.beep_service import update_beep
from services.voice_command_service import get_command

SEARCH_TIMEOUT = 7
start_time = time.time()
frame_count = 0
last_guidance_time = 0
last_no_product_time = 0
confirmation_buffer = {}
last_guidance_text = ""

SCAN_EVERY_N_FRAMES = 8
GUIDANCE_INTERVAL = 4
NO_PRODUCT_INTERVAL = 8
CONFIRM_THRESHOLD = 3


def run(frame):
    global frame_count, last_guidance_time, last_no_product_time
    global confirmation_buffer, last_guidance_text

    frame_count += 1
    current_time = time.time()

    # ── VOICE COMMANDS ────────────────────────────────────────────
    cmd = get_command()
    if cmd == "stop":
        speak("Scanner paused. Say scan to resume.")
        return "PAUSED", None
    elif cmd == "help":
        speak(
            "I am scanning for a barcode. "
            "Hold the product in front of your chest. "
            "I will tell you how to rotate it until I find the barcode. "
            "Listen for the beep — it gets faster as you get closer. "
            "Say repeat to hear the last result again."
        )
        return "SEARCH", None

    if frame_count % SCAN_EVERY_N_FRAMES != 0:
        return "SEARCH", None

    # ── TRY FULL DECODE ───────────────────────────────────────────
    # detect_barcode returns (list_of_barcodes, ocr_product_name)
    barcodes, ocr_product_name = detect_barcode(frame)

    if barcodes:
        candidate = barcodes[0]  # candidate is now correctly a string
        confirmation_buffer[candidate] = \
            confirmation_buffer.get(candidate, 0) + 1

        count = confirmation_buffer[candidate]
        print(f"👁️  Candidate: {candidate} ({count}/{CONFIRM_THRESHOLD})")
        update_beep(1.0)

        if count == 1:
            speak("Hold still")

        if count >= CONFIRM_THRESHOLD:
            confirmation_buffer.clear()
            speak("Got it!")
            return "SCAN", candidate

        return "SEARCH", None

    # ── OCR FALLBACK — announce product name if found ─────────────
    if ocr_product_name:
        speak(f"No barcode found. Product label reads: {ocr_product_name}")
        return "SEARCH", None

    # ── BARCODE NOT DECODED — FIND REGION FOR GUIDANCE ───────────
    confirmation_buffer.clear()
    region = find_barcode_region(frame)

    if region:
        guidance_text, clarity = get_guidance(frame, region)
        update_beep(clarity * 0.7)

        # Draw region on frame (helpful for sighted helper/developer)
        x, y, rw, rh = region
        cv2.rectangle(frame, (x, y), (x + rw, y + rh), (0, 165, 255), 2)
        cv2.putText(frame, "Barcode region", (x, y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)

        # Only speak if guidance changed or enough time passed
        if (guidance_text != last_guidance_text or
                current_time - last_guidance_time > GUIDANCE_INTERVAL):
            speak(guidance_text)
            last_guidance_text = guidance_text
            last_guidance_time = current_time

    else:
        update_beep(0.0)

        if current_time - start_time > SEARCH_TIMEOUT:
            return "ROTATION", None

        if current_time - last_no_product_time > NO_PRODUCT_INTERVAL:
            speak("Move camera slowly around the product")
            last_no_product_time = current_time

    return "SEARCH", None