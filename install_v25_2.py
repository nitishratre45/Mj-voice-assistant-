from pathlib import Path
import py_compile

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "autonomous_v25_1.py"
TARGET = BASE / "autonomous_v25_2.py"

code = SOURCE.read_text(encoding="utf-8")

# ---------------------------------------------------------
# V25.2 - YouTube result filtering
# ---------------------------------------------------------

marker = '''# Ignore obvious navigation/address-bar text'''

if marker in code:
    extra = r'''
            # V25.2: Never treat hashtags as actual video results
            if normalized.startswith("#"):
                continue

            if normalized.startswith("hashtag"):
                continue

            # Ignore common YouTube navigation/UI elements
            youtube_ui = {
                "youtube",
                "home",
                "shorts",
                "subscriptions",
                "history",
                "library",
                "search",
                "create",
                "settings",
                "show more",
                "show less"
            }

            if normalized in youtube_ui:
                continue
'''
    code = code.replace(marker, extra + "\n            " + marker)

else:
    print("V25.2 WARNING: filtering marker not found")

# ---------------------------------------------------------
# Prefer real video-like titles
# ---------------------------------------------------------

score_marker = '''# Hashtag alone is weaker than a real title'''

if score_marker in code:
    extra_score = r'''
            # V25.2: Strong preference for real video titles
            if page_type == "youtube":
                if len(normalized) >= 25:
                    score += 20

                if len(normalized) >= 40:
                    score += 10

                # Titles containing the requested query are highly relevant
                query_words = [
                    w.lower()
                    for w in query.split()
                    if len(w) > 2
                ]

                matched_words = sum(
                    1 for w in query_words
                    if w in normalized
                )

                score += matched_words * 15

                # Hashtags are not videos
                if normalized.startswith("#"):
                    score -= 100
'''
    code = code.replace(score_marker, extra_score + "\n            " + score_marker)

else:
    print("V25.2 WARNING: score marker not found")

# ---------------------------------------------------------
# Safety: don't click hashtag candidates
# ---------------------------------------------------------

click_marker = '''MJ V25: CLICK'''

# Add a helper function near the top if possible
helper = r'''
def _v25_2_is_valid_youtube_result(text):
    """
    Return True only for plausible YouTube video/title text.
    """
    if not text:
        return False

    value = str(text).strip().lower()

    if value.startswith("#"):
        return False

    blocked = (
        "youtube.com/results",
        "search_query=",
        "youtube.com",
        "www.youtube.com",
    )

    if any(x in value for x in blocked):
        return False

    return True


'''

# Insert helper before first class/function if possible
if "_v25_2_is_valid_youtube_result" not in code:
    lines = code.splitlines()
    insert_at = 0

    for i, line in enumerate(lines):
        if line.startswith("class ") or line.startswith("def "):
            insert_at = i
            break

    lines.insert(insert_at, helper.rstrip())
    code = "\n".join(lines) + "\n"

# ---------------------------------------------------------
# Write and compile
# ---------------------------------------------------------

TARGET.write_text(code, encoding="utf-8")

print("MJ V25.2: autonomous_v25_2.py installed")
print("MJ V25.2: size =", TARGET.stat().st_size, "bytes")

py_compile.compile(
    str(TARGET),
    doraise=True
)

print("MJ V25.2: syntax OK")