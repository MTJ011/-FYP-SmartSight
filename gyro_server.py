from flask import Flask, request, jsonify
import time
import threading
import tkinter as tk
from math import degrees

# ============================================================
#                 GLOBAL ANGLE STATE
# ============================================================

current_gyro_y = 0.0      # latest gyro y (rad/s)
angle_deg = 0.0           # accumulated angle
last_time = time.time()   # for integration timing

TURN_THRESHOLD = 0.8
DEADZONE = 0.15

# ============================================================
#                FLASK SERVER (YOUR ORIGINAL)
# ============================================================

app = Flask(__name__)

@app.route("/data", methods=["POST"])
def debug_gyro():
    global current_gyro_y

    data = request.json

    if not data or "payload" not in data:
        return jsonify({"error": "invalid"}), 400

    payload = data["payload"]
    gyro_entries = [e for e in payload if e.get("name") == "gyroscope"]

    if not gyro_entries:
        return jsonify({"status": "no gyro"}), 200

    xs, ys, zs = [], [], []
    for entry in gyro_entries:
        v = entry.get("values", {})
        xs.append(float(v.get("x", 0)))
        ys.append(float(v.get("y", 0)))
        zs.append(float(v.get("z", 0)))

    avg_x = sum(xs) / len(xs)
    avg_y = sum(ys) / len(ys)
    avg_z = sum(zs) / len(zs)

    # Update global gyro Y for GUI integration
    current_gyro_y = avg_y

    turn = "NONE"
    if abs(avg_y) > TURN_THRESHOLD:
        if avg_y > 0:
            turn = "LEFT TURN"
        else:
            turn = "RIGHT TURN"

    print(f"[{time.strftime('%H:%M:%S')}] "
          f"x={avg_x:.3f}, y={avg_y:.3f}, z={avg_z:.3f} | {turn}")

    return jsonify({"status": "ok"})


# ============================================================
#                   TKINTER GUI THREAD
# ============================================================

def gui_thread():
    global angle_deg, last_time, current_gyro_y

    root = tk.Tk()
    root.title("Rotation Angle Tracker")
    root.geometry("400x300")

    title = tk.Label(root, text="Phone Rotation Angle", font=("Arial", 18))
    title.pack(pady=10)

    angle_label = tk.Label(root, text="0°", font=("Arial", 48))
    angle_label.pack(pady=20)

    def reset_angle():
        nonlocal angle_label
        global angle_deg
        angle_deg = 0.0
        angle_label.config(text="0.0°")

    reset_button = tk.Button(root, text="Reset", font=("Arial", 14), command=reset_angle)
    reset_button.pack(pady=10)

    # update loop
    def update_angle():
        nonlocal angle_label
        global angle_deg, last_time, current_gyro_y

        now = time.time()
        dt = now - last_time
        last_time = now

        # integrate gyro to get angle
        angle_deg += degrees(current_gyro_y * dt)

        angle_label.config(text=f"{angle_deg:.1f}°")

        root.after(16, update_angle)  # ~60 FPS smooth

    update_angle()
    root.mainloop()

# ───────────────────────────────────────────────
# NEW ENDPOINT: return current angle + turn status
# ───────────────────────────────────────────────
@app.route("/gyro", methods=["GET"])
def get_gyro():
    global angle_deg, current_gyro_y

    # determine live turn state
    if abs(current_gyro_y) > TURN_THRESHOLD:
        turn = "LEFT" if current_gyro_y > 0 else "RIGHT"
    else:
        turn = "NONE"

    return jsonify({
        "angle": angle_deg,
        "turn": turn
    })

# ============================================================
#                  START SERVER + GUI
# ============================================================

if __name__ == "__main__":
    # Start GUI in a separate thread
    t = threading.Thread(target=gui_thread, daemon=True)
    t.start()

    print("GYRO SERVER + GUI running at http://0.0.0.0:8000/data")
    app.run(host="0.0.0.0", port=8000)
