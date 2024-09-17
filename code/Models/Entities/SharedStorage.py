from typing import List
import uuid
import datetime
class SharedStorage:
    """
        Represents a shared storage in the file management system.
    """
    def __init__(
            self, 
            name: str, 
            imagePath: str,
            rootFolderId: str,
            ownerId: str,
            readId : List[str], 
            writeId : List[str],
            id : str = None,

        ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.ownerId = ownerId
        self.imagePath = imagePath
        self.rootFolderId = rootFolderId
        self.readId = readId
        self.writeId = writeId

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "imagePath": self.imagePath,
            "rootFolderId": self.rootFolderId,
            "ownerId": self.ownerId,
            "readId": self.readId,
            "writeId": self.writeId
        }
