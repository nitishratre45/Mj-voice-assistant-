from __future__ import annotations

from pathlib import Path
import json
from storage_utils import atomic_write_json


class MJKnowledge:
    """Persistent local store for web knowledge and conversations."""

    def __init__(self, path=None):
        self.path = Path(path or Path(__file__).resolve().parent / "data" / "mj_knowledge.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.memories = []
        self.web_pages = []
        self.conversations = []
        self._load()

    def _load(self):
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.memories = data.get("memories", []) if isinstance(data.get("memories", []), list) else []
                    self.web_pages = data.get("web_pages", []) if isinstance(data.get("web_pages", []), list) else []
                    self.conversations = data.get("conversations", []) if isinstance(data.get("conversations", []), list) else []
        except Exception as exc:
            print("MJ KNOWLEDGE LOAD WARNING:", exc)

    def save(self):
        atomic_write_json(self.path, {
            "memories": self.memories[-500:],
            "web_pages": self.web_pages[-500:],
            "conversations": self.conversations[-500:],
        })

    def save_web_knowledge(self, title, content, url="", category="live_web", importance=1.0):
        item = {
            "title": str(title or "").strip(),
            "content": str(content or "").strip(),
            "url": str(url or "").strip(),
            "category": str(category or "live_web"),
            "importance": float(importance or 0),
        }
        if not item["title"] and not item["content"]:
            return False
        self.web_pages.append(item)
        self.save()
        return True

    def search_memory(self, query):
        q = str(query or "").lower().strip()
        return [x for x in self.memories if isinstance(x, dict) and q in str(x.get("content", "")).lower()]

    def search_web_knowledge(self, query):
        q = str(query or "").lower().strip()
        return [x for x in self.web_pages if isinstance(x, dict) and q in (str(x.get("title", "")) + " " + str(x.get("content", ""))).lower()]

    def search_conversations(self, query):
        q = str(query or "").lower().strip()
        return [x for x in self.conversations if isinstance(x, dict) and q in (str(x.get("user", "")) + " " + str(x.get("response", ""))).lower()]

    def stats(self):
        return {
            "memories": len([x for x in self.memories if isinstance(x, dict)]),
            "web_pages": len([x for x in self.web_pages if isinstance(x, dict)]),
            "conversations": len([x for x in self.conversations if isinstance(x, dict)]),
        }
