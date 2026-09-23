from pathlib import Path


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
MIC_DEVICE = None


# ============================================================
# WHISPER
# ============================================================

# Fast CPU model.
WHISPER_MODEL = "base"

# CPU-friendly.
WHISPER_COMPUTE_TYPE = "int8"


# ============================================================
# RECORDING
# ============================================================

# Wake word window.
WAKE_SECONDS = 2.2

# Normal command maximum.
COMMAND_MAX_SECONDS = 8.0

# Hard safety limit.
MAX_SPEECH_SECONDS = 8.0


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
SILENCE_DURATION = 0.55


# Keep audio just before speech begins.
PRE_ROLL_SECONDS = 0.35


# ============================================================
# VOICE START DETECTION
# ============================================================

# Minimum continuous voice required before
# treating a sound as actual speech.
MIN_VOICE_SECONDS = 0.16


# ============================================================
# NOISE FILTER
# ============================================================

# Ignore extremely short noises.
MIN_AUDIO_SECONDS = 0.35

# Don't accept a single random word from
# an extremely short recording.
SHORT_COMMAND_SECONDS = 0.75


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
FOLLOWUP_SECONDS = 8.0


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