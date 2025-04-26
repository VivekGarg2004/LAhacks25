from nba_api.live.nba.endpoints import boxscore
import pandas as pd
import json
from pymongo import MongoClient
import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME_boxscore")
COLLECTION_NAME = os.getenv("COLLECTION_NAME_live_boxscore", "live_boxscores")

def get_box_score(game_id):
    """
    Retrieve live box score data for a specific NBA game
    
    Args:
        game_id (str): The NBA game ID (format: '0022200001')
    
    Returns:
        dict: Player and team stats for the game
    """
    # Fetch box score data from NBA API
    box_score_data = boxscore.BoxScore(game_id=game_id)
    
    # Extract home team player stats and convert to DataFrame
    home_players_data = box_score_data.home_team_player_stats.get_dict()
    home_df = pd.DataFrame(home_players_data)
    
    # Extract away team player stats and convert to DataFrame
    away_players_data = box_score_data.away_team_player_stats.get_dict()
    away_df = pd.DataFrame(away_players_data)
    
    # Add team identifier to each player row
    home_df['TEAM_ABBREVIATION'] = box_score_data.home_team.get_dict()['teamTricode']
    away_df['TEAM_ABBREVIATION'] = box_score_data.away_team.get_dict()['teamTricode']
    
    # Combine home and away player stats
    all_players_df = pd.concat([home_df, away_df])
    
    # Extract statistics from nested structure
    player_stats_df = pd.json_normalize(all_players_df.to_dict('records'), 
                                      sep='_',
                                      record_path=None)
    
    # Create clean player stats DataFrame with desired columns
    player_stats_clean = pd.DataFrame()
    player_stats_clean['TEAM_ABBREVIATION'] = player_stats_df['TEAM_ABBREVIATION']
    player_stats_clean['PLAYER_NAME'] = player_stats_df['name']
    player_stats_clean['START_POSITION'] = player_stats_df['position']
    player_stats_clean['MIN'] = player_stats_df['statistics_minutesCalculated']
    player_stats_clean['PTS'] = player_stats_df['statistics_points']
    player_stats_clean['REB'] = player_stats_df['statistics_reboundsTotal']
    player_stats_clean['AST'] = player_stats_df['statistics_assists']
    player_stats_clean['STL'] = player_stats_df['statistics_steals']
    player_stats_clean['BLK'] = player_stats_df['statistics_blocks']
    player_stats_clean['TO'] = player_stats_df['statistics_turnovers']
    player_stats_clean['FGM'] = player_stats_df['statistics_fieldGoalsMade']
    player_stats_clean['FGA'] = player_stats_df['statistics_fieldGoalsAttempted']
    player_stats_clean['FG_PCT'] = player_stats_df['statistics_fieldGoalsPercentage']
    player_stats_clean['FG3M'] = player_stats_df['statistics_threePointersMade']
    player_stats_clean['FG3A'] = player_stats_df['statistics_threePointersAttempted']
    player_stats_clean['FG3_PCT'] = player_stats_df['statistics_threePointersPercentage']
    
    # Extract team stats
    home_team_stats = box_score_data.home_team_stats.get_dict()
    away_team_stats = box_score_data.away_team_stats.get_dict()
    
    # Add team identification to stats
    home_team_info = box_score_data.home_team.get_dict()
    away_team_info = box_score_data.away_team.get_dict()
    
    home_team_stats['TEAM_ID'] = home_team_info['teamId']
    home_team_stats['TEAM_CITY'] = home_team_info['teamCity']
    home_team_stats['TEAM_NAME'] = home_team_info['teamName']
    home_team_stats['TEAM_ABBREVIATION'] = home_team_info['teamTricode']
    home_team_stats['TEAM_SCORE'] = home_team_info['score']
    
    away_team_stats['TEAM_ID'] = away_team_info['teamId']
    away_team_stats['TEAM_CITY'] = away_team_info['teamCity']
    away_team_stats['TEAM_NAME'] = away_team_info['teamName']
    away_team_stats['TEAM_ABBREVIATION'] = away_team_info['teamTricode']
    away_team_stats['TEAM_SCORE'] = away_team_info['score']
    
    # Combine team stats into a list
    team_stats = [home_team_stats, away_team_stats]
    
    # Get game details
    game_details = box_score_data.game_details.get_dict()
    
    # Return as dictionary with both player and team stats
    return {
        'game_id': game_id,
        'retrieved_at': datetime.datetime.now(),
        'game_status': game_details.get('gameStatusText', ''),
        'arena': box_score_data.arena.get_dict() if box_score_data.arena else {},
        'player_stats': player_stats_clean.to_dict('records'),
        'team_stats': team_stats
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
        print(f"Database: {db_name}")
        print(f"Collection: {collection_name}")
        db = client[db_name]
        collection = db[collection_name]
        
        # Check if game already exists in the database
        game_id = box_score_data['game_id']
        existing_record = collection.find_one({'game_id': game_id})
        
        if existing_record:
            # Update existing record
            result = collection.replace_one({'game_id': game_id}, box_score_data)
            print(f"Updated existing live box score for game ID {game_id}")
        else:
            # Insert new record
            result = collection.insert_one(box_score_data)
            print(f"Inserted new live box score for game ID {game_id} with _id: {result.inserted_id}")
        
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
        
        # Print game status
        print(f"\n===== GAME STATUS: {box_score_data['game_status']} =====")
        
        # Print arena info if available
        if box_score_data['arena']:
            arena = box_score_data['arena']
            print(f"Arena: {arena.get('arenaName', 'N/A')} in {arena.get('arenaCity', 'N/A')}, {arena.get('arenaState', 'N/A')}")
        
        # Print team stats
        print("\n===== TEAM STATS =====")
        for team in box_score_data['team_stats']:
            print(f"\n{team['TEAM_CITY']} {team['TEAM_NAME']} ({team['TEAM_ABBREVIATION']}): {team['TEAM_SCORE']} pts")
            print(f"FG%: {team['statistics']['fieldGoalsPercentage']:.1%}, 3P%: {team['statistics']['threePointersPercentage']:.1%}")
            print(f"Rebounds: {team['statistics']['reboundsTotal']}, Assists: {team['statistics']['assists']}, Turnovers: {team['statistics'].get('turnoversTotal', 0)}")
        
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
                print(f"Live box score for game {game_id} successfully saved to MongoDB")
            else:
                print(f"Failed to save live box score for game {game_id} to MongoDB")
                
    except Exception as e:
        print(f"Error retrieving box score: {e}")
        print(f"Exception details: {str(e)}")
        print("Make sure the game ID is valid and in the format '0022200001'")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        game_id = sys.argv[1]
        # Check if the --save flag is provided
        save_to_db = "--save" in sys.argv
    else:
        game_id = input("Enter NBA game ID (default: 0022000181): ") or "0042400103"
        save_to_db = input("Save to MongoDB? (y/n): ").lower() == 'y'
    
    print_box_score(game_id, save_to_db)