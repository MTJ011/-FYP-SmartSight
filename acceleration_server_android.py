# ===================== acceleration_server_android_adaptive.py =====================
# Android Step Detection: Adaptive Threshold + Hard Lockout
# Run: python acceleration_server_android_adaptive.py
# Sensor Logger Android -> HTTP Push -> http://YOUR_PC_IP:8002/data

from flask import Flask, request, jsonify
from collections import deque
import math
import time
import statistics

app = Flask(__name__)

# ============================================================
# PARAMETERS (PRODUCTION SAFE)
# ============================================================

HP_ALPHA = 0.95
SMOOTH_ALPHA = 0.50

SAMPLE_RATE_EST = 25.0
WINDOW_SECONDS = 2.5

STEP_LOCKOUT = 0.30
MIN_PEAK_WIDTH = 0.10

BASE_THRESHOLD = 0.60
NOISE_THRESHOLD = 0.90

VAR_WALK = 0.20

MAX_SPIKE = 18.0

# ============================================================
# INTERNAL STATE
# ============================================================

gravity = [0.0, 0.0, 0.0]

step_count = 0
last_step_time = 0.0

prev_smoothed = 0.0

in_peak = False
peak_start_time = None

# rolling buffer for variance detection
buf = deque(maxlen=int(WINDOW_SECONDS * SAMPLE_RATE_EST))

# 🔧 ANDROID WARM-UP FIX
ignore_first_step = True

# ============================================================
# STEP DETECTION CORE
# ============================================================

def process_sample(ts, ax, ay, az):
    global gravity, step_count, last_step_time
    global prev_smoothed, in_peak, peak_start_time
    global ignore_first_step

    # ---- HARD LOCKOUT ----
    locked = (last_step_time != 0.0) and ((ts - last_step_time) < STEP_LOCKOUT)

    # ---- Gravity removal ----
    gravity[0] = HP_ALPHA * gravity[0] + (1 - HP_ALPHA) * ax
    gravity[1] = HP_ALPHA * gravity[1] + (1 - HP_ALPHA) * ay
    gravity[2] = HP_ALPHA * gravity[2] + (1 - HP_ALPHA) * az

    lin_x = ax - gravity[0]
    lin_y = ay - gravity[1]
    lin_z = az - gravity[2]

    mag = math.sqrt(lin_x*lin_x + lin_y*lin_y + lin_z*lin_z)
    if mag > MAX_SPIKE:
        return False

    # ---- Heavy smoothing ----
    smoothed = SMOOTH_ALPHA * mag + (1 - SMOOTH_ALPHA) * prev_smoothed
    prev_smoothed = smoothed

    buf.append(smoothed)

    # ---- MOTION CLASSIFICATION ----
    if len(buf) > 10:
        var = statistics.pvariance(buf)
    else:
        var = 0.0

    walking = var > VAR_WALK
    threshold = BASE_THRESHOLD if walking else NOISE_THRESHOLD

    # ---- PEAK DETECTION ----
    if smoothed > threshold:
        if not in_peak:
            in_peak = True
            peak_start_time = ts
    else:
        if in_peak:
            peak_width = ts - peak_start_time
            if peak_width >= MIN_PEAK_WIDTH:
                if not locked:
                    if ignore_first_step:
                        ignore_first_step = False
                        print("ANDROID: Ignored initial false step (sensor warm-up)")
                    else:
                        step_count += 1
                        last_step_time = ts
                        print(f"ANDROID STEP {step_count}")

            in_peak = False
            peak_start_time = None

    return False

# ============================================================
# HTTP ENDPOINTS
# ============================================================

@app.route("/data", methods=["POST"])
def receive_data():
    try:
        data = request.get_json(force=True)

        packets = None
        if isinstance(data, dict) and "payload" in data:
            packets = data["payload"]
        elif isinstance(data, list):
            packets = data
        else:
            return jsonify({"status": "ok"}), 200

        for p in packets:
            name = (p.get("name") or p.get("sensor") or "").lower()
            if "accel" not in name:
                continue

            vals = p.get("values")
            if isinstance(vals, dict):
                ax = float(vals.get("x", 0))
                ay = float(vals.get("y", 0))
                az = float(vals.get("z", 0))
            elif isinstance(vals, (list, tuple)):
                ax, ay, az = map(float, vals[:3])
            else:
                continue

            t_raw = p.get("time")
            if t_raw is None:
                ts = time.time()
            elif t_raw > 1e6:
                ts = float(t_raw) / 1e9
            else:
                ts = float(t_raw)

            process_sample(ts, ax, ay, az)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"status": "error"}), 400

@app.route("/steps", methods=["GET"])
def get_steps():
    return jsonify({"steps": step_count})

# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    print("Android ADAPTIVE step server running at http://0.0.0.0:8002/data")
    app.run(host="0.0.0.0", port=8002)
