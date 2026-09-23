import time

from config import STARTUP_GREETING, WAKE_REPLY

from voice.detector import (
    contains_wake_word,
    detect_language,
    remove_wake_word,
)

from voice.listener import VoiceListener
from voice.speaker import Speaker

# IMPORTANT:
# MJBrain ONLY comes from brain_core.py.
# Do NOT import MJBrain from brain.py.
from brain_core import MJBrain
from mj_screen_brain import MJScreenBrain

# MJ screen/browser control engine.
# V25.14 is the current verified browser/screen checkpoint.
try:
    from screen_controller import ScreenController
    from screen_agent import ScreenAgent
    from mj_screen_integration import MJScreenIntegration
    from autonomous_v25_14 import autonomous_screen_agent_v25
except Exception as exc:
    ScreenController = None
    autonomous_screen_agent_v25 = None
    print("MJ: Screen engine unavailable:", exc)


# ============================================================
# SETTINGS
# ============================================================

FOLLOW_UP_SECONDS = 8.0

# Small delay after TTS so MJ doesn't immediately hear itself.
TTS_SETTLE_SECONDS = 0.75

# Number of retries when MJ hears nothing after wake.
COMMAND_RETRIES = 2

# Maximum autonomous screen actions for one voice command.
SCREEN_MAX_STEPS = 15


# ============================================================
# SPEAKER
# ============================================================

def speak_reply(
    speaker,
    reply,
    language="hi",
):
    """
    Safely speak MJ's reply.
    """

    reply = (
        reply or ""
    ).strip()

    if not reply:
        return

    try:

        speaker.speak(
            reply,
            language or "hi",
        )

    except Exception as exc:

        print(
            f"MJ: Speaker error: {exc}"
        )


# ============================================================
# SCREEN / BROWSER COMMAND ROUTING
# ============================================================

def is_screen_command(command):
    text = (command or "").strip().lower()

    screen_words = (
        "youtube",
        "google",
        "chrome",
        "browser",
        "website",
        "search karo",
        "search kar",
        "khol",
        "kholo",
        "open karo",
        "open kar",
        "click karo",
        "click kar",
        "scroll",
        "video chalao",
        "video chala",
        "play karo",
        "play kar",

        "search",
        "dhundo",
        "dhoondo",
        "find",
        "khojo",
         "talash",
         "video kholo",
         "video khol",
         "play",
    )

    return any(word in text for word in screen_words)


def process_screen_command(
    command,
    speaker,
    screen_brain=None,
):
    if (
        ScreenController is None
        or autonomous_screen_agent_v25 is None
    ):
        print("MJ: Screen engine is not available.")
        speak_reply(
            speaker,
            "Screen control abhi available nahi hai.",
            "hi",
        )
        return False

    print()
    print("MJ SCREEN COMMAND:", command)

    try:
        controller = ScreenController()

        try:
            screen_agent = ScreenAgent()
        except Exception as exc:
            print(
                "MJ: ScreenAgent initialization failed:",
                exc,
            )
            screen_agent = None

        integration = MJScreenIntegration(
            controller=controller,
            screen_agent=screen_agent,
            autonomous_agent=autonomous_screen_agent_v25,
            max_steps=SCREEN_MAX_STEPS,
        )

        print(
            "MJ SCREEN CONTEXT BEFORE:",
            integration.context()[:1800],
        )

        result = integration.command(command)

        print("MJ SCREEN RESULT:", result)

        if isinstance(result, dict):
            success = bool(result.get("success"))
            reply = result.get("reply") or (
                "Ho gaya." if success
                else "Command screen par poori nahi ho payi."
            )

            speak_reply(
                speaker,
                reply,
                result.get("language", "hi"),
            )

            print(
                "MJ SCREEN CONTEXT AFTER:",
                integration.context()[:1800],
            )

            return True

        speak_reply(
            speaker,
            "Screen command ka result samajh nahi aaya.",
            "hi",
        )
        return True

    except Exception as exc:
        print("MJ: Screen integration error:", exc)

        speak_reply(
            speaker,
            "Screen control mein error aaya.",
            "hi",
        )

        return True


# ============================================================
# PROCESS COMMAND
# ============================================================

