import cv2
import mediapipe as mp
import math
import threading
import queue
import subprocess
import speech_recognition as sr
from ultralytics import YOLO

# --------------------------------
# TEXT TO SPEECH - WINDOWS RELIABLE VERSION
# --------------------------------
speech_queue = queue.Queue()

def speech_worker():
    while True:
        text = speech_queue.get()

        if text is None:
            break

        print("SPEAK:", text)

        safe_text = str(text).replace("'", "''")

        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"Add-Type -AssemblyName System.Speech; "
                f"$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$speak.Rate = 0; "
                f"$speak.Speak('{safe_text}');"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        speech_queue.task_done()

threading.Thread(target=speech_worker, daemon=True).start()

def speak(text):
    speech_queue.put(str(text))

voice_command = None

def voice_listener():
    global voice_command

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("Calibrating microphone...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

    while True:
        try:
            with mic as source:
                print("Listening for voice command...")
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)

            command = recognizer.recognize_google(audio).lower()
            print("VOICE:", command)

            if "lock" in command:
                voice_command = "lock"
            elif "reset" in command or "unlock" in command:
                voice_command = "reset"

        except:
            pass

threading.Thread(target=voice_listener, daemon=True).start()

model = YOLO("yolov8n.pt")

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

THRESHOLD = 50

locked_target = None
target_locked = False

last_spoken_instruction = ""

# --------------------------------
# REACH / FORWARD GUIDANCE VARIABLES
# --------------------------------
reach_start_hand_area = None
reach_mode_started = False

while True:
    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hand_results = hands.process(rgb)

    fingertip = None
    hand_bbox = None
    hand_area = None

    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            xs = []
            ys = []

            for lm in hand_landmarks.landmark:
                xs.append(int(lm.x * w))
                ys.append(int(lm.y * h))

            hx1 = max(min(xs), 0)
            hy1 = max(min(ys), 0)
            hx2 = min(max(xs), w)
            hy2 = min(max(ys), h)

            hand_bbox = (hx1, hy1, hx2, hy2)
            hand_area = max((hx2 - hx1) * (hy2 - hy1), 1)

            cv2.rectangle(frame, (hx1, hy1), (hx2, hy2), (0, 255, 255), 2)

            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

            fx = int(index_tip.x * w)
            fy = int(index_tip.y * h)

            fingertip = (fx, fy)
            cv2.circle(frame, fingertip, 12, (0, 0, 255), -1)

    results = model(frame, verbose=False)
    boxes = results[0].boxes

    selected_object = None
    min_distance = float("inf")

    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

        cls = int(box.cls[0])
        label = model.names[cls]
        confidence = float(box.conf[0])

        if confidence < 0.5:
            continue

        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        obj_bbox = (x1, y1, x2, y2)
        obj_area = max((x2 - x1) * (y2 - y1), 1)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2,
        )

        if fingertip and not target_locked:
            distance = math.sqrt((fx - cx) ** 2 + (fy - cy) ** 2)

            if distance < min_distance:
                min_distance = distance
                selected_object = (label, (cx, cy), distance, obj_bbox, obj_area)

    if voice_command == "lock":
        if selected_object:
            locked_target = selected_object
            target_locked = True
            last_spoken_instruction = ""
            reach_start_hand_area = None
            reach_mode_started = False

            print(f"LOCKED TARGET: {locked_target[0]}")
            speak(f"Locked target {locked_target[0]}")
        else:
            print("NO TARGET TO LOCK")
            speak("No target found")

        voice_command = None

    if voice_command == "reset":
        target_locked = False
        locked_target = None
        last_spoken_instruction = ""
        reach_start_hand_area = None
        reach_mode_started = False

        print("TARGET RESET")
        speak("Target reset")

        voice_command = None

    active_target = locked_target if target_locked else selected_object

    guidance = ""

    if active_target and fingertip:
        label, center, distance, target_bbox, target_area = active_target

        tx, ty = center

        cv2.circle(frame, (tx, ty), 20, (0, 255, 0), 3)
        cv2.line(frame, fingertip, center, (0, 255, 0), 2)

        dx = tx - fx
        dy = ty - fy

        # --------------------------------
        # STAGE 1: ALIGN HORIZONTAL
        # --------------------------------
        if dx > THRESHOLD:
            guidance = "KEEP MOVING RIGHT"
            reach_start_hand_area = None
            reach_mode_started = False

        elif dx < -THRESHOLD:
            guidance = "KEEP MOVING LEFT"
            reach_start_hand_area = None
            reach_mode_started = False

        # --------------------------------
        # STAGE 2: ALIGN VERTICAL
        # --------------------------------
        elif dy > THRESHOLD:
            guidance = "STOP HORIZONTAL. KEEP MOVING DOWN"
            reach_start_hand_area = None
            reach_mode_started = False

        elif dy < -THRESHOLD:
            guidance = "STOP HORIZONTAL. KEEP MOVING UP"
            reach_start_hand_area = None
            reach_mode_started = False

        # --------------------------------
        # STAGE 3: FORWARD REACH GUIDANCE
        # Hand moves away from glasses camera, so hand bbox becomes smaller.
        # --------------------------------
        else:
            if target_locked and hand_area:
                if reach_start_hand_area is None:
                    reach_start_hand_area = hand_area
                    reach_mode_started = True
                    guidance = "HAND ALIGNED. MOVE HAND FORWARD"

                else:
                    hand_shrink_ratio = hand_area / reach_start_hand_area

                    tx1, ty1, tx2, ty2 = target_bbox
                    fingertip_inside_target = (
                        tx1 <= fx <= tx2 and
                        ty1 <= fy <= ty2
                    )

                    if hand_shrink_ratio > 0.75:
                        guidance = "KEEP MOVING FORWARD"

                    elif hand_shrink_ratio > 0.55:
                        guidance = "SLOWLY MOVE FORWARD"

                    else:
                        if fingertip_inside_target:
                            guidance = "STOP. PICK THE PRODUCT"
                        else:
                            guidance = "SLOWLY MOVE FORWARD"

                    cv2.putText(
                        frame,
                        f"HAND SHRINK: {hand_shrink_ratio:.2f}",
                        (20, 280),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2,
                    )

            else:
                guidance = "HAND ALIGNED"

        cv2.putText(
            frame,
            f"TARGET: {label}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            3,
        )

        cv2.putText(
            frame,
            guidance,
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3,
        )

        if target_locked:
            current_instruction = str(guidance)

            if current_instruction and current_instruction != last_spoken_instruction:
                speak(current_instruction)
                last_spoken_instruction = current_instruction

    status = "TARGET LOCKED" if target_locked else "SEARCH MODE"

    cv2.putText(frame, status, (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)

    cv2.putText(
        frame,
        "Say 'lock target' / 'reset target'",
        (20, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        "Keyboard: L = Lock | R = Reset",
        (20, 230),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.imshow("Hand Guidance System", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("l"):
        if selected_object:
            locked_target = selected_object
            target_locked = True
            last_spoken_instruction = ""
            reach_start_hand_area = None
            reach_mode_started = False

            print(f"LOCKED TARGET: {locked_target[0]}")
            speak(f"Locked target {locked_target[0]}")

    if key == ord("r"):
        target_locked = False
        locked_target = None
        last_spoken_instruction = ""
        reach_start_hand_area = None
        reach_mode_started = False

        print("TARGET RESET")
        speak("Target reset")

    if key == 27:
        break

speech_queue.put(None)
cap.release()
cv2.destroyAllWindows()