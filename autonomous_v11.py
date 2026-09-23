
import time
import webbrowser
from urllib.parse import quote_plus


class AutonomousV11:

    def __init__(self, controller, max_steps=15, observe_delay=1.0):
        self.controller = controller
        self.max_steps = max_steps
        self.observe_delay = observe_delay
        self.browser = None

    def observe(self):
        try:
            data = self.controller.reader.read_screen(
                self.controller.screen
            )
            return data if isinstance(data, list) else []
        except Exception as e:
            print("MJ V11: OBSERVE ERROR =", e)
            return []

    def text(self, data):
        parts = []
        for x in data:
            if isinstance(x, dict):
                t = str(x.get("text", "")).strip()
                if t:
                    parts.append(t)
        return " ".join(parts).lower()

    def parse_goal(self, goal):
        g = goal.lower()

        browser = None
        if "youtube" in g:
            browser = "youtube"
        elif "google" in g or "chrome" in g:
            browser = "google"

        search = any(
            x in g
            for x in ["search", "sarch", "dhundo", "find"]
        )

        result = any(
            x in g
            for x in [
                "result kholo",
                "result open",
                "video kholo",
                "video open",
                "open result"
            ]
        )

        scroll = any(
            x in g
            for x in [
                "scroll down",
                "neeche scroll",
                "neeche jao"
            ]
        )

        query = ""

        markers = [
            "search karo",
            "sarch karo",
            "search",
            "sarch",
            "dhundo",
            "find"
        ]

        found = []

        for marker in markers:
            p = g.find(marker)
            if p >= 0:
                found.append((p, marker))

        if found:
            p, marker = min(found, key=lambda x: x[0])
            before = g[:p]

            for word in [
                "youtube kholo",
                "youtube khol",
                "youtube open",
                "google kholo",
                "google khol",
                "google open",
                "chrome kholo",
                "chrome khol",
                "chrome open",
                "aur",
                "phir",
                "please",
                "karo"
            ]:
                before = before.replace(word, " ")

            query = " ".join(before.split())

        print("MJ V11: GOAL")
        print("  browser =", browser)
        print("  search  =", search)
        print("  result  =", result)
        print("  scroll  =", scroll)
        print("  query   =", repr(query))

        return {
            "browser": browser,
            "search": search,
            "result": result,
            "scroll": scroll,
            "query": query
        }

    def open_search_page(self, browser, query=""):

        if browser == "youtube":
            if query:
                url = (
                    "https://www.youtube.com/results?search_query="
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

        print("MJ V11: OPEN URL =", url)

        try:
            webbrowser.open(url)
            self.browser = browser
            return True, browser + " khol diya."
        except Exception as e:
            return False, str(e)

    def wait_for_page(self, browser):

        print("MJ V11: Waiting for", browser, "page...")

        for i in range(1, 9):
            time.sleep(1)

            data = self.observe()
            t = self.text(data)

            if browser == "youtube":
                ready = (
                    "youtube" in t
                    or "youtube.com" in t
                )
            else:
                ready = (
                    "google" in t
                    or "google.com" in t
                )

            print(
                f"MJ V11: PAGE CHECK {i}/8 "
                f"elements={len(data)} ready={ready}"
            )

            if ready:
                return data

        return self.observe()

    def find_relevant_result(self, data, query):

        words = [
            w.lower()
            for w in query.split()
            if len(w) >= 3
        ]

        candidates = []

        for item in data:

            if not isinstance(item, dict):
                continue

            text = str(item.get("text", "")).strip()
            normalized = str(
                item.get("normalized", text)
            ).lower()

            confidence = float(
                item.get("confidence", 0)
            )

            if not text or confidence < 60:
                continue

            score = 0

            for word in words:
                if word in normalized:
                    score += 30

            if query.lower() in normalized:
                score += 60

            if len(normalized) >= 12:
                score += 10

            blocked = {
                "youtube",
                "google",
                "search",
                "home",
                "shorts",
                "history",
                "subscriptions"
            }

            if normalized in blocked:
                continue

            if score > 0:
                candidates.append(
                    (score, item)
                )

        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )

        print(
            "MJ V11: CANDIDATES =",
            len(candidates)
        )

        for score, item in candidates[:10]:
            print(
                " ",
                score,
                "|",
                item.get("text"),
                "| conf=",
                item.get("confidence")
            )

        if candidates:
            return candidates[0][1]

        return None

    def click_result(self, data, query):

        result = self.find_relevant_result(
            data,
            query
        )

        if not result:
            return False, "Relevant result nahi mila."

        x = result.get("center_x")
        y = result.get("center_y")

        if x is None or y is None:
            return False, "Result coordinates nahi mile."

        print(
            "MJ V11: CLICK RESULT =",
            result.get("text"),
            "at",
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
                "Result click kar diya: "
                + str(result.get("text"))
            )

        except Exception as e:
            return False, str(e)

    def verify_change(self, before):

        before_text = self.text(before)

        for i in range(1, 7):

            time.sleep(1)

            after = self.observe()
            after_text = self.text(after)

            changed = (
                after_text[:1500]
                != before_text[:1500]
                or abs(len(after) - len(before)) >= 10
            )

            print(
                f"MJ V11: VERIFY {i}/6 "
                f"changed={changed} "
                f"elements={len(after)}"
            )

            if changed:
                return True

        return False

    def scroll_down(self):

        try:
            self.controller.screen.scroll_down(5)

            return True, (
                "Screen neeche scroll kar di."
            )

        except Exception as e:
            return False, str(e)

    def run(self, goal):

        p = self.parse_goal(goal)

        state = {
            "browser": False,
            "search": False,
            "result": False,
            "scroll": False
        }

        history = []

        print("=" * 70)
        print("MJ V11 SMART AUTONOMOUS BROWSER ENGINE")
        print("=" * 70)

        for step in range(1, self.max_steps + 1):

            print(
                f"\nMJ V11: STEP {step}/{self.max_steps}"
            )

            data = self.observe()

            print(
                "MJ V11: OBSERVED =",
                len(data),
                "elements"
            )

            if p["browser"] and not state["browser"]:
                action = "open_browser"

            elif p["search"] and not state["search"]:
                action = "open_search"

            elif p["result"] and not state["result"]:
                action = "open_result"

            elif p["scroll"] and not state["scroll"]:
                action = "scroll"

            else:
                action = "done"

            print(
                "MJ V11: DECISION =",
                action
            )

            if action == "done":

                print(
                    "MJ V11: VERIFIED GOAL COMPLETE"
                )

                return {
                    "success": True,
                    "goal": goal,
                    "steps": history,
                    "completed": True,
                    "reason": "verified_completed"
                }

            success = False
            result = ""

            if action == "open_browser":

                success, result = (
                    self.open_search_page(
                        p["browser"]
                    )
                )

                if success:
                    state["browser"] = True
                    data = self.wait_for_page(
                        p["browser"]
                    )

            elif action == "open_search":

                success, result = (
                    self.open_search_page(
                        p["browser"],
                        p["query"]
                    )
                )

                if success:
                    state["search"] = True
                    time.sleep(2)

            elif action == "open_result":

                before = data

                success, result = (
                    self.click_result(
                        data,
                        p["query"]
                    )
                )

                if success:

                    verified = self.verify_change(
                        before
                    )

                    if verified:
                        state["result"] = True
                        result += (
                            " | Navigation verified."
                        )
                    else:
                        success = False
                        result = (
                            "Result click hua, "
                            "lekin navigation verify nahi hua."
                        )

            elif action == "scroll":

                success, result = (
                    self.scroll_down()
                )

                if success:
                    state["scroll"] = True

            print(
                "MJ V11: RESULT =",
                result
            )

            history.append({
                "step": step,
                "action": action,
                "result": result,
                "success": success
            })

            if not success:

                return {
                    "success": False,
                    "goal": goal,
                    "steps": history,
                    "completed": False,
                    "reason": "action_failed"
                }

            time.sleep(
                self.observe_delay
            )

        return {
            "success": False,
            "goal": goal,
            "steps": history,
            "completed": False,
            "reason": "max_steps_reached"
        }


def autonomous_screen_agent_v11(
    controller,
    goal,
    max_steps=15,
    observe_delay=1.0
):

    agent = AutonomousV11(
        controller,
        max_steps=max_steps,
        observe_delay=observe_delay
    )

    return agent.run(goal)
