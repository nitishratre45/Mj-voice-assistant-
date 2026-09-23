import subprocess
import time
from pathlib import Path

import pygame

from config import (
    TEMP_DIR,
    VOICE_HI,
    VOICE_EN,
    TTS_RATE_HI,
    TTS_RATE_EN,
    TTS_TIMEOUT_SECONDS,
    TTS_PLAYBACK_TIMEOUT_SECONDS,
)

class Speaker:
    def __init__(self):
        self.mixer_ready = False

        try:
            pygame.mixer.init()
            self.mixer_ready = True
        except Exception as exc:
            print("MJ VOICE WARNING: audio output unavailable; continuing without TTS.", exc)

    def speak(self, text: str, language: str = "hi"):
        text = (text or "").strip()
        if not text:
            return

        if not self.mixer_ready:
            print("MJ VOICE WARNING: skipping speech output because the audio mixer is unavailable.")
            return

        voice = VOICE_HI if language == "hi" else VOICE_EN
        rate = TTS_RATE_HI if language == "hi" else TTS_RATE_EN

        filename = TEMP_DIR / f"mj_voice_{time.time_ns()}.mp3"

        print("MJ:", text)

        try:
            result = subprocess.run(
                [
                    "edge-tts",
                    "--voice", voice,
                    f"--rate={rate}",
                    "--text", text,
                    "--write-media", str(filename),
                ],
                capture_output=True,
                text=True,
                timeout=TTS_TIMEOUT_SECONDS,
            )

            if result.returncode != 0:
                print("MJ TTS ERROR:")
                print(result.stderr)
                return

            pygame.mixer.music.stop()

            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

            pygame.mixer.music.load(str(filename))
            pygame.mixer.music.play()

            deadline = time.monotonic() + TTS_PLAYBACK_TIMEOUT_SECONDS
            while pygame.mixer.music.get_busy():
                if time.monotonic() >= deadline:
                    print("MJ TTS PLAYBACK TIMEOUT")
                    break
                time.sleep(0.03)

        except subprocess.TimeoutExpired:
            print("MJ TTS ERROR: edge-tts timed out.")
        except Exception as exc:
            print("MJ VOICE ERROR:", exc)

        finally:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass

            try:
                filename.unlink(missing_ok=True)
            except Exception:
                pass

    def close(self):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass
