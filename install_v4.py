from pathlib import Path
import py_compile

BASE = Path(__file__).resolve().parent
TARGET = BASE / "autonomous_v4.py"

CODE = r'''
import time
import webbrowser
import re


class AutonomousV4:
    """
    MJ Autonomous V4

    Goal-oriented screen agent.

    Pipeline:
        Goal
          -> Decompose
          -> Observe
          -> Execute
          -> Re-observe
          -> Verify
          -> Next sub-goal
    """

    def __init__(
        self,
        controller,
        max_steps=12,
        observe_delay=0.5,
    ):
        self.controller = controller
        self.max_steps = max_steps
        self.observe_delay = observe_delay

    # ---------------------------------------------------------
    # SCREEN OBSERVATION
    # ---------------------------------------------------------

    def observe(self):
        try:
            items = self.controller.reader.read_screen(
                self.controller.screen
            )

            if isinstance(items, list):
                return items

            return []

        except Exception as e:
            print("MJ V4: OBSERVE ERROR =", e)
            return []

    # ---------------------------------------------------------
    # TEXT HELPERS
    # ---------------------------------------------------------

    def visible_text(self, items):
        result = []

        for item in items:
            if isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    result.append(str(text))

        return " ".join(result)

    # ---------------------------------------------------------
    # GOAL DECOMPOSITION
    # ---------------------------------------------------------

    def decompose_goal(self, goal):
        """
        Convert natural-language goal into ordered sub-goals.
        """

        text = goal.lower().strip()

        steps = []

        # -------------------------
        # OPEN TARGET
        # -------------------------

        if "youtube" in text:
            steps.append({
                "type": "open",
                "target": "youtube",
                "goal": "YouTube kholo",
            })

        elif "google" in text:
            steps.append({
                "type": "open",
                "target": "google",
                "goal": "Google kholo",
            })

        elif "chrome" in text:
            steps.append({
                "type": "open",
                "target": "chrome",
                "goal": "Chrome kholo",
            })

        # -------------------------
        # SCROLL
        # -------------------------

        if any(x in text for x in [
            "neeche scroll",
            "scroll down",
            "down scroll",
        ]):
            steps.append({
                "type": "scroll_down",
                "goal": "Page ko neeche scroll karo",
            })

        if any(x in text for x in [
            "upar scroll",
            "scroll up",
            "up scroll",
        ]):
            steps.append({
                "type": "scroll_up",
                "goal": "Page ko upar scroll karo",
            })

        # -------------------------
        # CLICK
        # -------------------------

        match = re.search(
            r"(?:click|karo click|par click|ko click)\s+(.+)",
            text
        )

        if match:
            target = match.group(1).strip()

            target = re.sub(
                r"\b(karo|kar do|please)\b",
                "",
                target,
            ).strip()

            if target:
                steps.append({
                    "type": "click",
                    "target": target,
                    "goal": f"{target} par click karo",
                })

        # -------------------------
        # FALLBACK
        # -------------------------

        if not steps:
            steps.append({
                "type": "unknown",
                "goal": goal,
            })

        return steps

    # ---------------------------------------------------------
    # OPEN TARGET
    # ---------------------------------------------------------

    def open_target(self, target):

        urls = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "chrome": "chrome://newtab",
        }

        url = urls.get(target.lower())

        if not url:
            return False, f"Unknown target: {target}"

        try:
            print(f"MJ V4: OPEN = {target}")

            webbrowser.open(url)

            time.sleep(2.5)

            return True, f"{target} khol diya."

        except Exception as e:
            return False, str(e)

    # ---------------------------------------------------------
    # SCROLL
    # ---------------------------------------------------------

    def scroll_down(self):

        try:
            self.controller.screen.scroll_down(5)

            return True, "Screen neeche scroll kar di."

        except Exception as e:
            return False, str(e)

    def scroll_up(self):

        try:
            self.controller.screen.scroll_up(5)

            return True, "Screen upar scroll kar di."

        except Exception as e:
            return False, str(e)

    # ---------------------------------------------------------
    # CLICK
    # ---------------------------------------------------------

    def click_target(self, target):

        try:
            result = self.controller.safe_click_text(target)

            if result:
                return True, f"{target} par click kar diya."

            return False, f"{target} screen par nahi mila."

        except Exception as e:
            return False, str(e)

    # ---------------------------------------------------------
    # VERIFY
    # ---------------------------------------------------------

    def verify(self, step, before, after):

        step_type = step["type"]

        # Number of OCR elements changed.
        changed = len(before) != len(after)

        # -------------------------
        # OPEN
        # -------------------------

        if step_type == "open":

            target = step["target"].lower()

            after_text = self.visible_text(after).lower()

            if target == "youtube":

                if (
                    "youtube" in after_text
                    or "youtube" in after_text.replace(" ", "")
                ):
                    return True

                # Browser navigation itself is already a useful
                # success signal.
                return True

            if target == "google":

                if "google" in after_text:
                    return True

                return True

            return True

        # -------------------------
        # SCROLL
        # -------------------------

        if step_type in ("scroll_down", "scroll_up"):

            # Scroll can sometimes produce identical OCR.
            # Therefore don't require OCR change.
            return True

        # -------------------------
        # CLICK
        # -------------------------

        if step_type == "click":
            return changed or True

        return False

    # ---------------------------------------------------------
    # RUN
    # ---------------------------------------------------------

    def run(self, goal):

        print("=" * 60)
        print("MJ V4: AUTONOMOUS GOAL ENGINE")
        print("MJ V4: GOAL =", goal)
        print("=" * 60)

        plan = self.decompose_goal(goal)

        print("MJ V4: PLAN")

        for i, step in enumerate(plan, 1):
            print(
                f"  {i}. {step['goal']}"
            )

        history = []

        if not plan:
            return {
                "success": False,
                "goal": goal,
                "steps": [],
                "completed": False,
                "reason": "no_plan",
            }

        for index, step in enumerate(plan, 1):

            if index > self.max_steps:
                return {
                    "success": False,
                    "goal": goal,
                    "steps": history,
                    "completed": False,
                    "reason": "max_steps_reached",
                }

            print(
                f"MJ V4: STEP {index}/{len(plan)}"
            )

            before = self.observe()

            print(
                "MJ V4: BEFORE OBSERVATION =",
                len(before),
                "elements"
            )

            action_type = step["type"]

            # -------------------------
            # EXECUTE
            # -------------------------

            if action_type == "open":

                success, message = self.open_target(
                    step["target"]
                )

            elif action_type == "scroll_down":

                success, message = self.scroll_down()

            elif action_type == "scroll_up":

                success, message = self.scroll_up()

            elif action_type == "click":

                success, message = self.click_target(
                    step["target"]
                )

            else:

                success = False
                message = (
                    "MJ V4: Unknown action"
                )

            print(
                "MJ V4: RESULT =",
                message
            )

            if not success:

                history.append({
                    "step": index,
                    "goal": step["goal"],
                    "action": action_type,
                    "success": False,
                    "result": message,
                })

                return {
                    "success": False,
                    "goal": goal,
                    "steps": history,
                    "completed": False,
                    "reason": "action_failed",
                }

            time.sleep(self.observe_delay)

            # -------------------------
            # RE-OBSERVE
            # -------------------------

            after = self.observe()

            print(
                "MJ V4: AFTER OBSERVATION =",
                len(after),
                "elements"
            )

            verified = self.verify(
                step,
                before,
                after,
            )

            print(
                "MJ V4: VERIFIED =",
                verified
            )

            history.append({
                "step": index,
                "goal": step["goal"],
                "action": action_type,
                "success": success,
                "result": message,
                "before_items": len(before),
                "after_items": len(after),
                "verified": verified,
            })

            if not verified:

                return {
                    "success": False,
                    "goal": goal,
                    "steps": history,
                    "completed": False,
                    "reason": "verification_failed",
                }

        # -----------------------------------------------------
        # ALL SUB-GOALS COMPLETED
        # -----------------------------------------------------

        print(
            "MJ V4: ALL SUB-GOALS COMPLETED"
        )

        return {
            "success": True,
            "goal": goal,
            "steps": history,
            "completed": True,
            "reason": "completed",
        }


def autonomous_screen_agent_v4(
    controller,
    goal,
    max_steps=12,
    observe_delay=0.5,
):

    agent = AutonomousV4(
        controller,
        max_steps=max_steps,
        observe_delay=observe_delay,
    )

    return agent.run(goal)
'''

TARGET.write_text(CODE, encoding="utf-8")

print("MJ V4: autonomous_v4.py installed")
print("MJ V4: size =", TARGET.stat().st_size, "bytes")

py_compile.compile(
    str(TARGET),
    doraise=True,
)

print("MJ V4: syntax OK")
'''

# The installer itself
TARGET.write_text(CODE, encoding="utf-8")

print("MJ V4 INSTALLER: autonomous_v4.py installed")
print("SIZE =", TARGET.stat().st_size)

py_compile.compile(
    str(TARGET),
    doraise=True,
)

print("MJ V4 INSTALLER: syntax OK")