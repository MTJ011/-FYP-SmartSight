import time
import cv2
from services.guidance_service import find_barcode_region, get_guidance
from services.voice_service import speak
from services.beep_service import update_beep

last_guidance_time = 0
last_text = ""
GUIDANCE_INTERVAL = 2


def run(frame):
    global last_guidance_time, last_text

    region = find_barcode_region(frame)

    if not region:
        return "SEARCH", None

    guidance_text, clarity = get_guidance(frame, region)
    update_beep(clarity)

    # draw box
    x, y, w, h = region
    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    current_time = time.time()

    if guidance_text != last_text or current_time - last_guidance_time > GUIDANCE_INTERVAL:
        speak(guidance_text)
        last_text = guidance_text
        last_guidance_time = current_time

    # ✅ CONDITION TO SCAN (IMPORTANT)
    if clarity > 0.8:
        speak("Hold still, scanning")
        return "SCAN", None

    return "ALIGNMENT", None