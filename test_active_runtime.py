"""Offline regression tests for the active MJ runtime's safe core paths."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from command_memory import CommandMemory
from autonomous_v25_14 import AutonomousV25
from brain_core import BrainResponse, MJBrain
from executor import ActionExecutor
from intent_engine import IntentEngine
from mj_gemini_brain import MJGeminiBrain
from knowledge import KnowledgeEngine
from mj_knowledge import MJKnowledge
from mj_web import MJWeb
import mj
from planner import PlanStep, TaskPlanner
from screen_ai import ScreenAI
from screen_reader import ScreenReader
from smart_followup import SmartFollowUp
from storage_utils import atomic_write_json
from voice.detector import contains_wake_word, detect_language, remove_wake_word
from voice.speaker import Speaker


class ActiveRuntimeTests(unittest.TestCase):
    def test_browser_false_return_is_not_success(self):
        executor = ActionExecutor()

        with mock.patch(
            "executor.webbrowser.open",
            return_value=False,
        ):
            self.assertEqual(
                executor.open_target("youtube"),
                (
                    "YouTube khol nahi paya.",
                    "hi",
                    False,
                ),
            )

        with mock.patch(
            "executor.webbrowser.open_new_tab",
            return_value=False,
        ):
            self.assertEqual(
                executor.web_search("Tilak Varma"),
                (
                    "Search window khul nahi payi.",
                    "hi",
                    False,
                ),
            )

    def test_failed_screen_command_cannot_learn_successful_variant(self):
        class MemoryStub:
            def __init__(self):
                self.learn_calls = []

            def find_match(self, command, minimum=0.80):
                return {
                    "command": "search Tilak Varma",
                    "score": 0.90,
                }

            def learn_successful_variant(self, *args, **kwargs):
                self.learn_calls.append((args, kwargs))

            def remember(self, *args, **kwargs):
                pass

        class SpeakerStub:
            def speak(self, *args, **kwargs):
                pass

        memory = MemoryStub()
        previous_memory = mj.command_memory
        mj.command_memory = memory

        try:
            with mock.patch.object(
                mj,
                "process_screen_command",
                return_value=(True, False),
            ):
                self.assertTrue(
                    mj.process_command(
                        "search Tilak",
                        object(),
                        SpeakerStub(),
                    )
                )
        finally:
            mj.command_memory = previous_memory

        self.assertEqual(memory.learn_calls, [])

    def test_mj_imports_without_unused_screen_brain(self):
        code = """
import builtins
import importlib

real_import = builtins.__import__

def blocked_import(name, *args, **kwargs):
    if name == "mj_screen_brain":
        raise ModuleNotFoundError("simulated optional module absence")
    return real_import(name, *args, **kwargs)

