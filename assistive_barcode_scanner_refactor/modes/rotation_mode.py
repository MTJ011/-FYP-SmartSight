import time

from services.barcode_service import detect_barcode
from services.scan_context import scan_context
from services.voice_service import speak

PROMPT_INTERVAL = 4.0

rotation_prompts = [
    "Rotate the product slowly.",
    "Turn the product around.",
    "Tilt the object upward.",
    "Tilt the object downward.",
    "Show another side of the product."
]

last_prompt_time = 0


def reset():
    global last_prompt_time
    last_prompt_time = 0
    scan_context.rotation_step = 0


def run(frame):
    global last_prompt_time

    now = time.time()

    codes = detect_barcode(frame)

    if codes:
        scan_context.detected_barcode = codes[0]
        speak("Barcode found. Hold still.")
        reset()
        return "ALIGNMENT", codes[0]

    if now - last_prompt_time > PROMPT_INTERVAL:
        prompt = rotation_prompts[
            scan_context.rotation_step % len(rotation_prompts)
        ]

        speak(prompt)

        scan_context.rotation_step += 1
        last_prompt_time = now

    return "ROTATION", None