from pathlib import Path
import py_compile

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "autonomous_v25.py"
TARGET = BASE / "autonomous_v25_1.py"

code = SOURCE.read_text(encoding="utf-8")

# ---------------------------------------------------------
# FIX 1: query ke starting punctuation ko remove karo
# ---------------------------------------------------------

old = '''query = " ".join(
                before.split()
            )'''

new = '''query = " ".join(
                before.split()
            ).strip(" ,.!?:;-_")

            # Remove accidental command punctuation
            query = " ".join(
                query.split()
            ).strip(" ,.!?:;-_")'''

if old in code:
    code = code.replace(old, new)
else:
    print("V25.1: query block not found")

# ---------------------------------------------------------
# FIX 2: YouTube search URL ko result candidate mat banao
# ---------------------------------------------------------

old2 = '''blocked = {
                "youtube",
                "google",
                "search",
                "home",
                "shorts",
                "history",
                "subscriptions",
                "settings",
                "menu"
            }'''

new2 = '''blocked = {
                "youtube",
                "google",
                "search",
                "home",
                "shorts",
                "history",
                "subscriptions",
                "settings",
                "menu"
            }

            # Never click browser/navigation URLs
            if (
                "youtube.com/results" in normalized
                or "google.com/search" in normalized
                or normalized.startswith("http://")
                or normalized.startswith("https://")
            ):
                continue

            # Ignore obvious navigation/address-bar text
            if (
                "search_query=" in normalized
                or "youtube.com" in normalized
                and len(normalized) > 20
            ):
                continue'''

if old2 in code:
    code = code.replace(old2, new2)
else:
    print("V25.1: blocked block not found")

# ---------------------------------------------------------
# FIX 3: YouTube result ko title-like text prefer karo
# ---------------------------------------------------------

old3 = '''if len(normalized) >= 12:
                score += 8'''

new3 = '''if len(normalized) >= 12:
                score += 8

            # Prefer actual content titles over tiny OCR fragments
            if len(normalized) >= 20:
                score += 12

            # Hashtag alone is weaker than a real title
            if normalized.startswith("#"):
                score -= 15

            # Browser/UI words should not win
            ui_words = [
                "youtube",
                "google",
                "search",
                "results",
                "home",
                "shorts"
            ]

            if any(
                w in normalized
                for w in ui_words
            ):
                score -= 10'''

if old3 in code:
    code = code.replace(old3, new3)
else:
    print("V25.1: scoring block not found")

# ---------------------------------------------------------
# INSTALL
# ---------------------------------------------------------

TARGET.write_text(
    code,
    encoding="utf-8"
)

print(
    "MJ V25.1: installed"
)

print(
    "MJ V25.1: size =",
    TARGET.stat().st_size,
    "bytes"
)

py_compile.compile(
    str(TARGET),
    doraise=True
)

print(
    "MJ V25.1: syntax OK"
)