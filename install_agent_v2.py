from pathlib import Path
import py_compile

BASE = Path(__file__).resolve().parent
TARGET = BASE / "screen_agent.py"

if not TARGET.exists():
    raise SystemExit(f"screen_agent.py not found: {TARGET}")

MARKER = "# MJ AUTONOMOUS V2 OBSERVE VERIFY PATCH"

if MARKER in TARGET.read_text(encoding="utf-8"):
    print("MJ AUTONOMOUS V2: already installed")
else:
    original = TARGET.read_text(encoding="utf-8")
    backup = BASE / "screen_agent_before_v2.py"
    backup.write_text(original, encoding="utf-8")

    patch = r