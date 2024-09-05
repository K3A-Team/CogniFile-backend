import uuid

class PasswordResetTokens:
    """
    Represents a password reset token entity in the auth logic.
    """
    def __init__(self, random_value: str, expires_at: str, email: str, id : str = None):
        self.id = id or str(uuid.uuid4())
        self.random_value = random_value
        self.expires_at = expires_at
        self.email = email

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "random_value": self.random_value,
            "email": self.email,
            "expires_at": self.expires_at
        }