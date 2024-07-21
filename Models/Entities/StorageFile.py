from typing import List
import uuid

class StorageFile:
    """
        Represents a file stored in the file management system.
    """
    def __init__(
            self, 
            name: str, 
            folder: str,
            ownerId: str , 
            url : str,
            id : str = None,
            readId : List[str] = [], 
            writeId : List[str] = [],
        ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.folder = folder
        self.ownerId = ownerId
        self.readId = readId
        self.writeId = writeId
        self.url = url

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "folder": self.folder,
            "ownerId": self.ownerId,
            "readId": self.readId,
            "writeId": self.writeId,
            "url": self.url
        }