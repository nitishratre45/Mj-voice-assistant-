MJ PART 9 — CONTEXT + CLARIFICATION

NEW:
    context_engine.py
    question_handler.py

Goal:
MJ should not blindly guess when a request is incomplete.

Example:

User:
    MJ, Hyderabad jaana hai.

MJ:
    Kab jaana hai?

User:
    Kal.

MJ:
    Train, flight ya bus se jaana hai?

User:
    Train se.

MJ:
    Theek hai, details mil gayi:
    destination=Hyderabad, date=tomorrow, mode=train.

The context engine stores short-lived task slots:
    destination
    date
    travel_mode

IMPORTANT:
Do not replace the working listener.py or mj.py yet.
Do not remove previous parts.

Part 10 can connect this clarification layer to the
integrated MJBrain so pending questions and answers flow
through the normal voice loop.
