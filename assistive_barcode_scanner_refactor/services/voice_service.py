import pyttsx3
import threading
import time

_lock = threading.Lock()

_tts_done = threading.Event()
_tts_done.set()

_POST_SPEECH_SILENCE = 0.4


def is_speaking():
    return not _tts_done.is_set()


def wait_until_done():
    _tts_done.wait()


def speak(text, block=False):

    if not text:
        return

    print(f"🔊 {text}")

    def _run():

        with _lock:

            try:
                _tts_done.clear()

                engine = pyttsx3.init()
                engine.setProperty("rate", 165)

                engine.say(text)
                engine.runAndWait()
                engine.stop()

                time.sleep(_POST_SPEECH_SILENCE)

            except Exception as e:
                print(f"TTS error: {e}")

            finally:
                _tts_done.set()

    if block:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()