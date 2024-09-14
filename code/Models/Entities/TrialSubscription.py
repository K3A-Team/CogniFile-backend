import uuid

class TrialSubscription:
    """
    Represents a Trial Subscription entity.
    """
    def __init__(
            self, 
            uid: str,
            amount: str,
            trial: str,
            payment_intent: str,
            id: str = None,
        ):
        self.id = id or str(uuid.uuid4())
        self.uid = uid
        self.amount = amount
        self.trial = trial
        self.payment_intent = payment_intent

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trial": self.trial,
            "amount": self.amount,
            "uid": self.uid,
            "payment_intent": self.payment_intent
        }
