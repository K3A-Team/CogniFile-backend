import uuid

class User:
    """
    Represents a user in the file management system.
    """
    def __init__(self, firstName: str, lastName: str, email: str, password: str, rootFolderId :str, chatbotSessionId : str,id : str = None):
        self.id = id or str(uuid.uuid4())
        self.firstName: str = firstName
        self.lastName: str = lastName
        self.email: str = email
        self.password: str = password
        self.rootFolderId = rootFolderId
        self.chatbotSessionId = chatbotSessionId

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "firstName": self.firstName,
            "lastName": self.lastName,
            "email": self.email,
            "password": self.password,
            "rootFolderId": self.rootFolderId,
            "chatbotSessionId" : self.chatbotSessionId
        }