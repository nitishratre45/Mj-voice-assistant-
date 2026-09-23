from collections import deque
import re
import time
from difflib import SequenceMatcher

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import (
    SAMPLE_RATE,
    CHANNELS,
    MIC_DEVICE,
    WHISPER_MODEL,
    WHISPER_COMPUTE_TYPE,
    SILENCE_MULTIPLIER,
    MIN_RMS,
    SILENCE_DURATION,
    PRE_ROLL_SECONDS,
    MAX_SPEECH_SECONDS,
    WAKE_SECONDS,
    COMMAND_MAX_SECONDS,
)


class VoiceListener:
    """
    MJ PRO VOICE ENGINE

    Pipeline:

        Microphone
            ↓
        Adaptive noise gate
            ↓
        Voice activity detection
            ↓
        Pre-roll
            ↓
        Speech capture
            ↓
        Whisper
            ↓
        Text normalization
            ↓
        Hallucination filter
            ↓
        Garbage filter
            ↓
        MJ Brain

    Compatible with existing mj.py.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self):

        print("MJ: Loading speech engine...")

        self.model = WhisperModel(
            WHISPER_MODEL,
            device="cpu",
            compute_type=WHISPER_COMPUTE_TYPE,
        )

        print("MJ: Speech engine ready.")

        self.device = MIC_DEVICE

        # Pro voice runtime state.
        self._last_command = ""
        self._last_command_time = 0.0
        self._last_ambient = 0.0
        self._last_threshold = MIN_RMS
        self._speech_confirmed = False

        if self.device is None:
            default_device = sd.default.device

            if isinstance(
                default_device,
                (list, tuple),
            ):
                self.device = default_device[0]
            else:
                self.device = default_device

        info = sd.query_devices(
            self.device,
            "input",
        )

        print(
            f"MJ: Microphone: "
            f"{info.get('name', 'Unknown')}"
        )

        print(
            f"MJ: Device index: "
            f"{self.device}"
        )

        print(
            f"MJ: Input channels="
            f"{info.get('max_input_channels', '?')}, "
            f"default rate="
            f"{info.get('default_samplerate', '?')}"
        )

    # =========================================================
    # AUDIO HELPERS
    # =========================================================

    @staticmethod
    def _rms(audio):

        if audio is None:
            return 0.0

        if len(audio) == 0:
            return 0.0

        audio = np.asarray(
            audio,
            dtype=np.float32,
        )

        audio = (
            audio
            - np.mean(audio)
        )

        return float(
            np.sqrt(
                np.mean(
                    audio * audio
                )
            )
        )

    @staticmethod
    def _peak(audio):

        if audio is None:
            return 0.0

        if len(audio) == 0:
            return 0.0

        return float(
            np.max(
                np.abs(
                    np.asarray(
                        audio,
                        dtype=np.float32,
                    )
                )
            )
        )

    @staticmethod
    def _clean_audio(audio):

        audio = np.asarray(
            audio,
            dtype=np.float32,
        )

        if len(audio) == 0:
            return audio

        # Remove DC offset.
        audio = (
            audio
            - np.mean(audio)
        )

        # Gentle speech normalization for low-level mic input.
        # Loud audio is left essentially unchanged.
        rms = float(np.sqrt(np.mean(audio * audio)))
        if rms > 0 and rms < 0.012:
            gain = min(4.0, 0.035 / rms)
            audio = audio * gain

        # Prevent clipping.
        peak = float(
            np.max(
                np.abs(audio)
            )
        )

        if peak > 0.98:

            audio = (
                audio / peak
            ) * 0.95

        return audio.astype(
            np.float32
        )

    # =========================================================
    # PRO AUDIO / COMMAND HELPERS
    # =========================================================

    @staticmethod
    def _similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

    @classmethod
    def _repair_whisper_command(cls, text):
        """
        Conservative repair of common short voice commands.
        Never invents arbitrary targets.
        """
        text = cls._normalize_text(text)
        if not text:
            return ""

        replacements = {
            "scrol down": "scroll down",
            "scroll dow": "scroll down",
            "scroll don": "scroll down",
            "scroll doun": "scroll down",
            "scrol up": "scroll up",
            "scroll u": "scroll up",
            "neeche scrol": "neeche scroll",
            "niche scroll": "neeche scroll",
            "upar scrol": "upar scroll",
            "escap": "esc",
            "escape": "esc",
            "control a": "ctrl a",
            "control c": "ctrl c",
            "control v": "ctrl v",
            "you tube": "youtube",
            "utube": "youtube",
            "goggle": "google",
            "googel": "google",
            "note pad": "notepad",
        }

        for bad, good in replacements.items():
            text = re.sub(
                rf"\b{re.escape(bad)}\b",
                good,
                text,
            )

        # Common Hinglish forms.
        phrases = (
            (r"\bscroll\s+neeche\b", "scroll down"),
            (r"\bscroll\s+upar\b", "scroll up"),
            (r"\bneeche\s+scroll\s+karo\b", "scroll down"),
            (r"\bupar\s+scroll\s+karo\b", "scroll up"),
            (r"\bneeche\s+scroll\b", "scroll down"),
            (r"\bupar\s+scroll\b", "scroll up"),
        )

        for pattern, replacement in phrases:
            text = re.sub(
                pattern,
                replacement,
                text,
            )

        # High-confidence short-command fuzzy repair.
        known = (
            "scroll down",
            "scroll up",
            "esc",
            "escape",
            "click",
            "right click",
            "double click",
            "screenshot",
            "enter",
            "back",
            "home",
            "stop",
            "pause",
            "resume",
        )

        words = text.split()
        if 1 <= len(words) <= 4:
            candidate = " ".join(words)
            best = max(
                known,
                key=lambda x: cls._similar(candidate, x),
            )
            score = cls._similar(candidate, best)
            if score >= 0.90:
                text = best

        return text

    @staticmethod
    def _speech_gain(audio):
        """
        Gentle normalization for quiet speech.
        Does not boost already loud audio.
        """
        audio = np.asarray(audio, dtype=np.float32)
        if len(audio) == 0:
            return audio

        rms = float(np.sqrt(np.mean(audio * audio)))
        if rms <= 0:
            return audio

        # Only lift genuinely quiet recordings.
        if rms < 0.012:
            gain = min(4.0, 0.035 / rms)
            audio = audio * gain

        peak = float(np.max(np.abs(audio)))
        if peak > 0.95:
            audio = audio * (0.95 / peak)

        return audio.astype(np.float32)

    def _is_duplicate_command(self, text):
        now = time.monotonic()
        normalized = self._normalize_text(text)

        if not normalized:
            return True

        if (
            normalized == self._normalize_text(self._last_command)
            and now - self._last_command_time < 2.0
        ):
            return True

        self._last_command = normalized
        self._last_command_time = now
        return False

    # =========================================================
    # TEXT NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_text(text):

        text = (
            text or ""
        )

        text = text.lower().strip()

        # Remove punctuation but preserve
        # English + Hindi characters.
        text = re.sub(
            r"[^a-zA-Z0-9\u0900-\u097F\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # =========================================================
    # WAKE WORD
    # =========================================================

    @classmethod
    def _is_wake_piece(
        cls,
        word,
    ):

        word = cls._normalize_text(
            word
        )

        return word in {
            "mj",
            "m j",
            "mjay",
            "m jay",
            "em jay",
            "em",
            "jay",
        }

    @classmethod
    def _wake_only_text(
        cls,
        text,
    ):

        text = cls._normalize_text(
            text
        )

        if not text:
            return False

        words = text.split()

        if not words:
            return False

        if len(words) > 12:
            return False

        matches = sum(
            1
            for word in words
            if cls._is_wake_piece(
                word
            )
        )

        return (
            matches
            /
            max(
                1,
                len(words),
            )
            >= 0.65
        )

    @classmethod
    def _clean_wake_text(
        cls,
        text,
    ):

        text = cls._normalize_text(
            text
        )

        if cls._wake_only_text(
            text
        ):
            return "mj"

        return text

    # =========================================================
    # REPETITION CLEANER
    # =========================================================

    @classmethod
    def _remove_repeated_text(
        cls,
        text,
    ):

        text = cls._normalize_text(
            text
        )

        if not text:
            return ""

        if cls._wake_only_text(
            text
        ):
            return "mj"

        words = text.split()

        if len(words) <= 2:
            return text

        # Example:
        # youtube kholo youtube kholo
        for size in range(
            min(8, len(words) // 2),
            0,
            -1,
        ):

            if len(words) < size * 2:
                continue

            first = words[
                :size
            ]

            second = words[
                size:size * 2
            ]

            if first == second:

                result = first[:]

                position = size * 2

                while (
                    position + size
                    <= len(words)
                ):

                    block = words[
                        position:
                        position + size
                    ]

                    if block != first:
                        break

                    position += size

                result.extend(
                    words[position:]
                )

                return " ".join(
                    result
                )

        # Adjacent duplicate words.
        result = []

        previous = None

        for word in words:

            if word == previous:
                continue

            result.append(
                word
            )

            previous = word

        return " ".join(
            result
        ).strip()

    # =========================================================
    # HALLUCINATION FILTER
    # =========================================================

    @classmethod
    def _is_hallucination(
        cls,
        text,
    ):

        text = cls._normalize_text(
            text
        )

        if not text:
            return True

        words = text.split()

        bad_phrases = (
            "thank you for watching",
            "thanks for watching",
            "please subscribe",
            "like and subscribe",
            "amara org",
            "subtitles by",
        )

        for phrase in bad_phrases:

            if phrase in text:
                return True

        if len(words) >= 8:

            unique = len(
                set(words)
            )

            if unique <= 2:
                return True

        return False

    # =========================================================
    # SUSPICIOUS RECOGNITION
    # =========================================================

    @classmethod
    def _is_suspicious(
        cls,
        text,
        duration,
        rms,
        purpose,
    ):

        text = cls._normalize_text(
            text
        )

        if not text:
            return True

        if purpose == "wake":
            return False

        words = text.split()

        # Very weak audio.
        if (
            rms < 0.0028
            and duration < 0.9
        ):
            return True

        # One random word from extremely
        # short audio is usually noise.
        if (
            len(words) == 1
            and duration < 0.70
        ):

            valid_single_words = {
                "click",
                "enter",
                "esc",
                "escape",
                "stop",
                "pause",
                "resume",
                "back",
                "home",
                "up",
                "down",
                "left",
                "right",
                "youtube",
                "google",
            }

            if text not in valid_single_words:
                return True

        return False

    # =========================================================
    # FIXED RECORDING
    # =========================================================

    def _record_fixed(
        self,
        seconds,
    ):

        frames = max(
            1,
            int(
                seconds
                * SAMPLE_RATE
            ),
        )

        audio = sd.rec(
            frames,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            device=self.device,
        )

        sd.wait()

        return self._clean_audio(
            audio.reshape(-1)
        )

    # =========================================================
    # AMBIENT NOISE
    # =========================================================

    def _ambient_noise(
        self,
        seconds=0.30,
    ):

        audio = self._record_fixed(
            seconds
        )

        return self._rms(
            audio
        )

    # =========================================================
    # WAKE LISTENER
    # =========================================================

    def listen_for_wake(self):

        # Wake recording is deliberately
        # short for faster response.
        audio = self._record_fixed(
            max(
                1.8,
                min(
                    WAKE_SECONDS,
                    2.5,
                ),
            )
        )

        return self.transcribe(
            audio,
            purpose="wake",
        )

    # =========================================================
    # COMMAND LISTENER
    # =========================================================

    def listen_until_silence(self):

        # Wait briefly after TTS.
        time.sleep(
            0.25
        )

        block_seconds = 0.06

        block_size = max(
            1,
            int(
                SAMPLE_RATE
                * block_seconds
            ),
        )

        pre_roll_blocks = max(
            1,
            int(
                PRE_ROLL_SECONDS
                / block_seconds
            ),
        )

        # -----------------------------------------------------
        # CALIBRATE MICROPHONE
        # -----------------------------------------------------

        samples = []

        for _ in range(3):

            sample = (
                self._record_fixed(
                    0.12
                )
            )

            samples.append(
                self._rms(
                    sample
                )
            )

        ambient = float(
            np.median(
                samples
            )
        )

        # Adaptive threshold.
        # Use a conservative floor plus ambient-relative threshold.
        # This avoids triggering on keyboard/fan noise while still
        # allowing your low-volume microphone speech through.
        threshold = max(
            MIN_RMS * 0.85,
            ambient * max(
                2.0,
                SILENCE_MULTIPLIER,
            ),
        )

        threshold = min(
            max(threshold, 0.0035),
            0.035,
        )

        self._last_ambient = ambient
        self._last_threshold = threshold

        print(
            f"MJ: Listening... "
            f"ambient={ambient:.4f}, "
            f"threshold={threshold:.4f}"
        )

        frames = []

        pre_roll = deque(
            maxlen=pre_roll_blocks
        )

        started = False

        speech_start = None
        silence_start = None

        wait_start = (
            time.monotonic()
        )

        # User gets enough time to start speaking.
        wait_limit = 7.0

        # Require speech to remain above
        # threshold for a short period.
        voice_start_time = None

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            device=self.device,
            blocksize=block_size,
        ) as stream:

            while True:

                data, overflowed = (
                    stream.read(
                        block_size
                    )
                )

                if overflowed:
                    print(
                        "MJ: Audio buffer "
                        "overflow recovered."
                    )

                chunk = (
                    data.reshape(-1)
                    .astype(
                        np.float32
                    )
                )

                level = self._rms(
                    chunk
                )

                now = (
                    time.monotonic()
                )

                pre_roll.append(
                    chunk.copy()
                )

                # =================================================
                # WAIT FOR REAL VOICE
                # =================================================

                if not started:

                    if level >= threshold:

                        if (
                            voice_start_time
                            is None
                        ):

                            voice_start_time = now

                        elif (
                            now
                            - voice_start_time
                            >= 0.10
                        ):

                            started = True

                            speech_start = now

                            frames.extend(
                                list(
                                    pre_roll
                                )
                            )

                            print(
                                f"MJ: Voice detected "
                                f"({level:.4f})"
                            )

                    else:

                        voice_start_time = None

                    if (
                        now
                        - wait_start
                        >= wait_limit
                    ):

                        return ""

                # =================================================
                # RECORD REAL SPEECH
                # =================================================

                else:

                    frames.append(
                        chunk
                    )

                    if level >= threshold:

                        silence_start = None

                    else:

                        if (
                            silence_start
                            is None
                        ):

                            silence_start = now

                        elif (
                            now
                            - silence_start
                            >= max(
                                0.62,
                                SILENCE_DURATION,
                            )
                        ):

                            break

                    # Hard command limit.
                    if (
                        speech_start
                        is not None
                        and
                        now
                        - speech_start
                        >= min(
                            COMMAND_MAX_SECONDS,
                            MAX_SPEECH_SECONDS,
                        )
                    ):

                        break

        if not frames:
            return ""

        audio = np.concatenate(
            frames
        )

        audio = self._clean_audio(
            audio
        )

        duration = (
            len(audio)
            / SAMPLE_RATE
        )

        if duration < 0.35:

            print(
                "MJ: Speech too short."
            )

            return ""

        print(
            f"MJ: Captured "
            f"{duration:.2f}s"
        )

        return self.transcribe(
            audio,
            purpose="command",
        )

    # =========================================================
    # TRANSCRIPTION
    # =========================================================

    def transcribe(
        self,
        audio,
        purpose="command",
    ):

        if (
            audio is None
            or
            len(audio) == 0
        ):
            return ""

        audio = self._clean_audio(
            audio
        )

        audio = self._speech_gain(
            audio
        )

        peak = self._peak(
            audio
        )

        rms = self._rms(
            audio
        )

        duration = (
            len(audio)
            / SAMPLE_RATE
        )

        print(
            f"MJ: Audio peak={peak:.4f}, "
            f"RMS={rms:.4f}"
        )

        # =====================================================
        # AUDIO QUALITY GATE
        # =====================================================

        if (
            peak < MIN_RMS
            or
            rms < 0.0022
        ):

            print(
                "MJ: Audio too quiet."
            )

            return ""

        # =====================================================
        # WHISPER OPTIONS
        # =====================================================

        common_options = {
            "beam_size": 5,
            "best_of": 5,
            "temperature": [0.0, 0.2, 0.4],
            "patience": 1.5,
            "vad_filter": True,
            "vad_parameters": {
                "min_silence_duration_ms": 350,
                "speech_pad_ms": 180,
            },
            "condition_on_previous_text": False,
            "no_speech_threshold": 0.50,
            "compression_ratio_threshold": 2.4,
            "log_prob_threshold": -1.0,
        }

        # =====================================================
        # WAKE MODE
        # =====================================================

        if purpose == "wake":

            segments, info = (
                self.model.transcribe(
                    audio,
                    language="en",
                    initial_prompt=(
                        "MJ. "
                        "M J. "
                        "M jay. "
                        "Em jay."
                    ),
                    **common_options,
                )
            )

        # =====================================================
        # COMMAND MODE
        # =====================================================

        else:

            segments, info = (
                self.model.transcribe(
                    audio,

                    # Let Whisper detect language.
                    # We do NOT blindly trust the detected
                    # language for command acceptance.
                    language=None,

                    initial_prompt=(
                        "Computer voice assistant command. "
                        "Hindi, Hinglish and English. "
                        "Google kholo. "
                        "YouTube kholo. "
                        "Calculator kholo. "
                        "Notepad kholo. "
                        "File par click karo. "
                        "File ko double click karo. "
                        "File par right click karo. "
                        "Upar scroll karo. "
                        "Neeche scroll karo. "
                        "Esc dabao. "
                        "Ctrl A. "
                        "Search box par click karo."
                    ),

                    **common_options,
                )
            )

        # =====================================================
        # COLLECT TEXT
        # =====================================================

        parts = []

        for segment in segments:

            piece = (
                segment.text
                or ""
            ).strip()

            if not piece:
                continue

            parts.append(
                " ".join(
                    piece.split()
                )
            )

        text = " ".join(
            parts
        )

        text = self._normalize_text(
            text
        )

        if purpose == "command":
            text = self._repair_whisper_command(text)

        if not text:

            print(
                "MJ: Speech not understood."
            )

            return ""

        # =====================================================
        # LANGUAGE LOG
        # =====================================================

        language = getattr(
            info,
            "language",
            None,
        )

        probability = getattr(
            info,
            "language_probability",
            None,
        )

        if language:

            if probability is not None:

                print(
                    f"MJ: Language="
                    f"{language} "
                    f"({probability:.2f})"
                )

            else:

                print(
                    f"MJ: Language="
                    f"{language}"
                )

        # =====================================================
        # WAKE CLEANUP
        # =====================================================

        if purpose == "wake":

            text = self._clean_wake_text(
                text
            )

            if (
                text == "mj"
                or
                self._wake_only_text(
                    text
                )
            ):

                print(
                    "MJ HEARD: mj"
                )

                return "mj"

            # Never send random wake-mode
            # text to the brain.
            return ""

        # =====================================================
        # CLEAN REPETITION
        # =====================================================

        text = (
            self._remove_repeated_text(
                text
            )
        )

        if not text:
            return ""

        # =====================================================
        # HALLUCINATION FILTER
        # =====================================================

        if self._is_hallucination(
            text
        ):

            print(
                "MJ: Ignored probable "
                "Whisper hallucination."
            )

            return ""

        # =====================================================
        # SUSPICIOUS TEXT FILTER
        # =====================================================

        if self._is_suspicious(
            text,
            duration,
            rms,
            purpose,
        ):

            print(
                f"MJ: Ignored suspicious "
                f"recognition: '{text}'"
            )

            return ""

        # =====================================================
        # FINAL CLEAN TEXT
        # =====================================================

        if self._is_duplicate_command(text):
            print(
                f"MJ: Ignored duplicate command: '{text}'"
            )
            return ""

        print(
            "MJ HEARD:",
            text
        )

        return text


# ============================================================
# MJ AUTONOMOUS COMPUTER AGENT V1
# ============================================================

class AgentGoal:
    """Small state object for a goal-driven computer-use loop."""

    def __init__(self, goal, max_steps=12):
        self.goal = str(goal or "").strip()
        self.max_steps = max(1, int(max_steps))
        self.step = 0
        self.history = []
        self.completed = False
        self.last_screen_signature = None

    def add(self, action, result=None):
        self.history.append({
            "step": self.step,
            "action": action,
            "result": result,
        })


def _mj_agent_normalize_goal(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def _mj_agent_screen_text(controller):
    """
    Read visible OCR text when the existing controller exposes it.
    Falls back to a screenshot-only observation.
    """
    observation = {
        "text": "",
        "screenshot": None,
    }

    try:
        if hasattr(controller, "read_visible_text"):
            value = controller.read_visible_text()
            if isinstance(value, str):
                observation["text"] = value
            elif value is not None:
                observation["text"] = str(value)
    except Exception:
        pass

    try:
        if hasattr(controller, "capture"):
            observation["screenshot"] = controller.capture(save=False)
        elif hasattr(controller, "screenshot"):
            observation["screenshot"] = controller.screenshot()
    except Exception:
        pass

    return observation


def _mj_agent_find_visible(controller, target):
    target = _mj_agent_normalize_goal(target)
    if not target:
        return None

    try:
        if hasattr(controller, "search_visible_text"):
            return controller.search_visible_text(target)
    except Exception:
        pass

    return None


def _mj_agent_execute_screen_action(agent, action):
    """
    Execute only actions already supported by the project's
    ScreenController/ScreenAgent APIs.
    """
    action_type = action.get("action")
    target = action.get("target", "")
    value = action.get("value", "")

    try:
        if action_type == "scroll_down":
            if hasattr(agent, "process"):
                return agent.process("scroll down")

        if action_type == "scroll_up":
            if hasattr(agent, "process"):
                return agent.process("scroll up")

        if action_type == "click" and target:
            if hasattr(agent, "process"):
                return agent.process(f"{target} par click karo")

        if action_type == "double_click" and target:
            if hasattr(agent, "process"):
                return agent.process(f"{target} ko double click karo")

        if action_type == "right_click" and target:
            if hasattr(agent, "process"):
                return agent.process(f"{target} par right click karo")

        if action_type == "click_and_type" and target and value:
            if hasattr(agent, "process"):
                return agent.process(
                    f"{target} par click karo aur {value} type karo"
                )

        if action_type == "press" and value:
            if hasattr(agent, "process"):
                return agent.process(f"{value} dabao")

    except Exception as exc:
        return (f"Agent action error: {exc}", "hi", False)

    return (f"Unsupported agent action: {action_type}", "hi", False)


def autonomous_screen_agent(controller, goal, planner=None,
                            max_steps=12, observe_delay=0.35,
                            on_step=None):
    """
    Goal-driven computer-use loop.

    The agent:
        1. observes the current screen,
        2. records state/history,
        3. chooses a conservative next action,
        4. executes it,
        5. repeats until the goal is reached or max_steps is hit.

    This V1 deliberately does NOT invent arbitrary clicks.
    A higher-level planner/LLM can supply richer actions later.
    """
    goal = _mj_agent_normalize_goal(goal)
    state = AgentGoal(goal, max_steps=max_steps)

    if not goal:
        return {
            "success": False,
            "goal": "",
            "steps": [],
            "reason": "empty_goal",
        }

    for _ in range(state.max_steps):
        state.step += 1

        obs = _mj_agent_screen_text(controller)
        visible_text = _mj_agent_normalize_goal(obs.get("text", ""))

        step_info = {
            "step": state.step,
            "goal": state.goal,
            "visible_text": visible_text[:4000],
        }

        # ----------------------------------------------------
        # Goal completion checks
        # ----------------------------------------------------
        goal_words = [
            w.lower()
            for w in re.findall(r"[a-zA-Z0-9]+", state.goal)
            if len(w) > 2
        ]

        visible_lower = visible_text.lower()

        if goal_words and all(word in visible_lower for word in goal_words):
            state.completed = True
            step_info["decision"] = "goal_visible"
            state.history.append(step_info)
            if on_step:
                on_step(step_info)
            break

        # ----------------------------------------------------
        # Conservative V1 decisions
        # ----------------------------------------------------
        goal_lower = state.goal.lower()
        action = None

        # Search intent: focus an obvious search box if visible.
        if any(k in goal_lower for k in (
            "search", "find", "dhoond", "dhund", "ढूंढ"
        )):
            for candidate in (
                "search box",
                "search",
                "google search",
                "address bar",
            ):
                result = _mj_agent_find_visible(controller, candidate)
                if result and result.get("found"):
                    action = {
                        "action": "click",
                        "target": candidate,
                    }
                    break

        # If the goal explicitly asks to scroll, choose direction.
        if action is None:
            if any(k in goal_lower for k in (
                "scroll down", "neeche", "नीचे"
            )):
                action = {"action": "scroll_down"}

            elif any(k in goal_lower for k in (
                "scroll up", "upar", "ऊपर"
            )):
                action = {"action": "scroll_up"}

        # If nothing safe is inferable, stop instead of guessing.
        if action is None:
            step_info["decision"] = "needs_higher_level_planner"
            state.history.append(step_info)
            if on_step:
                on_step(step_info)
            break

        step_info["decision"] = action
        state.history.append(step_info)

        if on_step:
            on_step(step_info)

        result = _mj_agent_execute_screen_action(
            controller,
            action,
        )

        state.history[-1]["result"] = result

        # Give the UI a moment to settle before re-observing.
        time.sleep(max(0.0, float(observe_delay)))

        if isinstance(result, tuple) and len(result) >= 3:
            if result[2] is False:
                break

    return {
        "success": state.completed,
        "goal": state.goal,
        "steps": state.history,
        "completed": state.completed,
        "reason": (
            "goal_completed"
            if state.completed
            else "agent_stopped"
        ),
    }

