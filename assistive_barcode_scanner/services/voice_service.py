import pyttsx3
import threading
import time

_lock = threading.Lock()

# ── TTS DONE EVENT ────────────────────────────────────────────────────────────
# Shared event: cleared while TTS is speaking, set when fully done.
# voice_command_service waits on this before listening.
_tts_done = threading.Event()
_tts_done.set()   # initially "done" (not speaking)

# Extra silence after TTS finishes before mic re-opens (seconds).
# Prevents picking up the tail echo of the speaker.
_POST_SPEECH_SILENCE = 0.6


def is_speaking() -> bool:
    return not _tts_done.is_set()


def wait_until_done():
    """Block until TTS is fully finished + silence buffer."""
    _tts_done.wait()


def speak(text):
    print(f"🔊 {text}")

    def _speak():
        with _lock:
            try:
                _tts_done.clear()           # signal: mic should mute now
                engine = pyttsx3.init()
                engine.setProperty("rate", 160)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                time.sleep(_POST_SPEECH_SILENCE)   # wait for echo to fade
            except Exception as e:
                print(f"TTS Error: {e}")
            finally:
                _tts_done.set()             # signal: mic can listen again

    threading.Thread(target=_speak, daemon=True).start()