builtins.__import__ = blocked_import
importlib.import_module("mj")
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )

    def test_wake_word_and_hinglish_detection(self):
        self.assertTrue(contains_wake_word("MJ YouTube kholo"))
        self.assertEqual(
            remove_wake_word("em jay YouTube kholo"),
            "youtube kholo",
        )
        self.assertEqual(detect_language("abhi time kya hai"), "hi")

    def test_intent_to_plan_for_known_application(self):
        intent = IntentEngine().understand("YouTube kholo")
        self.assertEqual(intent.intent, "open_app_or_site")
        self.assertEqual(intent.target, "youtube")
        self.assertGreaterEqual(intent.confidence, 0.75)

        plan = TaskPlanner().build(intent)
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].action, "open_target")
        self.assertEqual(plan[0].data["target"], "youtube")

    def test_intent_routing_avoids_substring_and_missing_query_misroutes(self):
        engine = IntentEngine()

        time_intent = engine.understand("abhi time kya hai")
        self.assertEqual(time_intent.intent, "get_time")

        missing_search = engine.understand("search karo")
        self.assertEqual(missing_search.intent, "web_search")
        self.assertTrue(missing_search.needs_question)
        self.assertEqual(missing_search.query, "")
        self.assertEqual(missing_search.missing, ["query"])

        punctuation_search = engine.understand("search???")
        self.assertEqual(punctuation_search.intent, "web_search")
        self.assertTrue(punctuation_search.needs_question)
        self.assertEqual(punctuation_search.query, "")

        topic_question = engine.understand(
            "Virat Kohli ke baare mein batao"
        )
        self.assertEqual(topic_question.intent, "question")
        self.assertEqual(
            topic_question.query,
            "virat kohli ke baare mein batao",
        )
        self.assertFalse(mj.is_screen_command("search !!!"))

    def test_follow_up_retains_clear_prior_target(self):
        follow_up = SmartFollowUp()
        follow_up.state.update(
            command="Tilak Varma search karo",
            success=True,
        )
        self.assertEqual(follow_up.state.last_target, "tilak varma")
        self.assertEqual(
            follow_up.resolve("isko kholo"),
            "tilak varma kholo",
        )

        # A non-target question should not erase useful navigation context.
        follow_up.state.update(
            command="abhi time kya hai",
            reply="10 baje hain",
            success=True,
        )
        self.assertEqual(follow_up.state.last_target, "tilak varma")

    def test_follow_up_extracts_search_target_without_command_fillers(self):
        follow_up = SmartFollowUp()
        follow_up.state.update(
            command="Google pe Tilak Varma search karo",
            success=True,
        )
        self.assertEqual(follow_up.state.last_target, "tilak varma")
        self.assertEqual(
            follow_up.resolve("isko kholo"),
            "tilak varma kholo",
        )

        empty_search = SmartFollowUp()
        empty_search.state.update(
            command="search karo",
            success=True,
        )
        self.assertEqual(empty_search.state.last_target, "")
        self.assertEqual(
            empty_search.resolve("isko kholo"),
            "isko kholo",
        )

    def test_atomic_json_and_command_memory(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            state_file = root / "state.json"
            memory_file = root / "command_memory.json"

            atomic_write_json(state_file, {"message": "नमस्ते"})
            self.assertEqual(
                json.loads(state_file.read_text(encoding="utf-8")),
                {"message": "नमस्ते"},
            )

            memory = CommandMemory(memory_file)
            memory.remember("open notepad", success=True, result="opened")
            match = memory.find_match("open notepad", minimum=0.9)
            self.assertIsNotNone(match)
            self.assertEqual(match["command"], "open notepad")

    def test_command_memory_ignores_malformed_numeric_fields(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            memory_file = Path(directory) / "command_memory.json"
            memory_file.write_text(
                json.dumps(
                    {
                        "commands": {
                            "open notepad": {
                                "count": "invalid",
                                "success_count": "invalid",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            memory = CommandMemory(memory_file)
            match = memory.find_match("open notepad", minimum=0.9)
            self.assertIsNotNone(match)
            memory.remember("open notepad", success=True)
            self.assertEqual(
                memory.data["commands"]["open notepad"]["count"],
                1,
            )

    def test_web_and_gemini_fail_closed_without_network(self):
        web = MJWeb()
        with self.assertRaises(ValueError):
            web._request("file:///not-an-http-url")
        self.assertEqual(web.fetch_page("file:///not-an-http-url"), "")

        # Empty prompts must never trigger an API request.
        self.assertIsNone(MJGeminiBrain().ask(""))

    def test_knowledge_search_preserves_google_query_prefixes(self):
        knowledge = KnowledgeEngine()
        with mock.patch("knowledge.webbrowser.open") as open_browser:
            result = knowledge.answer(
                "Google par Tilak Varma search karo"
            )

        self.assertEqual(
            result,
            (
                "Google par tilak varma search kar diya.",
                "hi",
            ),
        )
        open_browser.assert_called_once()
        self.assertIn(
            "tilak+varma",
            open_browser.call_args.args[0],
        )

    def test_mj_knowledge_skips_malformed_entries(self):
        knowledge = MJKnowledge.__new__(MJKnowledge)
        knowledge.memories = [
            "malformed",
            {"content": "artificial intelligence", "category": "topic"},
        ]
        knowledge.web_pages = [
            None,
            {
                "title": "Artificial Intelligence",
                "content": "intelligence content",
                "category": "topic",
                "url": "https://example.com",
            },
        ]
        knowledge.conversations = [
            42,
            {
                "user": "AI kya hai",
                "response": "Artificial intelligence",
            },
        ]

        self.assertEqual(
            len(knowledge.search_memory("intelligence")),
            1,
        )
        self.assertEqual(
            len(knowledge.search_web_knowledge("intelligence")),
            1,
        )
        self.assertEqual(
            len(knowledge.search_conversations("intelligence")),
            1,
        )

    def test_screen_reader_fails_closed_on_capture_error(self):
        reader = ScreenReader.__new__(ScreenReader)
        reader.available = True

        class BrokenScreen:
            def capture(self, save=False):
                raise RuntimeError("capture failed")

        self.assertEqual(
            reader.read_screen(BrokenScreen()),
            [],
        )

    def test_screen_ai_rejects_invalid_results_and_tracks_browser_failure(self):
        class Context:
            def __init__(self):
                self.state = type(
                    "State",
                    (),
                    {
                        "page": "unknown",
                        "text": "",
                        "elements": [],
                        "fingerprint": "",
                        "last_action": "",
                        "last_action_success": False,
                    },
                )()

            def observe(self):
                return self.state

            def mark_action(self, action, success):
                self.state.last_action_success = bool(success)

            def describe(self):
                return ""

            def find_text(self, target):
                return None

        class InvalidScreenAgent:
            def process(self, command):
                return {"success": False}

        class IncompleteBrowserAgent:
            def __call__(self, controller, command, max_steps=15):
                return {"success": True, "completed": False}

        screen_ai = ScreenAI.__new__(ScreenAI)
        screen_ai.controller = object()
        screen_ai.screen_agent = InvalidScreenAgent()
        screen_ai.autonomous_agent = IncompleteBrowserAgent()
        screen_ai.max_steps = 1
        screen_ai.context = Context()

        self.assertEqual(
            screen_ai.execute_direct("click target"),
            (
                "Screen agent ka invalid result mila.",
                "hi",
                False,
            ),
        )

        screen_ai.screen_agent = mock.Mock(
            process=mock.Mock(
                return_value=("completed-looking reply", "hi"),
            ),
        )
        self.assertEqual(
            screen_ai.execute_direct("click target"),
            (
                "completed-looking reply",
                "hi",
                False,
            ),
        )

        self.assertEqual(
            screen_ai.execute_browser_goal("search"),
            (
                "Screen par command poori nahi ho payi.",
                "hi",
                False,
            ),
        )
        self.assertFalse(
            screen_ai.context.state.last_action_success
        )

    def test_autonomous_browser_rejects_unknown_target(self):
        agent = AutonomousV25(object(), max_steps=1)

        with mock.patch("autonomous_v25_14.webbrowser.open") as open_browser:
            result = agent.open_browser("not-a-supported-browser")

        self.assertEqual(
            result,
            (
                False,
                "Unsupported browser target: not-a-supported-browser",
            ),
        )
        open_browser.assert_not_called()

    def test_missing_search_query_reaches_brain_not_screen_router(self):
        self.assertFalse(mj.is_screen_command("search karo"))

        class SpeakerStub:
            def __init__(self):
                self.calls = []

            def speak(self, text, language="hi"):
                self.calls.append((text, language))

        class BrainStub:
            def __init__(self):
                self.calls = []

            def process(self, command, wake_already_checked=False):
                self.calls.append((command, wake_already_checked))
                return ("Kya search karna hai?", "hi")

        speaker = SpeakerStub()
        brain = BrainStub()

        with mock.patch.object(
            mj,
            "process_screen_command",
        ) as screen_route:
            self.assertTrue(
                mj.process_command(
                    "search karo",
                    brain,
                    speaker,
                )
            )

        screen_route.assert_not_called()
        self.assertEqual(
            brain.calls,
            [("search karo", True)],
        )
        self.assertEqual(
            speaker.calls,
            [("Kya search karna hai?", "hi")],
        )

    def test_brain_response_preserves_executor_success_metadata(self):
        brain = MJBrain.__new__(MJBrain)

        class ExecutorStub:
            def __init__(self, result):
                self.result = result

            def execute(self, step):
                return self.result

        brain.executor = ExecutorStub(
            ("Action failed but reply exists", "hi", False)
        )
        failure = brain._execute_plan(
            [PlanStep("web_search", {"query": "AI"})]
        )

        self.assertIsInstance(failure, BrainResponse)
        self.assertEqual(
            tuple(failure),
            ("Action failed but reply exists", "hi"),
        )
        self.assertFalse(failure.success)

        brain.executor = ExecutorStub(
            ("Action succeeded", "en", True)
        )
        success = brain._execute_plan(
            [PlanStep("web_search", {"query": "AI"})]
        )
        self.assertEqual(tuple(success), ("Action succeeded", "en"))
        self.assertTrue(success.success)

    def test_legacy_open_preserves_executor_success_metadata(self):
        brain = MJBrain.__new__(MJBrain)
        brain.executor = mock.Mock()
        brain.executor.open_target.return_value = (
            "Application open nahi ho paya.",
            "hi",
            False,
        )

        result = brain._legacy_open("notepad")

        self.assertEqual(
            tuple(result),
            ("Application open nahi ho paya.", "hi"),
        )
        self.assertFalse(result.success)

    def test_failed_brain_screen_command_preserves_failure_metadata(self):
        class ScreenAgentStub:
            def process(self, text):
                return ("Screen action failed", "hi", False)

        brain = MJBrain.__new__(MJBrain)
        brain.screen_agent = ScreenAgentStub()
        brain.state = mock.Mock()
        brain.state.pending = {}
        brain.remembered = []
        brain._remember_command = brain.remembered.append

        response = brain.process(
            "click karo",
            wake_already_checked=True,
        )

        self.assertEqual(
            tuple(response),
            ("Screen action failed", "hi"),
        )
        self.assertFalse(response.success)
        self.assertEqual(brain.remembered, [])

    def test_failed_two_value_brain_response_is_not_recorded_as_success(self):
        class SpeakerStub:
            def speak(self, text, language="hi"):
                return None

        class BrainStub:
            def process(self, command, wake_already_checked=False):
                return BrainResponse(
                    "Action failed",
                    "hi",
                    False,
                )

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            memory = CommandMemory(
                Path(directory) / "command_memory.json"
            )
            follow_up = SmartFollowUp()
            old = (
                mj.is_screen_command,
                mj.smart_followup,
                mj.command_memory,
            )
            mj.is_screen_command = lambda command: False
            mj.smart_followup = follow_up
            mj.command_memory = memory

            try:
                self.assertTrue(
                    mj.process_command(
                        "failed action",
                        BrainStub(),
                        SpeakerStub(),
                    )
                )
            finally:
                (
                    mj.is_screen_command,
                    mj.smart_followup,
                    mj.command_memory,
                ) = old

            self.assertFalse(follow_up.state.last_success)
            self.assertEqual(
                memory.get("failed action")["success_count"],
                0,
            )

    def test_two_value_brain_response_stays_unpackable(self):
        response = BrainResponse(
            "English response",
            "en",
            True,
        )
        reply, language = response
        self.assertEqual(
            (reply, language),
            ("English response", "en"),
        )

    def test_speaker_fails_closed_without_audio_device(self):
        with mock.patch("pygame.mixer.init", side_effect=RuntimeError("no audio")):
            speaker = Speaker()
            self.assertFalse(speaker.mixer_ready)
            speaker.speak("hello world")

    def test_listener_fails_closed_without_model(self):
        listener = object.__new__(type("ListenerStub", (), {}) )
        listener.model = None
        self.assertEqual(listener.__class__.__dict__.get("transcribe", None), None)

        # Use the real implementation through the class method.
        ListenerClass = __import__("voice.listener", fromlist=["VoiceListener"]).VoiceListener
        listener = ListenerClass.__new__(ListenerClass)
        listener.model = None
        self.assertEqual(listener.transcribe([0.0, 0.1], purpose="wake"), "")

    def test_low_confidence_command_is_discarded_when_retry_is_empty(self):
        class ListenerStub:
            def __init__(self):
                self.calls = 0

            def listen_until_silence(self, context_text=""):
                self.calls += 1
                return "fun google." if self.calls == 1 else ""

        class SpeakerStub:
            def speak(self, *args, **kwargs):
                pass

        listener = ListenerStub()
        with mock.patch.object(mj, "speak_reply"), mock.patch.object(
            mj.time,
            "sleep",
        ):
            command = mj.get_command_after_wake(
                "MJ",
                listener,
                SpeakerStub(),
            )

        self.assertEqual(command, "")
        self.assertEqual(listener.calls, 2)

    def test_low_confidence_direct_browser_like_command_is_discarded(self):
        class SpeakerStub:
            def speak(self, *args, **kwargs):
                pass

        with mock.patch.object(
            mj,
            "process_screen_command",
        ) as process_screen:
            command = mj.get_command_after_wake(
                "MJ fun google.",
                object(),
                SpeakerStub(),
            )

        self.assertEqual(command, "")
        process_screen.assert_not_called()

    def test_low_confidence_app_like_follow_up_is_discarded(self):
        class ListenerStub:
            def listen_until_silence(self, context_text=""):
                return "fun notepad."

        self.assertEqual(
            mj.listen_follow_up(ListenerStub()),
            "",
        )

    def test_valid_hinglish_command_still_passes_voice_gate(self):
        class ListenerStub:
            def listen_until_silence(self, context_text=""):
                return "abhi time kya hai"

        self.assertEqual(
            mj.listen_follow_up(ListenerStub()),
            "abhi time kya hai",
        )


if __name__ == "__main__":
    unittest.main()
