from nba_api.stats.endpoints import BoxScoreTraditionalV2
from nba_stats.api.nba_client import NBAClient
from nba_stats.data.database import MongoDBClient
from nba_stats.utils.formatters import PlayByPlayFormatter
import json
import logging
import sys
from typing import Optional

# Construct box score from play by play

logger = logging.getLogger(__name__)

def construct_box_score(game_id, start_range, end_range, range_type=2):
    """
    Constructs a player box score from an NBA game.

    Parameters:
        game_id (str): The unique ID of the NBA game (e.g., '0022200001').
        start_range (int): Start range for the stats collection.
        end_range (int): End range for the stats collection.
        range_type (int, optional): Type of range to use. Defaults to 2.

    Returns:
        str: JSON-formatted string of player box score stats.
    """
    try:
        box_score = BoxScoreTraditionalV2(game_id=game_id, start_range=start_range, end_range=end_range)
        data = box_score.get_dict()

        headers = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]

        player_stats = [dict(zip(headers, row)) for row in rows]

        print(json.dumps(player_stats, indent=4))
        return json.dumps(player_stats, indent=4)
    
    except Exception as e:
        logger.error(f"Error processing box score data: {e}")
        logger.error(f"Exception details: {str(e)}")
        print("Make sure the game ID is valid and in the format '0022200001'")