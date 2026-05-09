import threading
import time
import subprocess

_current_interval = 999.0
_active = False


def _make_beep():
    try:
        # Raspberry Pi — uses aplay
        subprocess.Popen(
            ["python3", "-c",
             "import os; os.system('aplay /usr/share/sounds/alsa/Front_Left.wav 2>/dev/null')"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def update_beep(clarity_score):
    global _current_interval
    if clarity_score < 0.1:
        _current_interval = 999.0   # silent
    else:
        # 0.1 → 2.0s interval, 1.0 → 0.15s interval
        _current_interval = max(0.15, 2.0 - (clarity_score * 1.85))


def start_beep_loop():
    global _active
    _active = True

    def _loop():
        while _active:
            interval = _current_interval
            if interval < 900:
                _make_beep()
            time.sleep(interval)

    threading.Thread(target=_loop, daemon=True).start()


def stop_beep():
    global _active
    _active = False