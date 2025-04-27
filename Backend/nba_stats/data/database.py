from pymongo import MongoClient
from typing import Optional, Type, Any, List
from pymongo import DESCENDING
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
            self.client.server_info()
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
                logger.error("Failed to connect to MongoDB")
                return None
        
        db = self.client[db_name]
        collection = db[collection_name]

        try:
            data = collection.find_one({id_field: obj_id})
            if data:
                data.pop('_id', None)
                return obj_class.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving object from MongoDB: {e}")
            return None
        
    def get_latest(self, obj_id: Any, obj_class: Type, db_name: str, collection_name: str, limit: int = 30, sort_field: str = '_id', sort_direction: int = DESCENDING) -> Optional[List[Any]]:
        """
        Retrieve the latest 'limit' number of objects matching the query,
        sorted by 'sort_field' in 'sort_direction', and reconstruct them
        via from_dict(). Returns the last 'limit' objects based on the sort order.
        """
        if not self.client:
            if not self.connect():
                logger.error("Failed to connect to MongoDB")
                return None

        db = self.client[db_name]
        collection = db[collection_name]

        try:
            cursor = collection.find_one({"game_id": obj_id})
            cursor.pop('_id', None)
            plays = cursor.get('plays', [])

            if not plays:
                logger.error(f"No plays found for game_id: {obj_id}")
                return None
            limit = min(limit, len(plays))
            list_30 = plays[-limit:]
            new_dict = {
                'game_id': obj_id,
                'plays': list_30
            }
            
            return obj_class.from_dict(new_dict)
        except Exception as e:
            logger.error(f"Error retrieving latest objects from MongoDB: {e}")
            return None