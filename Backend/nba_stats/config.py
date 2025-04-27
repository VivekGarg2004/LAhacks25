import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection settings for live box scores
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME_boxscore = os.getenv("DB_NAME_boxscore")
DB_NAME_play_by_play = os.getenv("DB_NAME_play_by_play")
DB_NAME_scoreboard = os.getenv("DB_NAME_scoreboard")
COLLECTION_NAME_live = os.getenv("COLLECTION_NAME_live_boxscore", "live_boxscores")
COLLECTION_NAME_static = os.getenv("COLLECTION_NAME_static_boxscore", "static_boxscores")
COLLECTION_NAME_play_by_play = os.getenv("COLLECTION_NAME_play_by_play", "play_by_play")
COLLECTION_NAME_scoreboard = os.getenv("COLLECTION_NAME_scoreboard", "scoreboard")

