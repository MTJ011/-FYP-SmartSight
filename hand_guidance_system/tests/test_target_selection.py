import cv2
import mediapipe as mp
import math
from ultralytics import YOLO

# -------------------------------
# LOAD YOLO MODEL
# -------------------------------
model = YOLO("yolov8n.pt")

# -------------------------------
# MEDIAPIPE HANDS
# -------------------------------
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

mp_draw = mp.solutions.drawing_utils

# -------------------------------
# CAMERA
# -------------------------------
cap = cv2.VideoCapture(0)

while True:

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    # -------------------------------
    # HAND TRACKING
    # -------------------------------
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    hand_results = hands.process(rgb)

    fingertip = None

    if hand_results.multi_hand_landmarks:

        for hand_landmarks in hand_results.multi_hand_landmarks:

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            index_tip = hand_landmarks.landmark[
                mp_hands.HandLandmark.INDEX_FINGER_TIP
            ]

            fx = int(index_tip.x * w)
            fy = int(index_tip.y * h)

            fingertip = (fx, fy)

            cv2.circle(frame, fingertip, 12, (0, 0, 255), -1)

    # -------------------------------
    # OBJECT DETECTION
    # -------------------------------
    results = model(frame)

    boxes = results[0].boxes

    selected_object = None
    min_distance = float("inf")

    for box in boxes:

        x1, y1, x2, y2 = box.xyxy[0]

        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

        cls = int(box.cls[0])

        label = model.names[cls]

        confidence = float(box.conf[0])

        # Object center
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        # Draw bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

        cv2.putText(
            frame,
            f"{label} {confidence:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2
        )

        cv2.circle(frame, (cx, cy), 5, (255, 255, 0), -1)

        # -------------------------------
        # TARGET SELECTION
        # -------------------------------
        if fingertip:

            distance = math.sqrt(
                (fx - cx) ** 2 +
                (fy - cy) ** 2
            )

            if distance < min_distance:
                min_distance = distance
                selected_object = (
                    label,
                    (cx, cy),
                    distance
                )

    # -------------------------------
    # HIGHLIGHT SELECTED OBJECT
    # -------------------------------
    if selected_object:

        label, center, distance = selected_object

        cx, cy = center

        cv2.circle(frame, (cx, cy), 20, (0, 255, 0), 3)

        cv2.line(frame, fingertip, center, (0, 255, 0), 2)

        cv2.putText(
            frame,
            f"TARGET: {label}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            3
        )

    cv2.imshow("Target Selection System", frame)

    key = cv2.waitKey(1)

    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()