import subprocess
import time
from pathlib import Path

import pygame

from config import TEMP_DIR, VOICE_HI, VOICE_EN

# Faster speech. More important: pass --rate as ONE safe argument.
TTS_RATE_HI = "-5%"
TTS_RATE_EN = "-5%"

class Speaker:
    def __init__(self):
        pygame.mixer.init()
        self.cache = {}

    def _make_audio(self, text, voice, rate, filename):
        # Use --rate=VALUE so a negative/positive percentage can never
        # accidentally be interpreted as a separate command-line switch.
        commands = [
            [
                "edge-tts",
                "--voice", voice,
                f"--rate={rate}",
                "--text", text,
                "--write-media", str(filename),
            ],
            [
                "edge-tts",
                "--voice", voice,
                "--text", text,
                "--write-media", str(filename),
            ],
        ]

        last_error = ""
        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
            except Exception as exc:
                last_error = str(exc)
                continue

            if result.returncode == 0 and filename.exists():
                return True

            last_error = result.stderr.strip()

        print("MJ TTS ERROR:", last_error)
        return False

    def speak(self, text: str, language: str = "hi"):
        text = (text or "").strip()
        if not text:
            return

        voice = VOICE_HI if language == "hi" else VOICE_EN
        rate = TTS_RATE_HI if language == "hi" else TTS_RATE_EN

        # Cache short repeated replies so MJ doesn't wait for Edge-TTS
        # every time it says the same thing.
        cache_key = (text, language)
        filename = self.cache.get(cache_key)

        if filename is None:
            filename = TEMP_DIR / f"mj_voice_{time.time_ns()}.mp3"
            print("MJ:", text)

            if not self._make_audio(text, voice, rate, filename):
                return

            # Keep only short, repeated assistant replies cached.
            if len(text) <= 40:
                self.cache[cache_key] = filename

        try:
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

            pygame.mixer.music.load(str(filename))
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.02)

        except Exception as exc:
            print("MJ PLAY ERROR:", exc)

    def close(self):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass

        # Remove cached temporary files on exit.
        for filename in self.cache.values():
            try:
                Path(filename).unlink(missing_ok=True)
            except Exception:
                pass

