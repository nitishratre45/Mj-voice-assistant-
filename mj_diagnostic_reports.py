from __future__ import annotations

import importlib
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Optional

from config import (
    GEMINI_MODEL,
    TESSERACT_CMD,
    WHISPER_MODEL,
)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def _check_import(name: str) -> Check:
    try:
        importlib.import_module(name)
        return Check(name, True, "available")
    except Exception as exc:
        return Check(name, False, f"{type(exc).__name__}: {exc}")


def _check_command(name: str) -> Check:
    path = shutil.which(name)
    return Check(name, bool(path), path or "not found")


def run_health_check() -> dict:
    checks = [
        Check("python", True, sys.version.split()[0]),
        Check("platform", True, f"{platform.system()} {platform.release()}"),
        _check_import("numpy"),
        _check_import("sounddevice"),
        _check_import("faster_whisper"),
        _check_import("pygame"),
        _check_import("pyautogui"),
        _check_import("pytesseract"),
        _check_import("PIL"),
        Check(
            "edge-tts",
            bool(shutil.which("edge-tts")),
            shutil.which("edge-tts") or "not found",
        ),
        _check_command("python"),
        Check(
            "tesseract",
            bool(shutil.which("tesseract")) or bool(TESSERACT_CMD),
            TESSERACT_CMD or "not configured",
        ),
        Check(
            "whisper",
            bool(WHISPER_MODEL),
            WHISPER_MODEL or "not configured",
        ),
        Check(
            "gemini",
            bool(shutil.which("python")) and bool(GEMINI_MODEL),
            GEMINI_MODEL or "not configured",
        ),
    ]

    passed = sum(1 for c in checks if c.ok)
    return {
        "ok": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": [asdict(c) for c in checks],
    }


def format_health_check(result: Optional[dict] = None) -> str:
    result = result or run_health_check()
    failed = [c for c in result["checks"] if not c["ok"]]
    if not failed:
        return f"MJ health check clear hai. {result['passed']} checks pass hain."

    details = "; ".join(
        f"{c['name']}: {c['detail']}" for c in failed[:4]
    )
    return (
        f"MJ health check mein {len(failed)} issue mile. "
        f"{details}"
    )


if __name__ == "__main__":
    report = run_health_check()
    print(format_health_check(report))
