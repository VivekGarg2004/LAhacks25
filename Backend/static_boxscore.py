from nba_api.stats.endpoints import BoxScoreTraditionalV2
import pandas as pd
import json
from pymongo import MongoClient
import datetime
from dotenv import load_dotenv
import os
# MongoDB connection settings
# Load environment variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME_boxscore")
COLLECTION_NAME = os.getenv("COLLECTION_NAME_static_boxscore")

def get_box_score(game_id):
    """
    Retrieve box score data for a specific NBA game
    
    Args:
        game_id (str): The NBA game ID (format: '0022200001')
    
    Returns:
        dict: Player and team stats for the game
    """
    # Fetch box score data from NBA API
    box_score = BoxScoreTraditionalV2(game_id=game_id)
    
    # Convert to more usable pandas DataFrames
    player_stats = box_score.player_stats.get_data_frame()
    team_stats = box_score.team_stats.get_data_frame()
    
    # Make player stats more readable
    player_stats_clean = player_stats[[
        'TEAM_ABBREVIATION', 'PLAYER_NAME', 'START_POSITION', 
        'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TO', 
        'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT'
    ]]
    
    # Return as dictionary with both player and team stats
    return {
        'game_id': game_id,
        'retrieved_at': datetime.datetime.now(),
        'player_stats': player_stats_clean.to_dict('records'),
        'team_stats': team_stats.to_dict('records')
    }

def connect_to_mongodb(uri=MONGO_URI):
    """Connect to MongoDB and return client"""
    try:
        client = MongoClient(uri)
        # Ping the server to check connection
        client.admin.command('ping')
        print("Connected successfully to MongoDB")
        return client
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        return None

def save_to_mongodb(box_score_data, mongo_uri=MONGO_URI, db_name=DB_NAME, collection_name=COLLECTION_NAME):
    """Save box score data to MongoDB"""
    try:
        # Connect to MongoDB
        client = connect_to_mongodb(mongo_uri)
        if not client:
            return False
        
        # Access database and collection
        print(db_name)
        print(collection_name)
        db = client[db_name]
        collection = db[collection_name]
        
        # Check if game already exists in the database
        game_id = box_score_data['game_id']
        existing_record = collection.find_one({'game_id': game_id})
        
        if existing_record:
            # Update existing record
            result = collection.replace_one({'game_id': game_id}, box_score_data)
            print(f"Updated existing box score for game ID {game_id}")
        else:
            # Insert new record
            result = collection.insert_one(box_score_data)
            print(f"Inserted new box score for game ID {game_id} with _id: {result.inserted_id}")
        
        client.close()
        return True
    
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")
        return False

def print_box_score(game_id, save_to_db=False):
    """
    Print formatted box score for a given game ID and optionally save to MongoDB
    """
    try:
        box_score_data = get_box_score(game_id)
        
        # Print team stats
        print("\n===== TEAM STATS =====")
        for team in box_score_data['team_stats']:
            print(f"\n{team['TEAM_CITY']} {team['TEAM_NAME']} ({team['TEAM_ABBREVIATION']})")
            print(f"Points: {team['PTS']}, FG%: {team['FG_PCT']:.1%}, 3P%: {team['FG3_PCT']:.1%}")
            print(f"Rebounds: {team['REB']}, Assists: {team['AST']}, Turnovers: {team['TO']}")
        
        # Print player stats
        print("\n===== PLAYER STATS =====")
        for team_abbr in set(player['TEAM_ABBREVIATION'] for player in box_score_data['player_stats']):
            team_players = [p for p in box_score_data['player_stats'] if p['TEAM_ABBREVIATION'] == team_abbr]
            print(f"\n{team_abbr} Players:")
            
            # Sort by points scored (highest first)
            for player in sorted(team_players, key=lambda x: x['PTS'], reverse=True):
                print(f"{player['PLAYER_NAME']} - {player['PTS']} pts, {player['REB']} reb, {player['AST']} ast, {player['MIN']} min")
        
        # Save to MongoDB if requested
        if save_to_db:
            if save_to_mongodb(box_score_data):
                print(f"Box score for game {game_id} successfully saved to MongoDB")
            else:
                print(f"Failed to save box score for game {game_id} to MongoDB")
                
    except Exception as e:
        print(f"Error retrieving box score: {e}")
        print("Make sure the game ID is valid and in the format '0022200001'")

if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    import os
    
    if len(sys.argv) > 1:
        game_id = sys.argv[1]
        # Check if the --save flag is provided
        save_to_db = "--save" in sys.argv
    else:
        game_id = input("Enter NBA game ID (default: 0022000181): ") or "0022000181"
        save_to_db = input("Save to MongoDB? (y/n): ").lower() == 'y'
    
    print_box_score(game_id, save_to_db)