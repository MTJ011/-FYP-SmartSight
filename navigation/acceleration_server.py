# server_refined.py
# Paste and run: python server_refined.py
# Expects Sensor Logger -> HTTP Push -> URL http://YOUR_PC_IP:8000/data
from flask import Flask, request, jsonify
from collections import deque
import math
import time
import statistics

app = Flask(__name__)

# =======================
# PARAMETERS (tweak below)
# =======================
HP_ALPHA = 0.9         # high-pass filter alpha for gravity removal (0.8-0.99)
SMOOTH_ALPHA = 0.25    # exponential smoothing for magnitude (0 = no smoothing, 1 = heavy)
WINDOW_SECONDS = 5.0   # rolling window to compute mean/std for adaptive threshold
MIN_STEP_INTERVAL = 0.35  # seconds (minimum allowed time between steps)
MAX_STEP_INTERVAL = 1.5   # seconds (optional max allowed, not strictly needed)
STD_MULT = 1.0         # threshold = mean + STD_MULT * std
ABS_MIN_MAG = 0.6      # absolute minimum magnitude (m/s^2) for candidate peaks
MAX_SPIKE = 30.0       # ignore impossible huge spikes (safety)
SAMPLE_RATE_EST = 50.0 # estimated sample rate (used only to size buffers)
# =======================

# internal state
gravity = [0.0, 0.0, 0.0]
last_step_time = 0.0
step_count = 0

# keep a buffer of tuples (t_seconds, mag_smoothed)
buf = deque(maxlen=int(WINDOW_SECONDS * SAMPLE_RATE_EST) + 10)

# helper to push a sample and do detection
def process_sample(ts_s, ax, ay, az):
    global gravity, last_step_time, step_count

    # 1) high-pass: estimate gravity and remove
    gravity[0] = HP_ALPHA * gravity[0] + (1 - HP_ALPHA) * ax
    gravity[1] = HP_ALPHA * gravity[1] + (1 - HP_ALPHA) * ay
    gravity[2] = HP_ALPHA * gravity[2] + (1 - HP_ALPHA) * az

    lin_x = ax - gravity[0]
    lin_y = ay - gravity[1]
    lin_z = az - gravity[2]

    # raw magnitude
    mag = math.sqrt(lin_x*lin_x + lin_y*lin_y + lin_z*lin_z)

    # guard
    if mag > MAX_SPIKE:
        return False  # ignore noisy spike

    # smoothing (exponential) on magnitude using last value in buffer
    if len(buf) == 0:
        smoothed = mag
    else:
        prev = buf[-1][1]
        smoothed = SMOOTH_ALPHA * mag + (1 - SMOOTH_ALPHA) * prev

    buf.append((ts_s, smoothed))

    # need at least 3 samples to do local-max check (we use middle sample)
    if len(buf) < 3:
        return False

    # local-max candidate: check the sample at index -2 (the middle of last 3)
    t_m, mid = buf[-2]
    left = buf[-3][1]
    right = buf[-1][1]

    # simple local maxima test
    if not (mid > left and mid > right):
        return False

    # check adaptive threshold using data in WINDOW_SECONDS
    # collect magnitudes from buffer (we already keep only WINDOW_SECONDS worth)
    mags = [m for (_, m) in buf]
    mean = statistics.mean(mags)
    std = statistics.pstdev(mags) if len(mags) > 1 else 0.0
    adaptive_threshold = max(ABS_MIN_MAG, mean + STD_MULT * std)

    # time since last step
    dt = t_m - last_step_time

    # final conditions for a valid step
    if mid >= adaptive_threshold and dt > MIN_STEP_INTERVAL:
        # optional: ignore too-long intervals (not necessary)
        # if dt < MAX_STEP_INTERVAL: ...
        last_step_time = t_m
        step_count += 1
        print(f"STEP {step_count}")
        return True

    return False

# route to receive batched payloads (Sensor Logger free sends 'payload' array)
@app.route("/data", methods=["POST"])
def receive_data():
    try:
        data = request.get_json(force=True)

        # older/newer Sensor Logger versions differ: try payload or top-level array
        packets = None
        if isinstance(data, dict) and "payload" in data:
            packets = data["payload"]
        elif isinstance(data, list):
            packets = data
        else:
            # unknown format -> ignore gracefully
            # you can print data for debugging uncomment below
            # print("Unexpected JSON format:", data)
            return jsonify({"status": "ok"}), 200

        # iterate packets; each packet may contain many sensor readings
        for p in packets:
            # Some builds use 'name' + 'values' dict or 'sensor' + 'values'
            name = p.get("name") or p.get("sensor") or ""
            name = name.lower().replace(" ", "")

            # we only process accelerometer (iPhone) or linearacceleration if present
            if name not in ("accelerometer", "linearacceleration", "linear_acceleration", "acceleration"):
                continue

            vals = p.get("values")
            # Sensor Logger sometimes nests differently
            if isinstance(vals, dict):
                ax = float(vals.get("x", 0.0))
                ay = float(vals.get("y", 0.0))
                az = float(vals.get("z", 0.0))
            elif isinstance(vals, list) or isinstance(vals, tuple):
                # order may be [x,y,z]
                ax = float(vals[0]); ay = float(vals[1]); az = float(vals[2])
            else:
                # unknown values format
                continue

            # p['time'] might be in ns (typical) or in seconds (rare). detect scale:
            t_raw = p.get("time", None)
            if t_raw is None:
                ts_s = time.time()
            else:
                # heuristics: if > 1e12 it's nanoseconds; if ~1e9 it's ns; >1e6 but small?
                if t_raw > 1e12:
                    ts_s = float(t_raw) / 1e9
                elif t_raw > 1e6:
                    ts_s = float(t_raw) / 1e9
                else:
                    # already seconds
                    ts_s = float(t_raw)

            process_sample(ts_s, ax, ay, az)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        # debug print
        print("Error in receive_data:", e)
        try:
            print("raw:", request.data.decode()[:2000])
        except:
            pass
        return jsonify({"status": "error", "error": str(e)}), 400

@app.route("/steps", methods=["GET"])
def get_steps():
    return jsonify({"steps": step_count})


if __name__ == "__main__":
    print("Refined step server running on http://0.0.0.0:8002/data")
    app.run(host="0.0.0.0", port=8002)
