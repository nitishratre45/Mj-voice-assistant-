from pathlib import Path

path = Path("mj_web.py")
text = path.read_text(encoding="utf-8")

marker = "    def _clean_page_content("

if marker in text:
    print("MJ PAGE CLEANER ALREADY EXISTS")
    raise SystemExit(0)

insert_at = text.find("    def enrich_results(")

if insert_at < 0:
    raise SystemExit(
        "ERROR: enrich_results() NOT FOUND"
    )

section = r'''    def _clean_page_content(
        self,
        content,
        max_chars=12000
    ):

        try:

            import re
            import html

            text = str(
                content or ""
            )

            # Decode HTML entities.
            text = html.unescape(
                text
            )

            # Remove scripts.
            text = re.sub(
                r"<script\b[^>]*>.*?</script>",
                " ",
                text,
                flags=re.I | re.S
            )

            # Remove styles.
            text = re.sub(
                r"<style\b[^>]*>.*?</style>",
                " ",
                text,
                flags=re.I | re.S
            )

            # Remove navigation-like HTML blocks.
            text = re.sub(
                r"<nav\b[^>]*>.*?</nav>",
                " ",
                text,
                flags=re.I | re.S
            )

            # Remove all remaining tags.
            text = re.sub(
                r"<[^>]+>",
                " ",
                text
            )

            # Decode entities again after tag removal.
            text = html.unescape(
                text
            )

            # Remove common website navigation noise.
            noise = [
                "skip to content",
                "skip to main content",
                "menu",
                "home",
                "about us",
                "contact us",
                "careers",
                "advertise",
                "promote",
                "trending",
                "newsletter",
                "privacy policy",
                "cookie policy",
                "terms of service",
                "sign in",
                "login",
                "subscribe",
                "search",
                "follow us",
                "related posts",
                "read more",
            ]

            lines = []

            for line in text.splitlines():

                line = " ".join(
                    line.split()
                ).strip()

                if not line:
                    continue

                lower = line.lower()

                if lower in noise:
                    continue

                # Ignore very short UI fragments.
                if len(line) < 3:
                    continue

                lines.append(
                    line
                )

            text = " ".join(
                lines
            )

            # Remove repeated spaces.
            text = re.sub(
                r"\s+",
                " ",
                text
            ).strip()

            # Remove repeated navigation fragments.
            for phrase in noise:
                pattern = (
                    r"\b"
                    + re.escape(phrase)
                    + r"\b"
                )

                text = re.sub(
                    pattern,
                    " ",
                    text,
                    flags=re.I
                )

            text = re.sub(
                r"\s+",
                " ",
                text
            ).strip()

            if max_chars:
                text = text[
                    :int(max_chars)
                ]

            return text

        except Exception as exc:

            print(
                "MJ PAGE CLEAN ERROR:",
                exc
            )

            return str(
                content or ""
            )[:int(max_chars)]


'''

new_text = (
    text[:insert_at]
    + section
    + text[insert_at:]
)

path.write_text(
    new_text,
    encoding="utf-8"
)

print(
    "MJ PAGE CONTENT CLEANER ADDED"
)
