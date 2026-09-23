from pathlib import Path

ROOT = Path(".")

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    "archive_old",
    "self_update_backups",
    "backup",
    "backups",
    "old",
    "archive",
}

def is_excluded(path):
    for part in path.parts:
        if part.lower() in {
            x.lower()
            for x in EXCLUDED_DIRS
        }:
            return True

    return False


fixed = []
skipped = []

for path in ROOT.rglob("*.py"):

    if is_excluded(path):
        skipped.append(str(path))
        continue

    try:

        raw = path.read_bytes()

        if raw.startswith(b"\xef\xbb\xbf"):

            clean = raw[3:]

            path.write_bytes(
                clean
            )

            fixed.append(
                str(path)
            )

    except Exception as exc:

        print(
            "ERROR:",
            path,
            exc
        )


print()
print("=" * 70)
print("MJ UTF-8 BOM CLEANUP")
print("=" * 70)

print(
    "BOM REMOVED:",
    len(fixed)
)

for item in fixed:
    print(
        " FIXED:",
        item
    )

print(
    "EXCLUDED:",
    len(skipped)
)

print("=" * 70)
