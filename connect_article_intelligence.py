from pathlib import Path

path = Path("./mj_web.py")
text = path.read_text(encoding="utf-8")

start_marker = "    def enrich_results("
end_marker = "    # =========================================================\n    # UNIQUE RESULTS"

start = text.find(start_marker)

if start < 0:
    raise SystemExit("ERROR: enrich_results not found")

end = text.find(
    end_marker,
    start
)

if end < 0:
    raise SystemExit("ERROR: UNIQUE RESULTS section not found")

new_function = r'''    def enrich_results(
        self,
        results,
        max_pages=3,
        max_chars=12000
    ):

        enriched = []

        try:
            max_pages = int(
                max_pages
            )
        except Exception:
            max_pages = 3

        try:
            max_chars = int(
                max_chars
            )
        except Exception:
            max_chars = 12000

        for item in results:

            if len(enriched) >= max_pages:
                break

            if not isinstance(
                item,
                dict
            ):
                continue

            url = str(
                item.get(
                    "url",
                    ""
                )
            ).strip()

            if not url:
                continue

            try:

                print(
                    "MJ WEB PAGE READ:",
                    url
                )

                page = self.fetch_page(
                    url,
                    max_chars
                )

            except Exception as exc:

                print(
                    "MJ WEB PAGE READ ERROR:",
                    exc
                )

                continue

            if not page:
                continue

            merged = dict(
                item
            )

            if isinstance(
                page,
                dict
            ):

                merged.update(
                    page
                )

            else:

                merged[
                    "content"
                ] = str(
                    page
                )

            raw_content = str(
                merged.get(
                    "content",
                    ""
                )
            ).strip()

            title = str(
                merged.get(
                    "title",
                    item.get(
                        "title",
                        ""
                    )
                )
            ).strip()

            if not raw_content:
                continue

            # -------------------------------------------------
            # ARTICLE INTELLIGENCE EXTRACTION
            # -------------------------------------------------

            article_content = (
                self.extract_article_content(
                    raw_content,
                    title,
                    max_chars
                )
            )

            if not article_content:

                article_content = (
                    self.clean_page_content(
                        raw_content,
                        max_chars
                    )
                )

            merged[
                "raw_content"
            ] = raw_content

            merged[
                "content"
            ] = article_content

            merged[
                "content_chars"
            ] = len(
                article_content
            )

            merged[
                "search_title"
            ] = str(
                item.get(
                    "title",
                    title
                )
            )

            merged[
                "page_read"
            ] = True

            merged[
                "article_extracted"
            ] = bool(
                article_content
            )

            if article_content:

                print(
                    "MJ ARTICLE EXTRACTED:",
                    len(raw_content),
                    "=>",
                    len(article_content),
                    "chars"
                )

            enriched.append(
                merged
            )

        return enriched


'''

new_text = (
    text[:start]
    + new_function
    + text[end:]
)

path.write_text(
    new_text,
    encoding="utf-8"
)

print(
    "MJ ENRICH RESULTS CONNECTED TO ARTICLE INTELLIGENCE"
)