def process_command(
    command,
    brain,
    speaker,
):
    """
    Send a command to MJBrain.

    Returns:
        True  = command was processed
        False = empty command
    """

    command = (
        command or ""
    ).strip()

    if not command:
        return False

    print()
    print(
        "MJ COMMAND:",
        command,
    )

    # Browser/screen commands are handled directly by MJ's
    # verified screen engine. Other commands go to MJBrain.
    if is_screen_command(command):
        if process_screen_command(command, speaker):
            return True

    try:

        result = brain.process(
            command
        )

    except Exception as exc:

        print(
            "MJ: Brain error:",
            exc,
        )

        speak_reply(
            speaker,
            "Command process karte waqt problem aayi.",
            "hi",
        )

        return True

    # --------------------------------------------------------
    # Validate Brain response
    # --------------------------------------------------------

    if (
        not result
        or not isinstance(result, tuple)
        or len(result) < 2
    ):
        

        print(
            "MJ: Brain returned invalid response."
        )

        speak_reply(
            speaker,
            "Abhi mujhe samajh me nahi aayi.",
            detect_language(command),
        )

        return True

    reply, language = result

    # --------------------------------------------------------
    # Normal reply
    # --------------------------------------------------------

    if reply:

        speak_reply(
            speaker,
            reply,
            language or "hi",
        )

    else:

        speak_reply(
            speaker,
            "Abhi mujhe samajh nahi aaya.",
            language or detect_language(command),
        )

    return True


# ============================================================
# FOLLOW-UP LISTENING
# ============================================================

def listen_follow_up(
    listener,
):
    """
    Listen for another command after the previous command.

    User can say:

        MJ
        YouTube kholo

        Google kholo
        Notepad kholo
        Calculator kholo

    without repeating MJ.

    Returns:
        command string
        or empty string on timeout
    """

    print()

    print(
        f"MJ: Follow-up listening... "
        f"({FOLLOW_UP_SECONDS:.0f}s)"
    )

    start = time.monotonic()

    while True:

        elapsed = (
            time.monotonic()
            - start
        )

        if elapsed >= FOLLOW_UP_SECONDS:
            break

        try:

            command = (
                listener.listen_until_silence()
            )

        except Exception as exc:

            print(
                "MJ: Follow-up listener error:",
                exc,
            )

            break

        if command:

            command = (
                command.strip()
            )

            if command:

                return command

    print(
        "MJ: Follow-up timeout. Wake mode."
    )

    return ""


# ============================================================
# GET COMMAND AFTER WAKE
# ============================================================

