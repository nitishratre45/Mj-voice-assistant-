class ConversationState:
    """
    MJ conversation state.

    Stores:
    - pending confirmation
    - last target
    - last action
    """

    def __init__(self):
        self.pending = None
        self.last_target = None
        self.last_action = None

    def ask(self, question, intent, data=None):
        self.pending = {
            "intent": intent,
            "data": data or {},
        }
        return question

    def clear(self):
        self.pending = None

    def remember(self, target=None, action=None):
        if target:
            self.last_target = target

        if action:
            self.last_action = action

    def has_pending(self):
        return self.pending is not None

    def get_pending(self):
        return self.pending