from pydantic import BaseModel

class SubscriptionRequest(BaseModel):
    plan: str