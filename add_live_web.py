from pathlib import Path

path = Path("brain.py")
text = path.read_text(encoding="utf-8")

marker = "    def context_summary(self):"

pos = text.find(marker)

if pos == -1:
    raise SystemExit("ERROR: context_summary not found")

section = r'''

    # =========================================================
    # MJ UNIFIED KNOWLEDGE ENGINE
    # =========================================================

    def search_mj_knowledge(
        self,
        query,
        limit=8,
        live=False
    ):

        query = str(query or "").strip()

        if not query:
            return {
                "memories": [],
                "web": [],
                "conversations": []
            }

        memories = []
        web_results = []
        conversations = []

        try:

            if getattr(
                self,
                "mj_knowledge",
                None
            ):

                memories = (
                    self.mj_knowledge.search_memory(
                        query,
                        limit
                    )
                )

        except Exception as exc:

            print(
                "MJ MEMORY SEARCH ERROR:",
                exc
            )

        try:

            if getattr(
                self,
                "mj_knowledge",
                None
            ):

                web_results = (
                    self.mj_knowledge.search_web_knowledge(
                        query,
                        limit
                    )
                )

        except Exception as exc:

            print(
                "MJ WEB MEMORY SEARCH ERROR:",
                exc
            )

        if live:

            try:

                live_results = (
                    self.search_live_web_for_mj(
                        query,
                        limit,
                        True
                    )
                )

                if live_results:
                    web_results = live_results

            except Exception as exc:

                print(
                    "MJ LIVE SEARCH ERROR:",
                    exc
                )

        return {
            "memories": memories or [],
            "web": web_results or [],
            "conversations": conversations or []
        }


    # =========================================================
    # MJ LIVE WEB
    # =========================================================

    def search_live_web_for_mj(
        self,
        query,
        limit=8,
        save_results=True
    ):

        try:

            query = str(
                query or ""
            ).strip()

            if not query:
                return []

            web = getattr(
                self,
                "mj_web",
                None
            )

            if web is None:
                return []

            results = web.search(
                query,
                limit
            )

            if not results:
                return []

            if save_results:

                for item in results:

                    try:

                        title = str(
                            item.get(
                                "title",
                                ""
                            )
                        ).strip()

                        snippet = str(
                            item.get(
                                "snippet",
                                ""
                            )
                        ).strip()

                        url = str(
                            item.get(
                                "url",
                                ""
                            )
                        ).strip()

                        if not title and not snippet:
                            continue

                        self.save_web_knowledge_for_mj(
                            title or query,
                            snippet,
                            url,
                            "live_web",
                            1.0
                        )

                    except Exception as exc:

                        print(
                            "MJ WEB SAVE ERROR:",
                            exc
                        )

            print(
                "MJ LIVE WEB RESULTS:",
                len(results)
            )

            return results

        except Exception as exc:

            print(
                "MJ LIVE WEB ERROR:",
                exc
            )

            return []


    def ask_live_web_for_mj(
        self,
        query,
        limit=5
    ):

        results = (
            self.search_live_web_for_mj(
                query,
                limit,
                True
            )
        )

        if not results:

            return (
                "Internet par relevant information nahi mili.",
                "hi"
            )

        previews = []

        for item in results[:5]:

            title = str(
                item.get(
                    "title",
                    ""
                )
            ).strip()

            snippet = str(
                item.get(
                    "snippet",
                    ""
                )
            ).strip()

            if title and snippet:

                previews.append(
                    title + ": " + snippet
                )

            elif title:

                previews.append(title)

            elif snippet:

                previews.append(snippet)

        return (
            "Internet se mili information: "
            + " | ".join(previews),
            "hi"
        )


    def get_live_web_stats(self):

        try:

            web = getattr(
                self,
                "mj_web",
                None
            )

            if web is None:
                return {}

            return web.stats()

        except Exception as exc:

            print(
                "MJ WEB STATS ERROR:",
                exc
            )

            return {}
'''

text = (
    text[:pos]
    + section
    + "\n"
    + text[pos:]
)

path.write_text(
    text,
    encoding="utf-8"
)

print("MJ LIVE WEB METHODS ADDED")
