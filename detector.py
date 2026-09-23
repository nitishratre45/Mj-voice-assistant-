import re
from difflib import SequenceMatcher

HINDI_LATIN_WORDS = {
    "hai", "haan", "ho", "karo", "kar", "khol", "kholo",
    "chalao", "chala", "mujhe", "mera", "meri", "tum",
    "aap", "abhi", "suno", "sun", "batao", "bata",
    "dikhao", "dikha", "badhao", "badao", "kam", "aur",
    "thoda", "zyada", "kya", "kaise", "kaisi", "kyun",
    "rahi", "raha", "do", "de", "lo", "le", "pe", "par",
    "ko", "se", "band", "nahi", "nahin"
}

# Whisper can turn a very short "MJ" into things such as:
# "m j", "em jay", "mjay", "md", "em", etc.
WAKE_ALIASES = {
    "mj", "m j", "em jay", "em-jay", "mjay",
    "md", "em", "jay", "m jay", "m.j"
}

def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-zA-Z0-9\u0900-\u097F\s.-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,!?;:-")

def detect_language(text: str) -> str:
    text = normalize_text(text)

    if re.search(r"[\u0900-\u097F]", text):
        return "hi"

    words = re.findall(r"[a-zA-Z]+", text)
    if any(word in HINDI_LATIN_WORDS for word in words):
        return "hi"

    return "en"

def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def contains_wake_word(text: str) -> bool:
    text = normalize_text(text)
    if not text:
        return False

    padded = f" {text} "

    # Exact/common forms first.
    for alias in WAKE_ALIASES:
        if f" {alias} " in padded:
            return True

    # Short Whisper mistakes: accept only very short utterances,
    # so normal speech is not accidentally treated as "MJ".
    words = text.split()
    if len(words) <= 3:
        compact = "".join(words)
        for target in ("mj", "mjay", "emjay"):
            if _similar(compact, target) >= 0.58:
                return True

        # "em" / "jay" often occur separately.
        if "em" in words and "jay" in words:
            return True

        # "md" is a common two-letter transcription of "MJ".
        if compact in {"md", "mj", "mjay"}:
            return True

    return False

def remove_wake_word(text: str) -> str:
    text = normalize_text(text)

    patterns = [
        r"\bem\s*jay\b",
        r"\bem-jay\b",
        r"\bmjay\b",
        r"\bm\s*j\b",
        r"\bmj\b",
        r"\bmd\b",
    ]

    for pattern in patterns:
        text = re.sub(pattern, " ", text)

    return normalize_text(text)
