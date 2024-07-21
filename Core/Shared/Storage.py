import firebase_admin
from firebase_admin import credentials,auth
from firebase_admin import storage
import json
import os
import uuid

db = storage.bucket()

class Storage:
    """
    The Storage class provides methods to interact with Firebase Storage, 
    including storing and deleting files. It includes methods to upload a file to Firebase Storage and retrieve its public URL, 
    as well as to delete a file from Firebase Storage. 
    The class handles potential exceptions related to Firebase operations.
    """
    @staticmethod
    def store(file, filename):
        """
        Stores a file in Firebase Storage and returns its public URL.

        Args:
            file: The file to be stored.
            filename (str): The name to be used for the stored file.

        Returns:
            str: The public URL of the stored file.

        Raises:
            google.cloud.exceptions.GoogleCloudError: If there is an error uploading the file.
        """
        blob = db.blob(filename)
        blob.metadata = {"firebaseStorageDownloadTokens": str(uuid.uuid4())}
        
        blob.upload_from_file(file)
        download_url = blob.public_url
        # Create a token by default 
        blob.make_public()
        return download_url

    @staticmethod
    def delete(filename):
        """
        Deletes a file from Firebase Storage.
        Args: filename (str): The name of the file to be deleted.
        Returns: None
        Raises: google.cloud.exceptions.GoogleCloudError: If there is an error deleting the file.
        """
        blob = db.blob(filename)
        return blob.delete()
    