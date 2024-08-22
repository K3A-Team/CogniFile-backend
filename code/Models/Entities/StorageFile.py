from typing import List
import uuid
import datetime
class StorageFile:
    """
        Represents a file stored in the file management system.
    """
    def __init__(
            self, 
            name: str, 
            folder: str,
            ownerId: str, 
            size: str,
            url : str,
            id : str = None,
            tags: List[str] = [],
            readId : List[str] = [], 
            writeId : List[str] = [],
            interactionDate = str
        ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.folder = folder
        self.size = size
        self.ownerId = ownerId
        self.readId = readId
        self.writeId = writeId
        self.interactionDate = interactionDate or datetime.datetime.now().isoformat()
        self.tags = tags
        self.url = url

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "folder": self.folder,
            "size": self.size,
            "tags": self.tags,
            "ownerId": self.ownerId,
            "readId": self.readId,
            "writeId": self.writeId,
            "url": self.url,
            "interactionDate": self.interactionDate
        }
