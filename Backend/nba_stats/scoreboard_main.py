import sys
import logging
from typing import Optional
import datetime

from nba_stats.api.nba_client import NBAClient
from nba_stats.data.database import MongoDBClient
from nba_stats.utils.formatters import ScoreboardFormatter

logger = logging.getLogger(__name__)

def process_scoreboard(save_to_db: bool = False) -> None:
    """
    Process scoreboard for a given date and optionally save to MongoDB
    
    Args:
        date (str): The date in YYYYMMDD format
        save_to_db (bool): Whether to save the data to MongoDB
    """
    try:
        date = datetime.date.today()
        # Get scoreboard data from NBA API
        scoreboard_data = NBAClient.get_scoreboard()
        
        if not scoreboard_data:
            print(f"Failed to retrieve scoreboard for date: {date}")
            return
        
        # Print formatted scoreboard
        ScoreboardFormatter.print_scoreboard(scoreboard_data)
        
        # Save to MongoDB if requested
        if save_to_db:
            db_client = MongoDBClient()
            if db_client.save(scoreboard_data, db_name="Scoreboards", collection_name="scoreboard", id_field="game_date"):
                print(f"Scoreboard for date {date} successfully saved to MongoDB")
            else:
                print(f"Failed to save scoreboard for date {date} to MongoDB")
            db_client.close()
                
    except Exception as e:
        logger.error(f"Error processing scoreboard: {e}")
        logger.error(f"Exception details: {str(e)}")
        print("Make sure the date is valid and in the format 'YYYYMMDD'")
def main():
    """Main entry point for the scoreboard application"""
    if len(sys.argv) > 1:
        # Check if the --save flag is provided
        save_to_db = "--save" in sys.argv
    else:
        save_to_db = input("Save to MongoDB? (y/n): ").lower() == 'y'
    
    process_scoreboard(save_to_db)

if __name__ == "__main__":
    main()