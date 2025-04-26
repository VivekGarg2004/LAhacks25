import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection settings for live box scores
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME_boxscore = os.getenv("DB_NAME_boxscore")
COLLECTION_NAME_live = os.getenv("COLLECTION_NAME_live_boxscore", "live_boxscores")
COLLECTION_NAME_static = os.getenv("COLLECTION_NAME_static_boxscore", "static_boxscores")