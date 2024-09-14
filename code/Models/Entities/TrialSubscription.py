import datetime
import uuid

from Core.Shared.Trails import TRIALS

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
            start_date: datetime = datetime.utcnow(),
            id: str = None,
        ):
        self.id = id or str(uuid.uuid4())
        self.uid = uid
        self.amount = amount
        self.trial = trial
        self.payment_intent = payment_intent
        self.start_date = start_date
        self.end_date = start_date + datetime.timedelta(days=TRIALS[trial]["days"])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trial": self.trial,
            "amount": self.amount,
            "uid": self.uid,
            "payment_intent": self.payment_intent,
            "start_date": self.start_date,
            "end_date": self.end_date
        }
