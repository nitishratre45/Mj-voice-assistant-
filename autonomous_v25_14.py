import re
import time
import webbrowser
from urllib.parse import quote_plus




def _v25_7_is_real_youtube_candidate(text, query=""):
    """
    V25.7:
    Reject hashtags, URLs, YouTube UI text and obvious metadata.
    Prefer candidates containing the actual search words.
    """
    if not text:
        return False

    value = str(text).strip().lower()
    query = str(query or "").strip().lower()

    if not value:
        return False

    # Never click hashtags
    if value.startswith("#"):
        return False

    # Never click navigation/search URLs
    blocked = (
        "youtube.com/results",
        "search_query=",
        "youtube.com",
        "www.youtube.com",
        "youtube",
        "google.com",
        "search",
        "home",
        "shorts",
        "subscriptions",
    )

    if value.startswith("http://") or value.startswith("https://"):
        return False

    if any(x in value for x in blocked):
        return False

    # Remove obvious metadata
    metadata = (
        "views",
        "view",
        "hours ago",
        "hour ago",
        "minutes ago",
        "minute ago",
        "days ago",
        "day ago",
        "weeks ago",
        "week ago",
        "months ago",
        "month ago",
        "years ago",
        "year ago",
    )

    # A candidate made almost entirely from metadata is not a title
    words = value.split()

    if len(words) < 2:
        return False

    metadata_count = sum(
        1 for w in words
        if w in {
            "views",
            "view",
            "ago",
            "hours",
            "hour",
            "minutes",
            "minute",
            "days",
            "day",
            "weeks",
            "week",
            "months",
            "month",
            "years",
            "year",
        }
    )

    if metadata_count >= max(2, len(words) // 2):
        return False

    # Query relevance
    query_words = [
        w for w in re.findall(r"[a-z0-9]+", query)
        if len(w) > 2
    ]

    if query_words:
        matched = sum(1 for w in query_words if w in value)

        # For Tilak Varma, at least one meaningful query word
        # should normally be present.
        if matched == 0:
            return False

    return True


def _v25_2_is_valid_youtube_result(text):
    """
    Return True only for plausible YouTube video/title text.
    """
    if not text:
        return False

    value = str(text).strip().lower()

    if value.startswith("#"):
        return False

    blocked = (
        "youtube.com/results",
        "search_query=",
        "youtube.com",
        "www.youtube.com",
    )

    if any(x in value for x in blocked):
        return False

    return True
class AutonomousV25:

    def __init__(self, controller, max_steps=25, observe_delay=0.8):
        self.controller = controller
        self.max_steps = max_steps
        self.observe_delay = observe_delay

    # ---------------------------------------------------------
    # SCREEN OBSERVATION
    # ---------------------------------------------------------

    def observe(self):
        try:
            data = self.controller.reader.read_screen(
                self.controller.screen
            )
            return data if isinstance(data, list) else []
        except Exception as e:
            print("MJ V25: OBSERVE ERROR =", e)
            return []

    def visible_text(self, data):
        out = []

        for item in data:
            if not isinstance(item, dict):
                continue

            text = str(item.get("text", "")).strip()

            if text:
                out.append(text)

        return " ".join(out)

    def normalized_text(self, data):
        return self.visible_text(data).lower()

    # ---------------------------------------------------------
    # GOAL UNDERSTANDING
    # ---------------------------------------------------------

    def understand_goal(self, goal):

        g = goal.lower().strip()

        browser = None

        if "youtube" in g:
            browser = "youtube"

        elif "google" in g or "chrome" in g:
            browser = "google"

        search = any(
            x in g
            for x in [
                "search",
                "sarch",
                "dhundo",
                "find",
                "lookup"
            ]
        )

        scroll_down = any(
            x in g
            for x in [
                "scroll down",
                "neeche scroll",
                "neeche jao",
                "down scroll"
            ]
        )

        scroll_up = any(
            x in g
            for x in [
                "scroll up",
                "upar scroll",
                "upar jao",
                "up scroll"
            ]
        )

        click = any(
            x in g
            for x in [
                "click",
                "par click",
                "open result",
                "result kholo",
                "result open",
                "video kholo"
            ]
        )

        query = ""

        markers = [
            "search karo",
            "search kar",
            "sarch karo",
            "dhundo",
            "find",
            "lookup"
        ]

        positions = []

        for marker in markers:
            pos = g.find(marker)

            if pos >= 0:
                positions.append((pos, marker))

        if positions:

            pos, marker = min(
                positions,
                key=lambda x: x[0]
            )

            before = g[:pos]

            remove_words = [
                "youtube kholo",
                "youtube khol",
                "youtube open",
                "google kholo",
                "google khol",
                "google open",
                "chrome kholo",
                "chrome khol",
                "chrome open",
                "please",
                "aur",
                "phir",
                "karo"
            ]

            for word in remove_words:
                before = before.replace(
                    word,
                    " "
                )

            query = " ".join(
                before.split()
            ).strip(" ,.!?:;-_")

            # Remove accidental command punctuation
            query = " ".join(
                query.split()
            ).strip(" ,.!?:;-_")

        plan = {
            "browser": browser,
            "search": search,
            "query": query,
            "scroll_down": scroll_down,
            "scroll_up": scroll_up,
            "click": click
        }

        print("=" * 72)
        print("MJ V25.14: GOAL UNDERSTANDING")
        print("=" * 72)
        print("  browser     =", browser)
        print("  search      =", search)
        print("  query       =", repr(query))
        print("  scroll_down =", scroll_down)
        print("  scroll_up   =", scroll_up)
        print("  click       =", click)
        print("=" * 72)

        return plan

    # ---------------------------------------------------------
    # PAGE DETECTION
    # ---------------------------------------------------------

    def detect_page(self, data):

        text = self.normalized_text(data)

        youtube_score = 0
        google_score = 0

        if "youtube" in text:
            youtube_score += 5

        if "youtube.com" in text:
            youtube_score += 5

        if "google" in text:
            google_score += 3

        if "google.com" in text:
            google_score += 5

        if "search" in text:
            google_score += 1
            youtube_score += 1

        if youtube_score > google_score and youtube_score >= 4:
            page = "youtube"

        elif google_score >= 4:
            page = "google"

        else:
            page = "unknown"

        return page

    # ---------------------------------------------------------
    # BROWSER OPEN
    # ---------------------------------------------------------

    def open_browser(self, browser, query=""):

        browser = str(browser or "").strip().lower()

        if browser not in {
            "",
            "google",
            "youtube",
        }:
            return False, (
                f"Unsupported browser target: {browser}"
            )

        if browser == "youtube":

            if query:
                url = (
                    "https://www.youtube.com/results"
                    "?search_query="
                    + quote_plus(query)
                )
            else:
                url = "https://www.youtube.com"

        else:

            if query:
                url = (
                    "https://www.google.com/search?q="
                    + quote_plus(query)
                )
            else:
                url = "https://www.google.com"

        print("MJ V25: OPEN =", url)

        try:

            webbrowser.open(url)

            return True, (
                browser +
                " khol diya."
            )

        except Exception as e:

            return False, str(e)

    # ---------------------------------------------------------
    # WAIT / VERIFY PAGE
    # ---------------------------------------------------------

    def wait_for_page(self, browser):

        print(
            "MJ V25: Waiting for",
            browser,
            "..."
        )

        for i in range(1, 9):

            time.sleep(1)

            data = self.observe()

            page = self.detect_page(data)

            print(
                f"MJ V25.14: PAGE CHECK "
                f"{i}/8 -> {page}, "
                f"elements={len(data)}"
            )

            if page == browser:
                return True, data

        return False, self.observe()

    # ---------------------------------------------------------
    # SEARCH RESULT SCORING
    # ---------------------------------------------------------

    def find_best_result(self, data, query):
        """V25.9: robust YouTube result detection."""

        query = str(query or "").strip().lower()

        query_words = [
            w for w in re.findall(r"[a-z0-9]+", query)
            if len(w) > 2
        ]

        candidates = []

        for item in data:
            if not isinstance(item, dict):
                continue

            raw = str(item.get("text", "")).strip()
            normalized = str(
                item.get("normalized", raw)
            ).strip().lower()

            if not normalized:
                continue

            # -------------------------------------------------
            # Reject URLs / browser navigation
            # -------------------------------------------------
            compact = re.sub(
                r"[^a-z0-9:/?=._-]",
                "",
                normalized
            )

            if (
                "youtube.com/results" in normalized
                or "youtubecom/results" in compact
                or "search_query" in normalized
                or "searchquery" in compact
                or normalized.startswith("http")
                or "www.youtube.com" in normalized
                or "wwwyoutubecom" in compact
            ):
                continue

            # OCR can miss punctuation in URLs.
            if (
                "youtube" in normalized
                and ("results" in normalized or "search" in normalized)
                and len(normalized) > 20
            ):
                continue

            # -------------------------------------------------
            # Reject hashtags
            # -------------------------------------------------
            if "#" in raw or "#" in normalized:
                continue

            # -------------------------------------------------
            # Reject obvious UI
            # -------------------------------------------------
            blocked = (
                "youtube.com",
                "google.com",
                "new tab",
                "search results",
                "search",
                "home",
                "shorts",
                "subscriptions",
                "library",
                "history",
            )

            if any(x in normalized for x in blocked):
                continue

            words = normalized.split()

            if len(words) < 2:
                continue

            matched = sum(
                1
                for word in query_words
                if word in normalized
            )

            # For Tilak Varma, BOTH must appear.
            if len(query_words) >= 2 and matched < 2:
                continue

            score = 0.0

            # Query relevance.
            score += matched * 100

            # Exact phrase bonus.
            if query and query in normalized:
                score += 150

            # Title-like text.
            if len(words) >= 5:
                score += 30

            if len(words) >= 8:
                score += 20

            # Metadata penalty.
            metadata = {
                "views",
                "view",
                "ago",
                "hours",
                "hour",
                "minutes",
                "minute",
                "days",
                "day",
                "weeks",
                "week",
                "months",
                "month",
                "years",
                "year",
                "live",
                "recently",
                "uploaded",
                "unwatched",
                "watched",
            }

            metadata_count = sum(
                1
                for word in words
                if word in metadata
            )

            score -= metadata_count * 10

            confidence = float(
                item.get("confidence", 0) or 0
            )

            score += confidence * 0.10

            candidates.append(
                (score, item)
            )

        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )

        print(
            "MJ V25.14: RESULT CANDIDATES =",
            len(candidates)
        )

        for score, item in candidates[:10]:
            print(
                " ",
                round(score, 1),
                "|",
                item.get("text"),
                "| confidence=",
                item.get("confidence")
            )

        if not candidates:
            # -------------------------------------------------
            # V25.12 OCR FALLBACK
            #
            # YouTube often returns a title as separate OCR
            # boxes:
            #
            #     Tilak
            #     Varma
            #
            # The strict scorer above rejects these because
            # neither individual OCR box contains both words.
            # Group nearby OCR boxes into one virtual result.
            # -------------------------------------------------

            fallback_items = []

            for item in data:
                if not isinstance(item, dict):
                    continue

                raw = str(
                    item.get("text", "")
                ).strip()

                normalized = str(
                    item.get(
                        "normalized",
                        raw
                    )
                ).strip().lower()

                if not normalized:
                    continue

                # Never use hashtags as YouTube videos.
                if (
                    "#" in raw
                    or "#" in normalized
                ):
                    continue

                # Never use URLs/navigation.
                compact = re.sub(
                    r"[^a-z0-9:/?=._-]",
                    "",
                    normalized
                )

                if (
                    normalized.startswith("http")
                    or "youtube.com" in normalized
                    or "youtubecom" in compact
                    or "search_query" in normalized
                    or "searchquery" in compact
                ):
                    continue

                # Reject obvious navigation/UI.
                blocked_fallback = (
                    "search results",
                    "new tab",
                    "subscriptions",
                    "library",
                    "history",
                    "shorts",
                )

                if any(
                    word in normalized
                    for word in blocked_fallback
                ):
                    continue

                x = item.get("center_x")
                y = item.get("center_y")

                if x is None or y is None:
                    ix = item.get("x")
                    iy = item.get("y")

                    if (
                        ix is None
                        or iy is None
                    ):
                        continue

                    x = (
                        float(ix)
                        + float(
                            item.get(
                                "width",
                                0
                            )
                        ) / 2
                    )

                    y = (
                        float(iy)
                        + float(
                            item.get(
                                "height",
                                0
                            )
                        ) / 2
                    )

                try:
                    x = float(x)
                    y = float(y)
                except Exception:
                    continue

                fallback_items.append(
                    {
                        "item": item,
                        "text": normalized,
                        "x": x,
                        "y": y,
                        "confidence": float(
                            item.get(
                                "confidence",
                                0
                            ) or 0
                        )
                    }
                )

            # Look for query words in nearby OCR boxes.
            if len(query_words) >= 2:

                for left in fallback_items:

                    left_matches = [
                        word
                        for word in query_words
                        if word in left["text"]
                    ]

                    if not left_matches:
                        continue

                    for right in fallback_items:

                        if left is right:
                            continue

                        right_matches = [
                            word
                            for word in query_words
                            if word in right["text"]
                        ]

                        if not right_matches:
                            continue

                        combined_words = set(
                            left_matches
                            + right_matches
                        )

                        if not all(
                            word in combined_words
                            for word in query_words
                        ):
                            continue

                        dx = abs(
                            left["x"]
                            - right["x"]
                        )

                        dy = abs(
                            left["y"]
                            - right["y"]
                        )

                        # Nearby title words are normally on
                        # the same line or close vertical lines.
                        if dx > 650 or dy > 160:
                            continue

                        # Do not combine two distant screen areas.
                        min_x = min(
                            left["x"],
                            right["x"]
                        )
                        max_x = max(
                            left["x"],
                            right["x"]
                        )

                        min_y = min(
                            left["y"],
                            right["y"]
                        )
                        max_y = max(
                            left["y"],
                            right["y"]
                        )

                        center_x = (
                            min_x + max_x
                        ) / 2

                        center_y = (
                            min_y + max_y
                        ) / 2

                        combined_text = (
                            left["text"]
                            + " "
                            + right["text"]
                        )

                        confidence = (
                            left["confidence"]
                            + right["confidence"]
                        ) / 2

                        fallback_score = (
                            300
                            + confidence * 0.2
                            - dy * 0.15
                            - dx * 0.02
                        )

                        virtual_item = {
                            "text": combined_text,
                            "normalized": combined_text,
                            "center_x": int(
                                center_x
                            ),
                            "center_y": int(
                                center_y
                            ),
                            "confidence": confidence
                        }

                        candidates.append(
                            (
                                fallback_score,
                                virtual_item
                            )
                        )

            candidates.sort(
                key=lambda x: x[0],
                reverse=True
            )

            print(
                "MJ V25.14: OCR GROUP FALLBACK =",
                len(candidates)
            )

            for score, item in candidates[:10]:
                print(
                    " ",
                    round(score, 1),
                    "|",
                    item.get("text"),
                    "| @",
                    item.get("center_x"),
                    item.get("center_y")
                )

            if not candidates:
                return None


        # -------------------------------------------------
        # V25.14: stronger result ranking
        # -------------------------------------------------

        def v25_14_quality(entry):
            score, item = entry

            text = str(
                item.get("text", "")
            ).strip().lower()

            quality = float(score)

            # Exact search phrase.
            if query and query in text:
                quality += 120

            # Both query words.
            if query_words and all(
                word in text
                for word in query_words
            ):
                quality += 80

            words = re.findall(
                r"[a-z0-9]+",
                text
            )

            # Prefer title-like text.
            if len(words) >= 4:
                quality += 25

            if len(words) >= 8:
                quality += 20

            # Penalize metadata-heavy OCR.
            metadata = {
                "views",
                "view",
                "ago",
                "hours",
                "hour",
                "minutes",
                "minute",
                "days",
                "day",
                "weeks",
                "week",
                "months",
                "month",
                "years",
                "year",
                "live",
                "recently",
                "uploaded",
                "unwatched",
                "watched",
            }

            metadata_count = sum(
                1
                for word in words
                if word in metadata
            )

            quality -= (
                metadata_count * 4
            )

            # Never prefer hashtags.
            if text.startswith("#"):
                quality -= 200

            # Never prefer browser/search URLs.
            if (
                "youtube.com/results" in text
                or "search_query" in text
                or text.startswith("http")
            ):
                quality -= 500

            return quality

        candidates.sort(
            key=v25_14_quality,
            reverse=True
        )

        print(
            "MJ V25.14: RANKED RESULTS =",
            len(candidates)
        )

        for rank, (score, item) in enumerate(
            candidates[:10],
            start=1
        ):
            print(
                " ",
                rank,
                "| base=",
                round(score, 1),
                "|",
                item.get("text"),
                "| @",
                item.get("center_x"),
                item.get("center_y")
            )

        return candidates[0][1]

    def verify_navigation(self, before):
        """
        V25.13: Verify that clicking a result caused
        the screen/page to change.

        We do not require a specific URL because YouTube
        navigation can take a moment and OCR may vary.
        """

        try:
            time.sleep(1.2)

            after = self.observe()

            if not isinstance(before, list):
                before = []

            if not isinstance(after, list):
                after = []

            before_text = " ".join(
                str(item.get("text", ""))
                for item in before
                if isinstance(item, dict)
            ).strip().lower()

            after_text = " ".join(
                str(item.get("text", ""))
                for item in after
                if isinstance(item, dict)
            ).strip().lower()

            # Basic screen-content change check.
            if before_text != after_text:
                print(
                    "MJ V25.14: NAVIGATION VERIFIED "
                    "(screen content changed)"
                )
                return True, after

            # Compare number of OCR elements.
            if len(before) != len(after):
                print(
                    "MJ V25.14: NAVIGATION VERIFIED "
                    "(element count changed)"
                )
                return True, after

            # A second observation helps when the first one
            # happens during page transition.
            time.sleep(1.0)

            after2 = self.observe()

            if not isinstance(after2, list):
                after2 = []

            after2_text = " ".join(
                str(item.get("text", ""))
                for item in after2
                if isinstance(item, dict)
            ).strip().lower()

            if after2_text != before_text:
                print(
                    "MJ V25.14: NAVIGATION VERIFIED "
                    "(second observation changed)"
                )
                return True, after2

            if len(after2) != len(before):
                print(
                    "MJ V25.14: NAVIGATION VERIFIED "
                    "(second element count changed)"
                )
                return True, after2

            print(
                "MJ V25.14: Navigation change not detected."
            )

            return False, after2

        except Exception as exc:
            print(
                "MJ V25.14: VERIFY ERROR =",
                exc
            )
            return False, []

    def click_item(self, item):
        """V25.10: click OCR item using ScreenController.screen.left_click()."""

        if not item:
            return False, "No item to click."

        x = item.get("center_x")
        y = item.get("center_y")

        if x is None or y is None:
            x = item.get("x")
            y = item.get("y")

            if x is not None and y is not None:
                x = int(x) + int(item.get("width", 0)) // 2
                y = int(y) + int(item.get("height", 0)) // 2

        if x is None or y is None:
            return False, "Item has no coordinates."

        try:
            x = int(x)
            y = int(y)

            text = str(item.get("text", "")).strip()

            print(
                f"MJ V25.14: CLICK {text} @ {x} {y}"
            )

            # ScreenController does not expose click().
            # Its actual low-level click is screen.left_click().
            success = self.controller.screen.left_click(
                x,
                y
            )

            success = bool(success)

            if success:
                return True, (
                    f"Click kar diya: {text} @ "
                    f"{x} {y}"
                )

            return False, (
                f"Click failed: {text} @ "
                f"{x} {y}"
            )

        except Exception as exc:
            print(
                "MJ V25.14: CLICK ERROR =",
                exc
            )

            return False, f"Click error: {exc}"

    def run(self, goal):

        plan = self.understand_goal(
            goal
        )

        state = {
            "browser": False,
            "search": False,
            "result": False,
            "scroll": False
        }

        history = []

        for step in range(
            1,
            self.max_steps + 1
        ):

            print()
            print(
                f"MJ V25.14: STEP "
                f"{step}/{self.max_steps}"
            )

            data = self.observe()

            page = self.detect_page(
                data
            )

            print(
                "MJ V25.14: PAGE =",
                page
            )

            # ---------------------------------
            # Browser
            # ---------------------------------

            if (
                plan["browser"]
                and not state["browser"]
            ):

                action = "open_browser"

            # ---------------------------------
            # Search
            # ---------------------------------

            elif (
                plan["search"]
                and not state["search"]
            ):

                action = "search"

            # ---------------------------------
            # Result
            # ---------------------------------

            elif (
                plan["click"]
                and not state["result"]
            ):

                action = "result"

            # ---------------------------------
            # Scroll
            # ---------------------------------

            elif (
                plan["scroll_down"]
                and not state["scroll"]
            ):

                action = "scroll_down"

            elif (
                plan["scroll_up"]
                and not state["scroll"]
            ):

                action = "scroll_up"

            else:

                action = "done"

            print(
                "MJ V25.14: DECISION =",
                action
            )

            # ---------------------------------
            # DONE
            # ---------------------------------

            if action == "done":

                print(
                    "MJ V25.14: GOAL COMPLETE"
                )

                return {
                    "success": True,
                    "goal": goal,
                    "steps": history,
                    "completed": True,
                    "reason":
                        "verified completed aur kuch karna hai boss"
                }

            success = False
            result = ""

            # ---------------------------------
            # OPEN BROWSER
            # ---------------------------------

            if action == "open_browser":

                success, result = (
                    self.open_browser(
                        plan["browser"]
                    )
                )

                if success:

                    state["browser"] = True

                    self.wait_for_page(
                        plan["browser"]
                    )

            # ---------------------------------
            # SEARCH
            # ---------------------------------

            elif action == "search":

                success, result = (
                    self.open_browser(
                        plan["browser"],
                        plan["query"]
                    )
                )

                if success:

                    state["search"] = True

                    time.sleep(2)

                    print(
                        "MJ V25: Search page opened."
                    )

            # ---------------------------------
            # RESULT
            # ---------------------------------

            elif action == "result":

                if not plan["query"]:

                    result = (
                        "Search query nahi mili."
                    )

                    success = False

                else:

                    # V25.11: YouTube results may need
                    # additional time to render.
                    item = None

                    for retry in range(1, 7):
                        item = (
                            self.find_best_result(
                                data,
                                plan["query"]
                            )
                        )

                        if item:
                            break

                        print(
                            f"MJ V25.14: RESULT WAIT {retry}/6"
                        )

                        time.sleep(1.2)

                        data = self.observe()

                    if item:

                        before = data

                        success, result = (
                            self.click_item(item)
                        )

                        if success:

                            verified, after = (
                                self.verify_navigation(
                                    before
                                )
                            )

                            if verified:

                                state[
                                    "result"
                                ] = True

                                result += (
                                    " | Navigation verified."
                                )

                            else:

                                success = False

                                result = (
                                    "Click hua, "
                                    "navigation verify "
                                    "nahi hua."
                                )

                    else:

                        success = False

                        result = (
                            "Relevant result "
                            "nahi mila."
                        )

            # ---------------------------------
            # SCROLL DOWN
            # ---------------------------------

            elif action == "scroll_down":

                success, result = (
                    self.scroll_down()
                )

                if success:
                    state["scroll"] = True

            # ---------------------------------
            # SCROLL UP
            # ---------------------------------

            elif action == "scroll_up":

                success, result = (
                    self.scroll_up()
                )

                if success:
                    state["scroll"] = True

            print(
                "MJ V25.14: RESULT =",
                result
            )

            history.append({
                "step": step,
                "action": action,
                "result": result,
                "success": success
            })

            if not success:

                print(
                    "MJ V25: ACTION FAILED"
                )

                return {
                    "success": False,
                    "goal": goal,
                    "steps": history,
                    "completed": False,
                    "reason":
                        "action_failed"
                }

            time.sleep(
                self.observe_delay
            )

        return {
            "success": False,
            "goal": goal,
            "steps": history,
            "completed": False,
            "reason":
                "max_steps_reached"
        }


def autonomous_screen_agent_v25(
    controller,
    goal,
    max_steps=25,
    observe_delay=0.8
):

    agent = AutonomousV25(
        controller,
        max_steps=max_steps,
        observe_delay=observe_delay
    )

    return agent.run(goal)
