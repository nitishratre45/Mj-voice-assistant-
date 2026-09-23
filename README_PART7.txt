MJ PART 7 — BRAIN -> PLANNER -> EXECUTOR

NEW:
    executor.py

This is the first connection layer for Part 6.

Flow:
    Voice
      -> IntentEngine
      -> TaskPlanner
      -> BrainExecutor
      -> ActionExecutor
      -> Result

IMPORTANT:
This part does NOT replace your working mj.py/listener.py.
It provides the executor/orchestration layer first.

To connect it to the existing brain in the next integration step,
MJBrain can instantiate:
    IntentEngine
    TaskPlanner
    ActionExecutor
    BrainExecutor

Then process(text) can delegate suitable requests through it.

Testable examples after integration:
    YouTube kholo
    Google kholo
    Chrome kholo
    Notepad kholo
    Google par Rohit Sharma search karo
    Abhi time kya hai

Part 7 intentionally keeps the executor transparent and safe.
No arbitrary shell command execution is allowed from voice text.
