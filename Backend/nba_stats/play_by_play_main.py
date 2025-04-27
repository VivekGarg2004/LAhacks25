import sys
import logging
from typing import Optional

from nba_stats.api.nba_client import NBAClient
from nba_stats.data.database import MongoDBClient
from nba_stats.utils.formatters import PlayByPlayFormatter

logger = logging.getLogger(__name__)

def process_play_by_play(game_id: str, save_to_db: bool = False) -> None:
    """
    Process play-by-play data for a given game ID and optionally save to MongoDB
    
    Args:
        game_id (str): The NBA game ID
        save_to_db (bool): Whether to save the data to MongoDB
    """
    try:
        # Get play-by-play data from NBA API
        play_by_play_data = NBAClient.get_live_play_by_play(game_id)
        
        if not play_by_play_data:
            print(f"Failed to retrieve play-by-play data for game ID: {game_id}")
            return
        
        # Print formatted play-by-play data
        PlayByPlayFormatter.print_play_by_play(play_by_play_data)
        
        # Save to MongoDB if requested
        if save_to_db:
            db_client = MongoDBClient()
            if db_client.save(play_by_play_data, db_name="PlayByPlay", collection_name="play_by_play"):
                print(f"Play-by-play data for game {game_id} successfully saved to MongoDB")
            else:
                print(f"Failed to save play-by-play data for game {game_id} to MongoDB")
            db_client.close()
                
    except Exception as e:
        logger.error(f"Error processing play-by-play data: {e}")
        logger.error(f"Exception details: {str(e)}")
        print("Make sure the game ID is valid and in the format '0022200001'")
def main():
    """Main entry point for the play-by-play application"""
    if len(sys.argv) > 1:
        game_id = sys.argv[1]
        # Check if the --save flag is provided
        save_to_db = "--save" in sys.argv
    else:
        game_id = input("Enter NBA game ID (default: 0022000181): ") or "0042400103"
        save_to_db = input("Save to MongoDB? (y/n): ").lower() == 'y'
    
    process_play_by_play(game_id, save_to_db)
if __name__ == "__main__":
    main()
