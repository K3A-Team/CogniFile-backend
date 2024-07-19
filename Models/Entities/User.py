import uuid

class User:
    def __init__(self, firstName: str, lastName: str, email: str, password: str):
        self.id = str(uuid.uuid4())
        self.firstName: str = firstName
        self.lastName: str = lastName
        self.email: str = email
        self.password: str = password

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "firstName": self.firstName,
            "lastName": self.lastName,
            "email": self.email,
            "password": self.password
        }