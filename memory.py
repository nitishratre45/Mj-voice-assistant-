from __future__ import annotations

from pathlib import Path
from typing import Any

from storage_utils import atomic_write_json
import json


class MJMemory:
    """Small, resilient persistent memory store for MJ."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or Path(__file__).resolve().parent / "data" / "memory.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self.data = raw
        except Exception as exc:
            print("MJ MEMORY LOAD WARNING:", exc)
            self.data = {}

    def save(self) -> bool:
        try:
            atomic_write_json(self.path, self.data)
            return True
        except Exception as exc:
            print("MJ MEMORY SAVE WARNING:", exc)
            return False

    def get(self, key: str, default: Any = "") -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any, save: bool = True) -> None:
        self.data[str(key)] = value
        if save:
            self.save()

    def search(self, query: str) -> list[dict[str, Any]]:
        q = str(query or "").strip().lower()
        if not q:
            return []
        return [
            {"key": key, "value": value}
            for key, value in self.data.items()
            if q in str(key).lower() or q in str(value).lower()
        ]

    def remember_command(self, command: str, target: str = "") -> None:
        command = str(command or "").strip()
        if not command:
            return
        self.data["last_command"] = command
        if target:
            self.data["last_target"] = target
        self.data["conversation_topic"] = target or command
        self.save()

    def stats(self) -> dict[str, int]:
        conversations = 1 if self.data.get("last_command") else 0
        ignored = {"last_command", "last_target", "conversation_topic", "user_name"}
        memories = sum(1 for k in self.data if k not in ignored)
        return {
            "memories": memories,
            "conversations": conversations,
            "keys": len(self.data),
        }
