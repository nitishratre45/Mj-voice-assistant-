# MJ Part 1 — Core + Voice Engine

This is the first implementation stage of MJ.

## What works

- Microphone auto-selection from Windows default input
- Ambient-noise calibration
- Voice activity detection
- Speech-to-text with Faster-Whisper
- Hindi / English / Hinglish language heuristic
- Wake word detection for MJ / M J / Em Jay
- Direct wake + command support
- Edge-TTS speech output
- Clean temporary audio handling
- Graceful Ctrl+C shutdown

## What intentionally does NOT exist yet

Part 1 does not contain the final brain, PC action system,
memory, planner, or autonomous reasoning. Those are later layers.

## Run

```powershell
pip install -r requirements.txt
python mj.py
```

First Whisper run may download the selected model.

## Test

Say:

    MJ

Then:

    YouTube kholo

Part 1 should repeat what it heard. Actual YouTube action belongs to
the later brain/action layers.
