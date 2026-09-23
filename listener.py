from collections import deque
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import (
    SAMPLE_RATE,
    CHANNELS,
    MIC_DEVICE,
    WHISPER_MODEL,
    WHISPER_COMPUTE_TYPE,
    WHISPER_LANGUAGE,
    WHISPER_BEAM_SIZE,
    SILENCE_MULTIPLIER,
    MIN_RMS,
    SILENCE_DURATION,
    PRE_ROLL_SECONDS,
    MAX_SPEECH_SECONDS,
    WAKE_SECONDS,
)

class VoiceListener:
    def __init__(self):
        print("MJ: Loading speech engine...")
        self.model = None
        try:
            self.model = WhisperModel(
                WHISPER_MODEL,
                device="cpu",
                compute_type=WHISPER_COMPUTE_TYPE,
            )
            print("MJ: Speech engine ready.")
        except Exception as exc:
            print("MJ SPEECH ENGINE WARNING:", exc)
            self.model = None

        self.device = self._resolve_input_device(MIC_DEVICE)
        try:
            info = sd.query_devices(self.device, "input")
            print(f"MJ: Microphone: {info['name']}")
            print(f"MJ: Device index: {self.device}")
        except Exception as exc:
            print("MJ: Microphone info unavailable; continuing with detected device fallback.", exc)

    @staticmethod
    def _resolve_input_device(configured_device):
        """Use the configured microphone, with a safe default-device retry."""
        candidates = [configured_device]

        try:
            default_input = sd.default.device[0]
        except Exception:
            default_input = None

        if default_input not in candidates:
            candidates.append(default_input)

        last_error = None
        for candidate in candidates:
            if candidate is None:
                continue
            try:
                sd.query_devices(candidate, "input")
                return candidate
            except Exception as exc:
                last_error = exc

        message = "No usable input microphone was found."
        if last_error is not None:
            message += f" Last device error: {last_error}"
        raise RuntimeError(message)

    def _record_fixed(self, seconds):
        try:
            audio = sd.rec(
                int(seconds * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                device=self.device,
            )
            sd.wait()
            return audio.reshape(-1)
        except Exception as exc:
            print("MJ MICROPHONE RECORD ERROR:", exc)
            return np.array([], dtype=np.float32)

    @staticmethod
    def _rms(chunk):
        if len(chunk) == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(chunk))))

    def _ambient_noise(self, seconds=0.35):
        audio = self._record_fixed(seconds)
        return self._rms(audio)

    def listen_for_wake(self):
        if self.model is None:
            print("MJ WAKE LISTEN WARNING: speech model unavailable; skipping wake detection.")
            return ""

        audio = self._record_fixed(WAKE_SECONDS)
        text = self.transcribe(audio, purpose="wake")
        return text

    def listen_until_silence(self, context_text=""):
        """
        Records short blocks instead of calling sd.rec() for a fixed
        multi-second command window. It stops shortly after speech ends.
        """
        if self.model is None:
            print("MJ LISTEN LOOP WARNING: speech model unavailable; skipping microphone capture.")
            return ""

        block_seconds = 0.10
        block_size = int(SAMPLE_RATE * block_seconds)
        pre_roll_blocks = max(1, int(PRE_ROLL_SECONDS / block_seconds))

        ambient = self._ambient_noise()
        threshold = max(MIN_RMS, ambient * SILENCE_MULTIPLIER)

        print(
            f"MJ: Listening... ambient={ambient:.4f}, "
            f"threshold={threshold:.4f}"
        )

        frames = []
        pre_roll = deque(maxlen=pre_roll_blocks)

        started = False
        speech_start = None
        silence_start = None

        start_time = time.monotonic()

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                device=self.device,
                blocksize=block_size,
            ) as stream:

                while True:
                    data, _ = stream.read(block_size)
                    chunk = data.reshape(-1).copy()
                    level = self._rms(chunk)
                    now = time.monotonic()

                    pre_roll.append(chunk)

                    if level >= threshold:
                        if not started:
                            started = True
                            speech_start = now
                            frames.extend(list(pre_roll))
                            print(f"MJ: Voice detected ({level:.4f})")
                        else:
                            frames.append(chunk)

                        silence_start = None

                    elif started:
                        frames.append(chunk)

                        if silence_start is None:
                            silence_start = now
                        elif now - silence_start >= SILENCE_DURATION:
                            break

                    if (
                        started
                        and speech_start is not None
                        and now - speech_start >= MAX_SPEECH_SECONDS
                    ):
                        break

                    if not started and now - start_time >= MAX_SPEECH_SECONDS:
                        break
        except Exception as exc:
            print("MJ MICROPHONE STREAM ERROR:", exc)
            return ""

        if not frames:
            return ""

        audio = np.concatenate(frames).astype(np.float32)
        return self.transcribe(audio, context_text=context_text)

    @staticmethod
    def _initial_prompt(purpose="command", context_text=""):
        """Keep wake aliases while using bounded contextual vocabulary."""
        base = "MJ, M J, em jay"

        try:
            from vocabulary_engine import get_whisper_prompt

            vocabulary = get_whisper_prompt(
                purpose=purpose,
                context_text=str(context_text or "")[:1000],
            )
            if vocabulary:
                return f"{base}. {vocabulary}"[:1800]
        except Exception as exc:
            print("MJ VOCABULARY PROMPT WARNING:", exc)

        return base

    def transcribe(self, audio, context_text="", purpose="command"):
        if self.model is None:
            print("MJ TRANSCRIPTION WARNING: speech model unavailable; returning empty result.")
            return ""

        if audio is None or len(audio) == 0:
            return ""

        if not np.isfinite(audio).all():
            print("MJ AUDIO ERROR: non-finite samples received.")
            return ""

        peak = float(np.max(np.abs(audio)))
        print(f"MJ: Audio peak={peak:.4f}")

        if peak < MIN_RMS:
            return ""

        try:
            segments, _ = self.model.transcribe(
                audio,
                language=WHISPER_LANGUAGE,
                beam_size=WHISPER_BEAM_SIZE,
                best_of=1,
                temperature=0,
                vad_filter=True,
                condition_on_previous_text=False,
                initial_prompt=self._initial_prompt(purpose, context_text),
            )
        except Exception as exc:
            print("MJ TRANSCRIPTION ERROR:", exc)
            return ""

        text = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

        if text:
            print("MJ HEARD:", text)

        return text.lower()
