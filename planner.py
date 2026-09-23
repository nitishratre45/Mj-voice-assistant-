from dataclasses import dataclass, field
from typing import List


@dataclass
class PlanStep:
    action: str
    data: dict = field(default_factory=dict)
    description: str = ""


class TaskPlanner:
    """
    MJ Task Planner

    Converts an understood intent into executable steps.
    """

    def build(self, intent):

        steps: List[PlanStep] = []

        # =====================================================
        # OPEN SINGLE TARGET
        # =====================================================

        if intent.intent == "open_app_or_site":

            steps.append(
                PlanStep(
                    action="open_target",
                    data={
                        "target": intent.target
                    },
                    description=(
                        f"Open {intent.target}"
                    ),
                )
            )

        # =====================================================
        # OPEN MULTIPLE TARGETS
        # =====================================================

        elif intent.intent == "open_multiple":

            targets = getattr(
                intent,
                "targets",
                [],
            )

            if not targets and intent.target:
                targets = [
                    intent.target
                ]

            for target in targets:

                steps.append(
                    PlanStep(
                        action="open_target",
                        data={
                            "target": target
                        },
                        description=(
                            f"Open {target}"
                        ),
                    )
                )

        # =====================================================
        # WEB SEARCH
        # =====================================================

        elif intent.intent == "web_search":

            if intent.needs_question:

                steps.append(
                    PlanStep(
                        action="ask_user",
                        data={
                            "missing": intent.missing
                        },
                        description=(
                            "Ask what to search"
                        ),
                    )
                )

            else:

                steps.append(
                    PlanStep(
                        action="web_search",
                        data={
                            "query": intent.query
                        },
                        description=(
                            f"Search for "
                            f"{intent.query}"
                        ),
                    )
                )

        # =====================================================
        # SCREEN ACTION
        # =====================================================

        elif intent.intent == "screen_action":

            action = (
                intent.entities.get(
                    "action",
                    ""
                )
                if getattr(
                    intent,
                    "entities",
                    None,
                )
                else ""
            )

            # -----------------------------------------------
            # CLICK
            # -----------------------------------------------

            if action == "click":

                target = (
                    intent.entities.get(
                        "screen_target",
                        intent.target,
                    )
                )

                if target:

                    steps.append(
                        PlanStep(
                            action="screen_action",
                            data={
                                "action": "click",
                                "target": target,
                            },
                            description=(
                                f"Click "
                                f"{target}"
                            ),
                        )
                    )

                else:

                    steps.append(
                        PlanStep(
                            action="screen_action",
                            data={
                                "action": "click",
                            },
                            description=(
                                "Click a screen target"
                            ),
                        )
                    )

            # -----------------------------------------------
            # DOUBLE CLICK
            # -----------------------------------------------

            elif action == "double_click":

                target = (
                    intent.entities.get(
                        "screen_target",
                        intent.target,
                    )
                )

                steps.append(
                    PlanStep(
                        action="screen_action",
                        data={
                            "action": "double_click",
                            "target": target,
                        },
                        description=(
                            f"Double click "
                            f"{target}"
                        ),
                    )
                )

            # -----------------------------------------------
            # RIGHT CLICK
            # -----------------------------------------------

            elif action == "right_click":

                target = (
                    intent.entities.get(
                        "screen_target",
                        intent.target,
                    )
                )

                steps.append(
                    PlanStep(
                        action="screen_action",
                        data={
                            "action": "right_click",
                            "target": target,
                        },
                        description=(
                            f"Right click "
                            f"{target}"
                        ),
                    )
                )

            # -----------------------------------------------
            # SCROLL UP
            # -----------------------------------------------

            elif action == "scroll_up":

                steps.append(
                    PlanStep(
                        action="screen_action",
                        data={
                            "action": "scroll_up",
                        },
                        description=(
                            "Scroll screen up"
                        ),
                    )
                )

            # -----------------------------------------------
            # SCROLL DOWN
            # -----------------------------------------------

            elif action == "scroll_down":

                steps.append(
                    PlanStep(
                        action="screen_action",
                        data={
                            "action": "scroll_down",
                        },
                        description=(
                            "Scroll screen down"
                        ),
                    )
                )

            # -----------------------------------------------
            # PRESS KEY
            # -----------------------------------------------

            elif action == "press":

                key = (
                    intent.entities.get(
                        "key",
                        "",
                    )
                )

                steps.append(
                    PlanStep(
                        action="screen_action",
                        data={
                            "action": "press",
                            "key": key,
                        },
                        description=(
                            f"Press {key}"
                        ),
                    )
                )

            # -----------------------------------------------
            # HOTKEY
            # -----------------------------------------------

            elif action == "hotkey":

                modifier = (
                    intent.entities.get(
                        "modifier",
                        "",
                    )
                )

                key = (
                    intent.entities.get(
                        "key",
                        "",
                    )
                )

                steps.append(
                    PlanStep(
                        action="screen_action",
                        data={
                            "action": "hotkey",
                            "modifier": modifier,
                            "key": key,
                        },
                        description=(
                            f"Press "
                            f"{modifier}+{key}"
                        ),
                    )
                )

            # -----------------------------------------------
            # CLICK + TYPE
            # -----------------------------------------------

            elif action == "click_and_type":

                target = (
                    intent.entities.get(
                        "screen_target",
                        intent.target,
                    )
                )

                text = (
                    intent.entities.get(
                        "text",
                        "",
                    )
                )

                steps.append(
                    PlanStep(
                        action="screen_action",
                        data={
                            "action": "click_and_type",
                            "target": target,
                            "text": text,
                        },
                        description=(
                            f"Click {target} "
                            f"and type {text}"
                        ),
                    )
                )

            # -----------------------------------------------
            # UNKNOWN SCREEN ACTION
            # -----------------------------------------------

            else:

                steps.append(
                    PlanStep(
                        action="unknown",
                        data={
                            "query": intent.query
                        },
                        description=(
                            "Unknown screen action"
                        ),
                    )
                )

        # =====================================================
        # SCREENSHOT
        # =====================================================

        elif intent.intent == "screenshot":

            steps.append(
                PlanStep(
                    action="screenshot",
                    description=(
                        "Take a screenshot"
                    ),
                )
            )

        # =====================================================
        # VOLUME UP
        # =====================================================

        elif intent.intent == "volume_up":

            steps.append(
                PlanStep(
                    action="volume_up",
                    description=(
                        "Increase system volume"
                    ),
                )
            )

        # =====================================================
        # VOLUME DOWN
        # =====================================================

        elif intent.intent == "volume_down":

            steps.append(
                PlanStep(
                    action="volume_down",
                    description=(
                        "Decrease system volume"
                    ),
                )
            )

        # =====================================================
        # MUTE
        # =====================================================

        elif intent.intent == "mute":

            steps.append(
                PlanStep(
                    action="mute",
                    description=(
                        "Mute system audio"
                    ),
                )
            )

        # =====================================================
        # SHOW DESKTOP
        # =====================================================

        elif intent.intent == "show_desktop":

            steps.append(
                PlanStep(
                    action="show_desktop",
                    description=(
                        "Show desktop"
                    ),
                )
            )

        # =====================================================
        # LOCK COMPUTER
        # =====================================================

        elif intent.intent == "lock_computer":

            steps.append(
                PlanStep(
                    action="lock_computer",
                    description=(
                        "Lock computer"
                    ),
                )
            )

        # =====================================================
        # TIME
        # =====================================================

        elif intent.intent == "get_time":

            steps.append(
                PlanStep(
                    action="answer_time",
                    description=(
                        "Get current time"
                    ),
                )
            )

        # =====================================================
        # DATE
        # =====================================================

        elif intent.intent == "get_date":

            steps.append(
                PlanStep(
                    action="answer_date",
                    description=(
                        "Get current date"
                    ),
                )
            )

        # =====================================================
        # SYSTEM INFO
        # =====================================================

        elif intent.intent == "system_info":

            steps.append(
                PlanStep(
                    action="system_info",
                    description=(
                        "Get computer information"
                    ),
                )
            )

        # =====================================================
        # QUESTION
        # =====================================================

        elif intent.intent == "question":

            steps.append(
                PlanStep(
                    action="answer_question",
                    data={
                        "query": intent.query
                    },
                    description=(
                        "Answer the user's question"
                    ),
                )
            )

        # =====================================================
        # CONVERSATION
        # =====================================================

        elif intent.intent == "conversation":

            steps.append(
                PlanStep(
                    action="conversation",
                    data={
                        "query": intent.query
                    },
                    description=(
                        "Continue conversation"
                    ),
                )
            )

        # =====================================================
        # UNKNOWN
        # =====================================================

        else:

            steps.append(
                PlanStep(
                    action="unknown",
                    data={
                        "query": intent.query
                    },
                    description=(
                        "Unknown request"
                    ),
                )
            )

        return steps