MJ PART 8 — INTEGRATED BRAIN

This part connects:
    IntentEngine
    TaskPlanner
    ActionExecutor
    KnowledgeEngine
    ConversationState
    Memory

Flow:
    voice text
      -> understand
      -> plan
      -> execute
      -> knowledge fallback
      -> response

IMPORTANT:
BACK UP your current MJVOICE folder first.

Then replace ONLY:
    brain.py

Do NOT replace:
    voice/listener.py
    voice/speaker.py
    mj.py
    config.py

Required files already present from previous parts:
    intent_engine.py
    planner.py
    executor.py
    knowledge.py
    conversation.py
    memory.py

Run:
    python .\mj.py

Test:
    MJ
    YouTube kholo

    MJ
    Google par Rohit Sharma search karo

    MJ
    Abhi time kitna hai

    MJ
    Mere laptop ki info

The new brain keeps a legacy fallback so older working commands
continue to work while the new architecture is being expanded.
