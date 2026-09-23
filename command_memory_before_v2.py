import json
import time
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