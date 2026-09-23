import os
from pathlib import Path


def _env_int(name, default, minimum=None):
    """Read a bounded integer setting without making startup fragile."""
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        return default

    return max(minimum, value) if minimum is not None else value


def _env_float(name, default, minimum=None):
    """Read a bounded float setting without exposing configuration errors."""
    try:
        value = float(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        return default

    return max(minimum, value) if minimum is not None else value


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
TEMP_DIR = DATA_DIR / "temp"
SCREENSHOT_DIR = DATA_DIR / "screenshots"

for folder in (
    DATA_DIR,
    LOG_DIR,
    TEMP_DIR,
    SCREENSHOT_DIR,
):
    folder.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# AUDIO
# ============================================================

SAMPLE_RATE = 16000
CHANNELS = 1

# None = Windows default microphone
MIC_DEVICE = 0


# ============================================================
# WHISPER
# ============================================================

# Fast CPU model. Set MJ_WHISPER_MODEL to override it.
WHISPER_MODEL = os.getenv("MJ_WHISPER_MODEL", "base").strip() or "base"

# CPU-friendly.
WHISPER_COMPUTE_TYPE = (
    os.getenv("MJ_WHISPER_COMPUTE_TYPE", "int8").strip()
    or "int8"
)

# Empty/"auto" lets Faster-Whisper detect Hindi or English. A fixed
# language can still be supplied with MJ_WHISPER_LANGUAGE when desired.
_whisper_language = os.getenv("MJ_WHISPER_LANGUAGE", "").strip().lower()
WHISPER_LANGUAGE = (
    None if _whisper_language in {"", "auto", "none"}
    else _whisper_language
)
WHISPER_BEAM_SIZE = _env_int("MJ_WHISPER_BEAM_SIZE", 1, minimum=1)


# ============================================================
# RECORDING
# ============================================================

# Wake word window.
WAKE_SECONDS = 1.8

# Normal command maximum.
COMMAND_MAX_SECONDS = 5.0

# Hard safety limit.
MAX_SPEECH_SECONDS = 5.0


# ============================================================
# VOICE DETECTION
# ============================================================

# Adaptive ambient multiplier.
#
# Higher = stronger noise rejection.
SILENCE_MULTIPLIER = 2.0


# Minimum meaningful RMS.
MIN_RMS = 0.0045


# Silence required to finish a command.
SILENCE_DURATION = 0.38


# Keep audio just before speech begins.
PRE_ROLL_SECONDS = 0.20


# ============================================================
# VOICE START DETECTION
# ============================================================

# Minimum continuous voice required before
# treating a sound as actual speech.
MIN_VOICE_SECONDS = 0.12


# ============================================================
# NOISE FILTER
# ============================================================

# Ignore extremely short noises.
MIN_AUDIO_SECONDS = 0.30

# Don't accept a single random word from
# an extremely short recording.
SHORT_COMMAND_SECONDS = 0.65


# ============================================================
# WAKE WORDS
# ============================================================

WAKE_WORDS = (
    "mj",
    "m j",
    "em jay",
    "mjay",
    "m jay",
)


# ============================================================
# LANGUAGE
# ============================================================

# We intentionally allow Whisper to detect
# Hindi / English / Hinglish.
#
# The listener will reject bad detections
# instead of blindly trusting the language label.

SUPPORTED_LANGUAGES = (
    "hi",
    "en",
)


# ============================================================
# TTS VOICES
# ============================================================

VOICE_HI = "hi-IN-SwaraNeural"
VOICE_EN = "en-US-AriaNeural"


# ============================================================
# TTS SPEED
# ============================================================

TTS_RATE_HI = "-5%"
TTS_RATE_EN = "-5%"

# Bound external TTS work so a network or player failure cannot stall the
# wake-word loop forever. Both values are overridable without source edits.
TTS_TIMEOUT_SECONDS = _env_float("MJ_TTS_TIMEOUT_SECONDS", 30.0, minimum=1.0)
TTS_PLAYBACK_TIMEOUT_SECONDS = _env_float(
    "MJ_TTS_PLAYBACK_TIMEOUT_SECONDS",
    120.0,
    minimum=1.0,
)


# ============================================================
# SCREEN / OCR
# ============================================================

# Tesseract remains configurable because its Windows installation location
# varies. The default preserves the project's existing installation path.
TESSERACT_CMD = os.getenv(
    "MJ_TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
).strip()


# ============================================================
# NETWORK
# ============================================================

# These are intentionally generic timeouts, never credentials. Web modules
# may import them when a bounded request is needed.
WEB_REQUEST_TIMEOUT_SECONDS = _env_float(
    "MJ_WEB_REQUEST_TIMEOUT_SECONDS",
    12.0,
    minimum=1.0,
)
WEB_MAX_RESPONSE_BYTES = _env_int(
    "MJ_WEB_MAX_RESPONSE_BYTES",
    2_000_000,
    minimum=64_000,
)


# Optional Gemini fallback configuration. The API key is intentionally read
# only by mj_gemini_brain.py from GEMINI_API_KEY and is never stored here.
GEMINI_MODEL = os.getenv("MJ_GEMINI_MODEL", "gemini-3.6-flash").strip()
GEMINI_CONTEXT_MESSAGES = _env_int(
    "MJ_GEMINI_CONTEXT_MESSAGES",
    8,
    minimum=2,
)


# ============================================================
# STARTUP
# ============================================================

STARTUP_GREETING = (
    "Hi Nitish. Main ready hoon."
)

WAKE_REPLY = (
    "Haan, bolo."
)


# ============================================================
# FOLLOW-UP LISTENING
# ============================================================

# After executing one command,
# MJ continues listening for this duration.
FOLLOWUP_SECONDS = 6.0


# ============================================================
# RECOGNITION QUALITY
# ============================================================

# Whisper hallucination protection.
NO_SPEECH_THRESHOLD = 0.50

COMPRESSION_RATIO_THRESHOLD = 2.4

LOG_PROB_THRESHOLD = -1.0


# ============================================================
# RESPONSE BEHAVIOR
# ============================================================

# Don't speak an error for every tiny
# microphone / recognition failure.
QUIET_RETRY = True

# Don't send empty/garbage recognition
# to the brain.
REJECT_BAD_TRANSCRIPT = True

