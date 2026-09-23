
import time
import webbrowser
from urllib.parse import quote_plus



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
        print("MJ V25: GOAL UNDERSTANDING")
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
                f"MJ V25: PAGE CHECK "
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

        words = [
            w.lower()
            for w in query.split()
            if len(w) >= 3
        ]

        candidates = []

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
            ).lower()

            confidence = float(
                item.get(
                    "confidence",
                    0
                )
            )

            if not raw:
                continue

            if confidence < 55:
                continue

            score = 0

            for word in words:

                if word in normalized:
                    score += 35

            if (
                query
                and query.lower()
                in normalized
            ):
                score += 80

            if len(normalized) >= 12:
                score += 8

            # Prefer actual content titles over tiny OCR fragments
            if len(normalized) >= 20:
                score += 12

            
            # V25.2: Strong preference for real video titles
            # Determine page type locally from the observed screen/data.
        page_type = ""
        try:
            page_type = str(
                getattr(self, "page_type", "")
            ).lower()
        except Exception:
            page_type = ""

        # Also infer YouTube from the current screen text.
        if not page_type:
            try:
                screen_text = " ".join(
                    str(x.get("text", ""))
                    for x in data
                    if isinstance(x, dict)
                ).lower()

                if (
                    "youtube" in screen_text
                    or "youtube.com" in screen_text
                ):
                    page_type = "youtube"
            except Exception:
                page_type = ""

        if page_type == "youtube":
                if len(normalized) >= 25:
                    score += 20

                if len(normalized) >= 40:
                    score += 10

                # Titles containing the requested query are highly relevant
                query_words = [
                    w.lower()
                    for w in query.split()
                    if len(w) > 2
                ]

                matched_words = sum(
                    1 for w in query_words
                    if w in normalized
                )

                score += matched_words * 15

                # Hashtags are not videos
                if normalized.startswith("#"):
                    score -= 100

            # Hashtag alone is weaker than a real title
            if normalized.startswith("#"):
                score -= 15

            # Browser/UI words should not win
            ui_words = [
                "youtube",
                "google",
                "search",
                "results",
                "home",
                "shorts"
            ]

            if any(
                w in normalized
                for w in ui_words
            ):
                score -= 10

            blocked = {
                "youtube",
                "google",
                "search",
                "home",
                "shorts",
                "history",
                "subscriptions",
                "settings",
                "menu"
            }

            # Never click browser/navigation URLs
            if (
                "youtube.com/results" in normalized
                or "google.com/search" in normalized
                or normalized.startswith("http://")
                or normalized.startswith("https://")
            ):
                continue

            
            # V25.2: Never treat hashtags as actual video results
            if normalized.startswith("#"):
                continue

            if normalized.startswith("hashtag"):
                continue

            # Ignore common YouTube navigation/UI elements
            youtube_ui = {
                "youtube",
                "home",
                "shorts",
                "subscriptions",
                "history",
                "library",
                "search",
                "create",
                "settings",
                "show more",
                "show less"
            }

            if normalized in youtube_ui:
                continue

            # Ignore obvious navigation/address-bar text
            if (
                "search_query=" in normalized
                or "youtube.com" in normalized
                and len(normalized) > 20
            ):
                continue

            if normalized in blocked:
                continue

            if score > 0:

                candidates.append(
                    (
                        score,
                        item
                    )
                )

        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )

        print(
            "MJ V25: RESULT CANDIDATES =",
            len(candidates)
        )

        for score, item in candidates[:10]:

            print(
                " ",
                score,
                "|",
                item.get("text"),
                "| confidence=",
                item.get("confidence")
            )

        if candidates:
            return candidates[0][1]

        return None

    # ---------------------------------------------------------
    # CLICK
    # ---------------------------------------------------------

    def click_item(self, item):

        if not item:
            return False, "Item nahi mila."

        x = item.get("center_x")
        y = item.get("center_y")

        if x is None or y is None:
            return False, (
                "Item coordinates nahi mile."
            )

        print(
            "MJ V25: CLICK",
            item.get("text"),
            "@",
            x,
            y
        )

        try:

            self.controller.screen.click(
                x,
                y,
                button="left"
            )

            return True, (
                "Click kar diya: "
                + str(item.get("text"))
            )

        except Exception as e:

            return False, str(e)

    # ---------------------------------------------------------
    # SCREEN CHANGE VERIFICATION
    # ---------------------------------------------------------

    def screen_changed(
        self,
        before,
        after
    ):

        before_text = self.normalized_text(
            before
        )

        after_text = self.normalized_text(
            after
        )

        if before_text != after_text:
            return True

        if abs(
            len(after) -
            len(before)
        ) >= 8:
            return True

        return False

    def verify_navigation(self, before):

        for i in range(1, 7):

            time.sleep(1)

            after = self.observe()

            changed = self.screen_changed(
                before,
                after
            )

            print(
                f"MJ V25: VERIFY "
                f"{i}/6 changed={changed}"
            )

            if changed:
                return True, after

        return False, self.observe()

    # ---------------------------------------------------------
    # SCROLL
    # ---------------------------------------------------------

    def scroll_down(self):

        try:

            self.controller.screen.scroll_down(
                5
            )

            return True, (
                "Screen neeche scroll kar di."
            )

        except Exception as e:

            return False, str(e)

    def scroll_up(self):

        try:

            self.controller.screen.scroll_up(
                5
            )

            return True, (
                "Screen upar scroll kar di."
            )

        except Exception as e:

            return False, str(e)

    # ---------------------------------------------------------
    # MAIN AUTONOMOUS LOOP
    # ---------------------------------------------------------

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
                f"MJ V25: STEP "
                f"{step}/{self.max_steps}"
            )

            data = self.observe()

            page = self.detect_page(
                data
            )

            print(
                "MJ V25: PAGE =",
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
                "MJ V25: DECISION =",
                action
            )

            # ---------------------------------
            # DONE
            # ---------------------------------

            if action == "done":

                print(
                    "MJ V25: GOAL COMPLETE"
                )

                return {
                    "success": True,
                    "goal": goal,
                    "steps": history,
                    "completed": True,
                    "reason":
                        "verified_completed"
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

                    item = (
                        self.find_best_result(
                            data,
                            plan["query"]
                        )
                    )

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
                "MJ V25: RESULT =",
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
