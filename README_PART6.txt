MJ PART 6 — UNDERSTANDING + PLANNING

This part moves MJ away from exact-command matching.

NEW:
    intent_engine.py
    planner.py

Intent examples:
    "YouTube kholo"
    "YouTube open kar do"
    "mere liye YouTube chala do"
    "Google par Rohit Sharma search karo"
    "internet pe Tilak Varma ki latest news dekho"
    "abhi time kya hai"
    "mere laptop ki info batao"

The IntentEngine converts speech into:
    intent + confidence + target/query/entities

The TaskPlanner converts that into:
    one or more transparent steps

IMPORTANT:
Do not replace listener.py or mj.py in this part.
Do not remove your working Part 5 files.

Next part:
Brain/Executor will consume these plans and ask questions
when information is missing, instead of blindly executing.
