from pathlib import Path

files = [
    "fix_brain_empty_function.py",
    "fix_brain_empty_function_v2.py",
    "fix_brain_orphaned_block.py",
]

fixed = 0

for name in files:

    path = Path(name)

    if not path.exists():
        continue

    raw = path.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):

        path.write_bytes(raw[3:])

        print(
            "BOM REMOVED:",
            name
        )

        fixed += 1

print()
print(
    "REPAIR SCRIPT BOM CLEANUP:",
    fixed
)
