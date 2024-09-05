import uuid

class OAuthSessionTokens:
    """
    Represents a oauth session token entity in the auth logic, used to prevent malicious traffic and validate if a certain user has successfuly done a "oauth-tour".
    """
    def __init__(self, token: str, uid: str, id : str = None):
        self.id = id or str(uuid.uuid4())
        self.token = token
        self.uid = uid

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "token": self.token,
            "uid": self.uid,
        }