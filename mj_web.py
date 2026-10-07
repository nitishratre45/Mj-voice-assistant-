from __future__ import annotations

import json
import urllib.parse
import urllib.request
from html import unescape
from html.parser import HTMLParser

from config import WEB_MAX_RESPONSE_BYTES, WEB_REQUEST_TIMEOUT_SECONDS


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.parts.append(text)


class MJWeb:
    """Free-key web search/fetch layer with strict HTTP(S) validation."""

    USER_AGENT = "MJ-Voice-Assistant/1.0"

    def _request(self, url: str) -> bytes:
        parsed = urllib.parse.urlparse(str(url or ""))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Only http(s) URLs are allowed")
        req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
        with urllib.request.urlopen(req, timeout=WEB_REQUEST_TIMEOUT_SECONDS) as response:
            return response.read(WEB_MAX_RESPONSE_BYTES)

    def fetch_page(self, url: str) -> str:
        try:
            raw = self._request(url)
            parser = _TextParser()
            parser.feed(raw.decode("utf-8", errors="replace"))
            return " ".join(parser.parts)
        except Exception as exc:
            print("MJ WEB FETCH WARNING:", exc)
            return ""

    def search(self, query: str, limit: int = 5) -> list[dict]:
        query = str(query or "").strip()
        limit = max(1, min(int(limit or 5), 10))
        if not query:
            return []

        encoded = urllib.parse.quote_plus(query)
        # Wikipedia is a free, keyless API and gives structured results.
        url = f"https://en.wikipedia.org/w/rest.php/v1/search/page?q={encoded}&limit={limit}"
        try:
            payload = json.loads(self._request(url).decode("utf-8", errors="replace"))
            results = []
            for item in payload.get("pages", [])[:limit]:
                title = str(item.get("title") or "").strip()
                snippet = str(item.get("description") or item.get("excerpt") or "").strip()
                key = str(item.get("key") or "").strip()
                page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(key.replace(' ', '_'))}" if key else ""
                if title or snippet:
                    results.append({
                        "title": title,
                        "snippet": unescape(snippet),
                        "content": unescape(snippet),
                        "url": page_url,
                        "source": "wikipedia",
                    })
            return results
        except Exception as exc:
            print("MJ WEB SEARCH WARNING:", exc)
            return []

    def stats(self) -> dict[str, int]:
        return {"searches": 0, "pages_fetched": 0}
