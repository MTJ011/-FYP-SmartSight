# ===================== navigation_controller.py =====================
# State machine controlling sensors + spoken navigation
# WINDOWS-SAFE pyttsx3 FIX (engine recreated per utterance)

import time
import requests
import pyttsx3
from instructor import generate_instructions

STEP_API = "http://localhost:8002/steps"
GYRO_API = "http://localhost:8000/gyro"

TURN_TARGET = 90
TURN_TOL = 10
STEP_PAUSE = 0.6

# ───────────────────────── TTS (SAFE) ─────────────────────────

def speak(text):
    print(f"[TTS] {text}")
    engine = pyttsx3.init()      # 🔴 RE-INIT EVERY TIME (CRITICAL)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# ───────────────────────── HELPERS ─────────────────────────

def get_steps():
    try:
        return requests.get(STEP_API, timeout=0.5).json()["steps"]
    except:
        return None

def get_angle():
    try:
        return requests.get(GYRO_API, timeout=0.5).json()["angle"]
    except:
        return None

# ───────────────────────── MAIN LOGIC ─────────────────────────

instructions = generate_instructions()
print("[INFO] Instructions:", instructions)

for instr, val in instructions:

    # ───────── MOVE ─────────
    if instr == "MOVE":
        speak(f"Move {val} step{'s' if val > 1 else ''} forward")

        start_steps = None
        while start_steps is None:
            start_steps = get_steps()
            time.sleep(0.1)

        print(f"[DEBUG] MOVE start_steps = {start_steps}")

        prev_steps = start_steps
        last_progress = time.time()

        while True:
            cur_steps = get_steps()
            if cur_steps is None:
                time.sleep(0.1)
                continue

            delta = cur_steps - start_steps

            if cur_steps != prev_steps:
                print(f"[STEP DETECTED] total={cur_steps}, delta={delta}")
                prev_steps = cur_steps
                last_progress = time.time()

            print(f"[DEBUG] Waiting... delta={delta}/{val}")

            if delta >= val and time.time() - last_progress > STEP_PAUSE:
                break

            time.sleep(0.1)

        speak("Stop")
        print("[INFO] MOVE complete")

    # ───────── TURN ─────────
    elif instr == "TURN":
        speak(f"Turn {val.lower()}")

        start_angle = None
        while start_angle is None:
            start_angle = get_angle()
            time.sleep(0.1)

        print(f"[DEBUG] TURN start_angle = {start_angle:.1f}")

        while True:
            cur_angle = get_angle()
            if cur_angle is None:
                time.sleep(0.05)
                continue

            delta = abs(cur_angle - start_angle)
            print(f"[DEBUG] angle={cur_angle:.1f}, delta={delta:.1f}")

            if abs(delta - TURN_TARGET) <= TURN_TOL:
                break

            time.sleep(0.05)

        speak("Turn complete")
        print("[INFO] TURN complete")

    # ───────── END ─────────
    elif instr == "END":
        speak("You have reached your destination. Please stop.")
        print("[INFO] Navigation finished")
