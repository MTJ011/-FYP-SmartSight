import cv2
import mediapipe as mp

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

mp_draw = mp.solutions.drawing_utils

# Open webcam
cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()

    if not success:
        break

    # Flip frame for natural interaction
    frame = cv2.flip(frame, 1)

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process hand landmarks
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            # Draw landmarks
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Get index fingertip
            index_tip = hand_landmarks.landmark[
                mp_hands.HandLandmark.INDEX_FINGER_TIP
            ]

            h, w, c = frame.shape

            cx = int(index_tip.x * w)
            cy = int(index_tip.y * h)

            # Draw fingertip
            cv2.circle(frame, (cx, cy), 12, (0, 0, 255), -1)

            # Show coordinates
            cv2.putText(
                frame,
                f"Finger: ({cx}, {cy})",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

    cv2.imshow("Hand Tracking Test", frame)

    key = cv2.waitKey(1)

    if key == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()