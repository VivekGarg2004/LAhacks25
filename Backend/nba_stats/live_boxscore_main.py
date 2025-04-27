import sys
import logging
from typing import Optional

from nba_stats.api.nba_client import NBAClient
from nba_stats.data.database import MongoDBClient
from nba_stats.utils.formatters import BoxScoreFormatter

logger = logging.getLogger(__name__)

def process_box_score(game_id: str, save_to_db: bool = False) -> None:
    """
    Process box score for a given game ID and optionally save to MongoDB
    
    Args:
        game_id (str): The NBA game ID
        save_to_db (bool): Whether to save the data to MongoDB
    """
    try:
        # Get box score data from NBA API
        box_score_data = NBAClient.get_live_box_score(game_id)
        
        if not box_score_data:
            print(f"Failed to retrieve box score for game ID: {game_id}")
            return
        
        # Print formatted box score
        BoxScoreFormatter.print_box_score(box_score_data)
        
        # Save to MongoDB if requested
        if save_to_db:
            db_client = MongoDBClient()
            if db_client.save(box_score_data, db_name="Boxscores", collection_name="live_boxscores"):
                print(f"Live box score for game {game_id} successfully saved to MongoDB")
            else:
                print(f"Failed to save live box score for game {game_id} to MongoDB")
            db_client.close()
                
    except Exception as e:
        logger.error(f"Error processing box score: {e}")
        logger.error(f"Exception details: {str(e)}")
        print("Make sure the game ID is valid and in the format '0022200001'")

def main():
    """Main entry point for the application"""
    if len(sys.argv) > 1:
        game_id = sys.argv[1]
        # Check if the --save flag is provided
        save_to_db = "--save" in sys.argv
    else:
        game_id = input("Enter NBA game ID (default: 0042400103): ") or "0042400103"
        save_to_db = input("Save to MongoDB? (y/n): ").lower() == 'y'
    
    process_box_score(game_id, save_to_db)

if __name__ == "__main__":
    main()