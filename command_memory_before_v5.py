import json
import time
import re
from difflib import SequenceMatcher
from pathlib import Path


class CommandMemory:
    """
    MJ Personal Command Memory V1

    Remembers frequently used commands without changing
    the existing MJ brain/memory system.
    """

    def __init__(self, filename=None):
        root = Path(__file__).resolve().parent

        if filename is None:
            filename = root / "data" / "command_memory.json"

        self.file = Path(filename)
        self.file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.data = {
            "commands": {}
        }

        self._load()

    # --------------------------------------------------------
    # LOAD / SAVE
    # --------------------------------------------------------

    def _load(self):
        try:
            if self.file.exists():
                raw = json.loads(
                    self.file.read_text(
                        encoding="utf-8"
                    )
                )

                if isinstance(raw, dict):
                    self.data = raw

                if not isinstance(
                    self.data.get("commands"),
                    dict,
                ):
                    self.data["commands"] = {}

        except Exception as exc:
            print(
                "MJ COMMAND MEMORY LOAD WARNING:",
                exc,
            )

            self.data = {
                "commands": {}
            }

    def _save(self):
        try:
            self.file.write_text(
                json.dumps(
                    self.data,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        except Exception as exc:
            print(
                "MJ COMMAND MEMORY SAVE WARNING:",
                exc,
            )

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    def normalize(self, command):
        command = str(
            command or ""
        ).strip().lower()

        return " ".join(
            command.split()
        )

    # --------------------------------------------------------
    # REMEMBER
    # --------------------------------------------------------

    def remember(
        self,
        command,
        success=True,
        result=None,
    ):
        command = self.normalize(
            command
        )

        if not command:
            return

        if len(command) > 200:
            return

        commands = self.data.setdefault(
            "commands",
            {},
        )

        item = commands.get(
            command
        )

        now = time.time()

        if not isinstance(
            item,
            dict,
        ):
            item = {
                "count": 0,
                "first_seen": now,
                "last_seen": now,
                "success_count": 0,
                "last_result": "",
            }

        item["count"] = int(
            item.get("count", 0)
        ) + 1

        item["last_seen"] = now

        if success:
            item["success_count"] = (
                int(
                    item.get(
                        "success_count",
                        0,
                    )
                )
                + 1
            )

        if result:
            item["last_result"] = str(
                result
            )[:500]

        commands[command] = item

        self._save()

        print(
            "MJ MEMORY: learned command ->",
            command,
        )

    # --------------------------------------------------------
    # LOOKUP
    # --------------------------------------------------------

    def get(self, command):
        command = self.normalize(
            command
        )

        return self.data.get(
            "commands",
            {}
        ).get(command)

    # --------------------------------------------------------
    # FREQUENT COMMANDS
    # --------------------------------------------------------

    def frequent(self, limit=10):
        commands = self.data.get(
            "commands",
            {},
        )

        items = []

        for command, item in commands.items():

            if not isinstance(
                item,
                dict,
            ):
                continue

            items.append(
                (
                    int(
                        item.get(
                            "count",
                            0,
                        )
                    ),
                    command,
                    item,
                )
            )

        items.sort(
            key=lambda x: (
                x[0],
                x[2].get(
                    "last_seen",
                    0,
                ),
            ),
            reverse=True,
        )

        return items[:limit]

    # --------------------------------------------------------
    # SMART MATCHING V2
    # --------------------------------------------------------

    def _intent_tokens(self, text):
        """
        Convert common Hindi/Hinglish/English action
        variations into a common intent vocabulary.
        """

        text = self.normalize(text)

        replacements = {
            # OPEN
            "open": "open",
            "opened": "open",
            "opening": "open",
            "khol": "open",
            "kholo": "open",
            "kholna": "open",
            "khol do": "open",
            "kholna hai": "open",
            "chalu": "open",
            "chalao": "open",
            "chala do": "open",

            # SEARCH
            "search": "search",
            "searched": "search",
            "find": "search",
            "look": "search",
            "dhundo": "search",
            "dhoondo": "search",
            "khojo": "search",
            "search karo": "search",

            # CLOSE
            "close": "close",
            "closed": "close",
            "band": "close",
            "banda": "close",
            "band karo": "close",
            "band kar": "close",

            # CLICK
            "click": "click",
            "press": "click",
            "dabao": "click",
            "dabana": "click",
            "par click": "click",

            # SCROLL
            "scroll": "scroll",
            "upar": "up",
            "neeche": "down",
            "down": "down",
            "up": "up",

            # PLAY
            "play": "play",
            "chala": "play",
            "bajao": "play",
            "baja do": "play",
        }

        for phrase, replacement in sorted(
            replacements.items(),
            key=lambda x: len(x[0]),
            reverse=True,
        ):
            text = text.replace(
                phrase,
                replacement,
            )

        return text

    def _intent_similarity(self, a, b):
        a = self._intent_tokens(a)
        b = self._intent_tokens(b)

        if not a or not b:
            return 0.0

        return SequenceMatcher(
            None,
            a,
            b,
        ).ratio()

    def _tokens(self, text):
        text = self.normalize(text)

        tokens = re.findall(
            r"[a-zA-Z0-9\u0900-\u097F]+",
            text,
        )

        # Common Hinglish command variations.
        aliases = {
            "open": "khol",
            "opened": "khol",
            "khol": "khol",
            "kholo": "khol",
            "kholna": "khol",
            "kholna": "khol",
            "kar": "kar",
            "karo": "kar",
            "do": "kar",
            "open karo": "khol",
            "open kar": "khol",
            "open karna": "khol",
        }

        normalized = []

        for token in tokens:

            replacement = aliases.get(
                token,
                token,
            )

            normalized.append(
                replacement
            )

        return set(normalized)

    def _similarity(self, a, b):
        a = self.normalize(a)
        b = self.normalize(b)

        if not a or not b:
            return 0.0

        sequence_score = SequenceMatcher(
            None,
            a,
            b,
        ).ratio()

        tokens_a = self._tokens(a)
        tokens_b = self._tokens(b)

        if tokens_a and tokens_b:

            union = tokens_a | tokens_b
            overlap = tokens_a & tokens_b

            token_score = (
                len(overlap) / len(union)
            )

        else:
            token_score = 0.0

        intent_score = self._intent_similarity(
            a,
            b,
        )

        return (
            sequence_score * 0.35
            + token_score * 0.30
            + intent_score * 0.35
        )

    def find_match(
        self,
        command,
        minimum=0.62,
    ):
        """
        Find the best remembered command.

        Returns a dictionary with the matched command
        and confidence, or None.
        """

        query = self.normalize(
            command
        )

        if not query:
            return None

        commands = self.data.get(
            "commands",
            {},
        )

        best = None

        for remembered, item in commands.items():

            if not isinstance(
                item,
                dict,
            ):
                continue

            raw_score = self._similarity(
                query,
                remembered,
            )

            count = int(
                item.get(
                    "count",
                    0,
                )
            )

            success_count = int(
                item.get(
                    "success_count",
                    0,
                )
            )

            if count > 0:
                success_ratio = (
                    success_count / count
                )
            else:
                success_ratio = 0.0

            score = (
                raw_score
                + min(
                    0.08,
                    success_ratio * 0.08,
                )
            )

            # Confidence must always stay between 0 and 1.
            score = max(
                0.0,
                min(
                    1.0,
                    score,
                ),
            )

            candidate = {
                "command": remembered,
                "score": score,
                "raw_score": raw_score,
                "count": count,
                "success_count": success_count,
                "result": str(
                    item.get(
                        "last_result",
                        "",
                    )
                ),
            }

            if (
                best is None
                or candidate["score"]
                > best["score"]
            ):
                best = candidate

        if best is None:
            return None

        if best["score"] < minimum:
            return None

        return best

    def explain_match(
        self,
        command,
        minimum=0.62,
    ):
        match = self.find_match(
            command,
            minimum=minimum,
        )

        if match is None:
            return (
                "MJ MEMORY MATCH: none"
            )

        return (
            "MJ MEMORY MATCH: "
            f"{command!r} -> "
            f"{match['command']!r} "
            f"(confidence="
            f"{match['score']:.2f}, "
            f"used={match['count']}x)"
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def describe(self):
        total = len(
            self.data.get(
                "commands",
                {},
            )
        )

        frequent = self.frequent(
            limit=5
        )

        lines = [
            "MJ COMMAND MEMORY",
            f"stored_commands={total}",
        ]

        for count, command, item in frequent:
            lines.append(
                f"{count}x -> {command}"
            )

        return "\n".join(lines)