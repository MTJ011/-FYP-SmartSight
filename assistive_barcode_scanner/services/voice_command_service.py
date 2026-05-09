import speech_recognition as sr
import threading

recognizer = sr.Recognizer()
_current_command = None
_lock = threading.Lock()

COMMANDS = {
    "scan":   ["scan", "start", "begin"],
    "repeat": ["repeat", "again", "what"],
    "stop":   ["stop", "pause", "quit"],
    "help":   ["help", "how", "instructions"],
    "yes":    ["yes", "yeah", "yep", "done", "okay", "ok", "haan", "han"],
    "no":     ["no", "not", "wait", "nahi", "nope"],
}


def get_command():
    global _current_command
    with _lock:
        cmd = _current_command
        _current_command = None
    return cmd


def _listen_loop():
    global _current_command

    # Import here to avoid circular import
    from services.voice_service import is_speaking, wait_until_done

    mic = sr.Microphone()

    with mic as source:
        print("🎤 Calibrating microphone...")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)

    print("🎤 Voice commands ready")

    while True:
        try:
            # ── BLOCK while TTS is active ──────────────────────────
            if is_speaking():
                wait_until_done()   # blocks until speech + silence buffer done
                continue

            with mic as source:
                audio = recognizer.listen(source, timeout=4, phrase_time_limit=3)

            # ── DISCARD if TTS fired while we were listening ───────
            if is_speaking():
                continue

            text = recognizer.recognize_google(audio).lower().strip()
            print(f"🎤 Heard: '{text}'")

            words = text.split()
            for cmd, triggers in COMMANDS.items():
                if any(t in words for t in triggers):
                    with _lock:
                        _current_command = cmd
                    print(f"✅ Command: {cmd}")
                    break

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(f"Voice error: {e}")


def start_listening():
    threading.Thread(target=_listen_loop, daemon=True).start()