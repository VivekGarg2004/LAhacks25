from pymongo import MongoClient
from typing import Optional, Type, Any
import logging

from ..config import MONGO_URI

logger = logging.getLogger(__name__)

class MongoDBClient:
    """Generic MongoDB client for any type of document."""

    def __init__(self, uri: Optional[str] = None):
        self.uri = uri or MONGO_URI
        self.client = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def connect(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(self.uri)
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            return False
    
    def close(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
        self.client = None

    def save(self, obj: Any, db_name: str, collection_name: str, id_field: str = 'game_id') -> bool:
        """
        Save any object that has to_dict() and an ID field.
        """
        if not self.client:
            if not self.connect() :
                return False
        
        db = self.client[db_name]
        collection = db[collection_name]

        try:
            obj_dict = obj.to_dict()
            obj_id = getattr(obj, id_field, None)
            if obj_id is None:
                logger.error(f"Object missing id field: {id_field}")
                return False

            existing = collection.find_one({id_field: obj_id})
            if existing:
                collection.replace_one({id_field: obj_id}, obj_dict)
                logger.info(f"Updated {collection_name} record with {id_field}={obj_id}")
            else:
                result = collection.insert_one(obj_dict)
                logger.info(f"Inserted new record with _id: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving object to MongoDB: {e}")
            return False

    def get(self, obj_id: Any, obj_class: Type, db_name: str, collection_name: str, id_field: str = 'game_id') -> Optional[Any]:
        """
        Retrieve an object by ID and reconstruct it via from_dict().
        """
        if not self.client:
            if not self.connect():
                return None
        
        db = self.client[db_name]
        collection = db[collection_name]

        try:
            data = collection.find_one({id_field: obj_id})
            if data:
                return obj_class.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving object from MongoDB: {e}")
            return None
