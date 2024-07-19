from typing import List


class StorageFile:
    def __init__(
            self, 
            name: str, 
            folder: str,
            ownerId: str , 
            readId : List[str] = [], 
            writeId : List[str] = []
        ):
        self.name = name
        self.folder = folder
        self.ownerId = ownerId
        self.readId = readId
        self.writeId = writeId


    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "folder": self.folder,
            "ownerId": self.ownerId,
            "readId": self.readId,
            "writeId": self.writeId
        }