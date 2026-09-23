from pathlib import Path
import json
import re

VOCAB_FILE = Path(__file__).with_name("mj_vocabulary.json")

DEFAULT_VOCAB = {
    "computer": ["laptop", "computer", "desktop", "screen", "keyboard", "mouse", "monitor", "folder", "file"],
    "apps": ["chrome", "browser", "visual studio code", "vs code", "notepad", "whatsapp", "telegram", "youtube"],
    "actions": ["open", "close", "click", "double click", "scroll up", "scroll down", "go back", "go forward", "type", "write", "search", "play", "pause", "stop", "minimize", "maximize"],
    "hinglish": ["mera naam kya hai", "mera naam", "mujhe batao", "kya kar sakte ho", "isko kholo", "isko band karo", "upar scroll karo", "neeche scroll karo", "file par click karo", "browser kholo", "laptop kholo"]
}


def load_vocabulary():
    try:
        if not VOCAB_FILE.exists():
            VOCAB_FILE.write_text(
                json.dumps(DEFAULT_VOCAB, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

        data = json.loads(
            VOCAB_FILE.read_text(encoding="utf-8-sig")
        )

        return data if isinstance(data, dict) else DEFAULT_VOCAB.copy()

    except Exception as exc:
        print("MJ VOCABULARY LOAD ERROR:", repr(exc))
        return DEFAULT_VOCAB.copy()


def get_all_entries():
    data = load_vocabulary()
    entries = []

    for key, values in data.items():
        if key == "aliases":
            continue

        if isinstance(values, list):
            for value in values:
                text = str(value).strip()
                if text:
                    entries.append(text)

    # Include aliases as recognition vocabulary.
    aliases = data.get("aliases", {})

    if isinstance(aliases, dict):
        for canonical, values in aliases.items():
            canonical = str(canonical).strip()

            if canonical:
                entries.append(canonical)

            if isinstance(values, list):
                for value in values:
                    text = str(value).strip()
                    if text:
                        entries.append(text)

    seen = set()
    unique = []

    for entry in entries:
        key = entry.casefold()

        if key not in seen:
            seen.add(key)
            unique.append(entry)

    return unique


def _tokens(text):
    return re.findall(
        r"[a-z0-9]+",
        str(text).casefold()
    )


def find_relevant_vocabulary(text="", limit=40):
    entries = get_all_entries()

    if not entries:
        return []

    query = str(text).strip().casefold()
    query_tokens = _tokens(query)

    if not query_tokens:
        return entries[:limit]

    scored = []

    # Context groups prevent opposite/unrelated commands from competing.
    context_groups = {
        "scroll_up": {
            "scroll up", "scroll upward", "upar scroll",
            "upar scroll karo"
        },
        "scroll_down": {
            "scroll down", "scroll downward", "neeche scroll",
            "neeche scroll karo"
        },
        "click": {
            "click", "click karo"
        },
        "double_click": {
            "double click", "double click karo", "double-click",
            "doubleclick"
        },
        "name": {
            "mera naam kya hai", "mera naam kya h",
            "mera name kya hai", "my name kya hai",
            "what is my name", "whats my name"
        },
    }

    query_group = None
    for group_name, phrases in context_groups.items():
        if query in phrases or any(
            phrase in query for phrase in phrases
        ):
            query_group = group_name
            break

    for entry in entries:
        entry_normalized = entry.casefold().strip()

        # If the query clearly belongs to a command group,
        # ignore entries from the opposite group.
        if query_group == "scroll_up" and entry_normalized in context_groups["scroll_down"]:
            continue
        if query_group == "scroll_down" and entry_normalized in context_groups["scroll_up"]:
            continue
        if query_group == "click" and entry_normalized in context_groups["double_click"]:
            continue
        if query_group == "double_click" and entry_normalized in context_groups["click"]:
            continue
        entry_tokens = _tokens(entry_normalized)

        if not entry_tokens:
            continue

        score = 0

        # Exact complete phrase.
        if entry_normalized == query:
            score = 1000

        # User phrase contains the vocabulary phrase.
        elif entry_normalized in query:
            score = 500 + len(entry_tokens) * 10

        # Vocabulary phrase contains the complete user phrase.
        elif query in entry_normalized:
            score = 400 + len(query_tokens) * 10

        else:
            overlap = len(set(query_tokens) & set(entry_tokens))

            # Only keep genuinely related entries.
            if overlap == 0:
                continue

            coverage = overlap / max(len(query_tokens), 1)

            if coverage >= 0.5:
                score = 100 + overlap * 15

            elif len(query_tokens) <= 2 and overlap == 1:
                score = 60

            else:
                continue

        scored.append((score, entry))

    scored.sort(
        key=lambda item: (-item[0], item[1].casefold())
    )

    return [
        entry
        for _, entry in scored[:limit]
    ]


def get_whisper_prompt(purpose="command", text="", context_text=""):
    if purpose == "wake":
        entries = [
            x for x in get_all_entries()
            if x.casefold() in {"mj", "m j", "em jay"}
        ]

        if not entries:
            entries = ["MJ", "M J", "em jay"]

    else:
        # First use the current text when available.
        entries = find_relevant_vocabulary(
            text=text,
            limit=40
        )

        # If current text is unavailable, use recent context to
        # bias vocabulary selection without loading the full dictionary.
        if not text and context_text:
            context_entries = find_relevant_vocabulary(
                text=context_text,
                limit=20
            )

            # Preserve order while removing duplicates.
            entries = list(dict.fromkeys(context_entries + entries))

            # Keep the Whisper prompt bounded.
            entries = entries[:40]

    if not entries:
        return ""

    return (
        "Important vocabulary and phrases: "
        + ". ".join(entries)
        + "."
    )


def get_alias_map():
    data = load_vocabulary()
    aliases = data.get("aliases", {})

    result = {}

    if not isinstance(aliases, dict):
        return result

    for canonical, values in aliases.items():
        canonical = str(canonical).strip()

        if not canonical:
            continue

        result[canonical.casefold()] = canonical

        if isinstance(values, list):
            for value in values:
                alias = str(value).strip()

                if alias:
                    result[alias.casefold()] = canonical

    return result


def normalize_vocabulary_text(text):
    original = str(text).strip()

    if not original:
        return ""

    alias_map = get_alias_map()

    if not alias_map:
        return original

    normalized = original
    normalized_key = normalized.casefold().strip()

    # Exact phrase normalization.
    if normalized_key in alias_map:
        return alias_map[normalized_key]

    # Phrase-aware replacement, longest aliases first.
    replacements = sorted(
        alias_map.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for alias, canonical in replacements:
        if len(alias) < 2:
            continue

        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"

        normalized = re.sub(
            pattern,
            canonical,
            normalized,
            flags=re.IGNORECASE
        )

    return normalized


def canonical_vocabulary(text):
    return normalize_vocabulary_text(text)


def vocabulary_count():
    return len(get_all_entries())


if __name__ == "__main__":
    print("MJ VOCABULARY: READY")
    print("MJ VOCABULARY ENTRIES:", vocabulary_count())

    tests = [
        "open chrome",
        "scroll up",
        "mera naam kya hai",
        "file par click karo"
    ]

    for test in tests:
        result = find_relevant_vocabulary(test, limit=10)
        print()
        print("QUERY:", test)
        print("MATCHES:", result)