def get_command_after_wake(
    heard,
    listener,
    speaker,
):
    """
    Handles:

        MJ YouTube kholo

    and:

        MJ
        YouTube kholo
    """

    heard = (
        heard or ""
    ).strip()

    if not heard:
        return ""

    # --------------------------------------------------------
    # Remove wake word.
    # --------------------------------------------------------

    direct_command = (
        remove_wake_word(
            heard
        )
    )

    direct_command = (
        direct_command or ""
    ).strip()

    # --------------------------------------------------------
    # Direct command:
    #
    # "MJ YouTube kholo"
    # --------------------------------------------------------

    if direct_command:

        print(
            "MJ DIRECT COMMAND:",
            direct_command,
        )

        return direct_command

    # --------------------------------------------------------
    # Wake only:
    #
    # "MJ"
    # --------------------------------------------------------

    speak_reply(
        speaker,
        WAKE_REPLY,
        "hi",
    )

    time.sleep(
        TTS_SETTLE_SECONDS
    )

    # --------------------------------------------------------
    # First attempt
    # --------------------------------------------------------

    for attempt in range(
        COMMAND_RETRIES
    ):

        try:

            command = (
                listener
                .listen_until_silence()
            )

        except Exception as exc:

            print(
                "MJ: Command listener error:",
                exc,
            )

            command = ""

        if command:

            command = (
                command.strip()
            )

            if command:

                return command

        # ----------------------------------------------------
        # Retry
        # ----------------------------------------------------

        if attempt == 0:

            print(
                "MJ: Command not heard. Retrying..."
            )

            speak_reply(
                speaker,
                "Hmm, dobara bolo.",
                "hi",
            )

            time.sleep(
                TTS_SETTLE_SECONDS
            )

    return ""


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 60
    )

    print(
        "                 MJ - SMART ASSISTANT"
    )

    print(
        "           CONTINUOUS VOICE + BRAIN ENGINE"
    )

    print(
        "=" * 60
    )

    listener = None
    speaker = None
    brain = None

    # ========================================================
    # INITIALIZATION
    # ========================================================

    try:

        print(
            "MJ: Initializing..."
        )

        listener = VoiceListener()

        speaker = Speaker()

        # IMPORTANT:
        # brain_core.MJBrain is the main brain.
        brain = MJBrain()

    except Exception as exc:

        print()
        print(
            "MJ: Startup error:",
            exc,
        )

        # Speaker may not exist yet.
        if speaker is not None:

            try:

                speak_reply(
                    speaker,
                    "MJ start nahi ho paya.",
                    "hi",
                )

            except Exception:
                pass

        return

    # ========================================================
    # MAIN RUNTIME
    # ========================================================

    try:

        # ----------------------------------------------------
        # STARTUP GREETING
        # ----------------------------------------------------

        speak_reply(
            speaker,
            STARTUP_GREETING,
            detect_language(
                STARTUP_GREETING
            ),
        )

        time.sleep(
            TTS_SETTLE_SECONDS
        )

        print()

        print(
            "MJ: Brain ready."
        )

        print(
            "MJ: Hindi + English + Hinglish supported."
        )

        print(
            "MJ: Say 'MJ' to wake me."
        )

        print(
            f"MJ: After a command, "
            f"I'll listen for another command "
            f"for {FOLLOW_UP_SECONDS:.0f} seconds."
        )

        print()

        # ====================================================
        # CONTINUOUS LOOP
        # ====================================================

        while True:

            # =================================================
            # WAKE MODE
            # =================================================

            try:

                heard = (
                    listener.listen_for_wake()
                )

            except Exception as exc:

                print(
                    "MJ: Wake listener error:",
                    exc,
                )

                time.sleep(
                    0.5
                )

                continue

            if not heard:

                continue

            heard = (
                heard.strip()
            )

            if not heard:

                continue

            print(
                "MJ WAKE HEARD:",
                heard,
            )

            # =================================================
            # CHECK WAKE WORD
            # =================================================

            try:

                wake_detected = (
                    contains_wake_word(
                        heard
                    )
                )

            except Exception as exc:

                print(
                    "MJ: Wake detection error:",
                    exc,
                )

                wake_detected = False

            if not wake_detected:

                continue

            print(
                "MJ: Wake word detected."
            )

            # =================================================
            # GET COMMAND
            # =================================================

            command = (
                get_command_after_wake(
                    heard,
                    listener,
                    speaker,
                )
            )

            if not command:

                print(
                    "MJ: No command received."
                )

                continue

            # =================================================
            # PROCESS FIRST COMMAND
            # =================================================

            processed = (
                process_command(
                    command,
                    brain,
                    speaker,
                )
            )

            if not processed:

                continue

            # =================================================
            # LET TTS FINISH / MICROPHONE SETTLE
            # =================================================

            time.sleep(
                TTS_SETTLE_SECONDS
            )

            # =================================================
            # FOLLOW-UP MODE
            # =================================================

            while True:

                follow_up = (
                    listen_follow_up(
                        listener
                    )
                )

                if not follow_up:

                    break

                processed = (
                    process_command(
                        follow_up,
                        brain,
                        speaker,
                    )
                )

                if not processed:

                    break

                # ------------------------------------------------
                # Important:
                # Give TTS time to finish before recording again.
                # ------------------------------------------------

                time.sleep(
                    TTS_SETTLE_SECONDS
                )

            # =================================================
            # BACK TO WAKE MODE
            # =================================================

            print()
            print(
                "MJ: Back to wake mode."
            )
            print()

    # ========================================================
    # CTRL + C
    # ========================================================

    except KeyboardInterrupt:

        print()
        print(
            "MJ: Stopping..."
        )

    # ========================================================
    # FATAL ERROR
    # ========================================================

    except Exception as exc:

        print()
        print(
            "MJ: Fatal error:",
            exc,
        )

    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        if speaker is not None:

            try:

                speaker.close()

            except Exception as exc:

                print(
                    "MJ: Speaker cleanup error:",
                    exc,
                )

        print(
            "MJ: Assistant stopped."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()