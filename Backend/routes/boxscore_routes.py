from flask import Blueprint, jsonify, request, Response
import io
import traceback
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import logging
from nba_stats.data.database import MongoDBClient
from nba_stats.api.nba_client import NBAClient
from nba_stats.data.models import BoxScoreData
import requests

boxscore_bp = Blueprint('boxscore', __name__)

@boxscore_bp.route('/boxscore/<game_id>', methods=['GET'])
def get_boxscore(game_id):
    """Get box score data for a specific game"""
    try:
        # First try to get from database
        with MongoDBClient() as db_client:
            boxscore_data = db_client.get(
                obj_id=game_id,
                obj_class=BoxScoreData,
                db_name="Boxscores",
                collection_name="live_boxscores"
            )
            
            # If not in database, fetch from API
            if not boxscore_data:
                boxscore_data = NBAClient.get_live_box_score(game_id)
                if boxscore_data:
                    # Save to database for future requests
                    db_client.save(boxscore_data, "Boxscores", "live_boxscores")
            
            if not boxscore_data:
                return jsonify({"error": "Box score not found"}), 404
            
            # Return the data
            return jsonify(boxscore_data.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@boxscore_bp.route('/hello', methods=['GET'])
def hello_world():
    """Simple endpoint to return Hello World"""
    return jsonify({"message": "Hello, World!"})

@boxscore_bp.route('/boxscore/game_tables/<game_id>', methods=['GET'])
def get_game_tables(game_id):
    """Get game tables for a specific game as a visualization"""
    try:
        # First try to get from database
        with MongoDBClient() as db_client:
            boxscore_data = db_client.get(
                obj_id=game_id,
                obj_class=BoxScoreData,
                db_name="Boxscores",
                collection_name="live_boxscores"
            )
            # If not in database, fetch from API
            if not boxscore_data:
                logging.info(f"Boxscore data not found in database, fetching from API for game ID: {game_id}")
                boxscore_data = NBAClient.get_live_box_score(game_id)
                if boxscore_data:
                    # Save to database for future requests
                    db_client.save(boxscore_data, "Boxscores", "live_boxscores")
            
            if not boxscore_data:
                return jsonify({"error": "Box score not found"}), 404
            
            # Instead of returning JSON, generate visualization
            from flask import send_file
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt
            import io

            # Process data
            data = boxscore_data.to_dict()
            
            # Create a DataFrame from player_stats
            df = pd.DataFrame(data['player_stats'])
            
            # Convert minutes from "PTXXM" format to numeric minutes
            df['MIN_NUM'] = df['MIN'].apply(lambda min_str: 
                0 if min_str == "PT00M" else int(min_str.replace("PT", "").replace("M", "")))
            
            # Fix START_POSITION where it's NaN
            df['START_POSITION'] = df['START_POSITION'].apply(
                lambda x: '' if isinstance(x, dict) and '$numberDouble' in x else x)
            
            # Get game information
            game_status = data['game_status']
            arena_name = data['arena']['arenaName']
            arena_location = f"{data['arena']['arenaCity']}, {data['arena']['arenaState']}"
            
            # Get team scores
            team_names = [team['teamCity'] + ' ' + team['teamName'] for team in data['team_stats']]
            team_scores = [team['TEAM_SCORE'] for team in data['team_stats']]
            
            # Create a title for the visualization
            title = f"{team_names[0]} vs {team_names[1]}"
            subtitle = f"{arena_name}, {arena_location} | {game_status}"
            
            # Create box score tables for both teams
            def create_box_score_table(df, team_abbr):
                # Filter dataframe for this team
                team_df = df[df['TEAM_ABBREVIATION'] == team_abbr].copy()
                
                # Sort by starters first, then minutes played
                team_df['is_starter'] = team_df['START_POSITION'].apply(lambda x: 0 if x == '' else 1)
                team_df = team_df.sort_values(by=['is_starter', 'MIN_NUM'], ascending=[False, False])
                
                # Select relevant columns
                box_score = team_df[['PLAYER_NAME', 'MIN_NUM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TO', 
                                     'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT']].copy()
                
                # Format field goal and 3-point percentages
                box_score['FG'] = box_score.apply(lambda row: f"{row['FGM']}-{row['FGA']} ({row['FG_PCT']:.3f})", axis=1)
                box_score['3PT'] = box_score.apply(lambda row: f"{row['FG3M']}-{row['FG3A']} ({row['FG3_PCT']:.3f})", axis=1)
                
                # Drop original shooting columns
                box_score = box_score.drop(columns=['FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT'])

                # Set all 0 value to '-'
                box_score = box_score.replace(0, '-')
                box_score = box_score.fillna('-')
                
                # Rename columns
                box_score = box_score.rename(columns={
                    'PLAYER_NAME': 'PLAYER', 
                    'MIN_NUM': 'MIN',
                    'TO': 'TOV'
                })
                
                return box_score
            
            # Get the team abbreviations
            team_abbrs = df['TEAM_ABBREVIATION'].unique()
            
            # Create box score tables
            team1_box = create_box_score_table(df, team_abbrs[0])
            team2_box = create_box_score_table(df, team_abbrs[1])
            
            # Set up the figure with appropriate size
            fig_height = (len(team1_box) + len(team2_box) + 3) * 0.4  # Adjust for spacing
            plt.figure(figsize=(12, fig_height))
            
            # Create a grid layout
            plt.subplot(2, 1, 1)
            plt.title(f"{team_names[0]} ({team_scores[0]})", fontsize=14, fontweight='bold')
            plt.axis('off')
            
            # First team table
            team1_table = plt.table(
                cellText=team1_box.values,
                colLabels=team1_box.columns,
                loc='center',
                cellLoc='center'
            )
            team1_table.auto_set_font_size(False)
            team1_table.set_fontsize(9)
            team1_table.scale(1, 1.5)
            
            # Style header row
            for k, cell in team1_table._cells.items():
                if k[0] == 0:  # Header row
                    cell.set_text_props(weight='bold', color='white')
                    cell.set_facecolor('#3498db')  # Clean blue
                elif k[0] % 2 == 1:  # Alternating row colors
                    cell.set_facecolor('#f2f2f2')
            
            plt.subplot(2, 1, 2)
            plt.title(f"{team_names[1]} ({team_scores[1]})", fontsize=14, fontweight='bold')
            plt.axis('off')
            
            # Second team table
            team2_table = plt.table(
                cellText=team2_box.values,
                colLabels=team2_box.columns,
                loc='center',
                cellLoc='center'
            )
            team2_table.auto_set_font_size(False)
            team2_table.set_fontsize(9)
            team2_table.scale(1, 1.5)
            
            # Style header row
            for k, cell in team2_table._cells.items():
                if k[0] == 0:  # Header row
                    cell.set_text_props(weight='bold', color='white')
                    cell.set_facecolor('#2c3e50')  # Dark slate
                elif k[0] % 2 == 1:  # Alternating row colors
                    cell.set_facecolor('#f2f2f2')
            
            # Add main title
            plt.suptitle(f"{title}\n{subtitle}", fontsize=16, y=0.98)
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.9, hspace=0.3)
            
            # Instead of saving to file, save to memory buffer
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format='png', dpi=300, bbox_inches='tight')
            img_buf.seek(0)
            plt.close()  # Explicitly close the figure
            
            return Response(img_buf, mimetype='image/png')
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


@boxscore_bp.route('/boxscore/game_tables_current', methods=['GET'])
def get_game_tables_current():
    """Get game tables for a specific game as a visualization"""
    try:
        # First try to get from database
        base_url = "http://127.0.0.1:3000/api/v1"
        # Get current game ID
        game_id = requests.get(f"{base_url}/current_game_id").json().get('game_id')
        with MongoDBClient() as db_client:
            boxscore_data = db_client.get(
                obj_id=game_id,
                obj_class=BoxScoreData,
                db_name="Boxscores",
                collection_name="live_boxscores"
            )
            # If not in database, fetch from API
            if not boxscore_data:
                logging.info(f"Boxscore data not found in database, fetching from API for game ID: {game_id}")
                boxscore_data = NBAClient.get_live_box_score(game_id)
                if boxscore_data:
                    # Save to database for future requests
                    db_client.save(boxscore_data, "Boxscores", "live_boxscores")
            
            if not boxscore_data:
                return jsonify({"error": "Box score not found"}), 404
            
            # Instead of returning JSON, generate visualization
            from flask import send_file
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt
            import io

            # Process data
            data = boxscore_data.to_dict()
            
            # Create a DataFrame from player_stats
            df = pd.DataFrame(data['player_stats'])
            
            # Convert minutes from "PTXXM" format to numeric minutes
            df['MIN_NUM'] = df['MIN'].apply(lambda min_str: 
                0 if min_str == "PT00M" else int(min_str.replace("PT", "").replace("M", "")))
            
            # Fix START_POSITION where it's NaN
            df['START_POSITION'] = df['START_POSITION'].apply(
                lambda x: '' if isinstance(x, dict) and '$numberDouble' in x else x)
            
            # Get game information
            game_status = data['game_status']
            arena_name = data['arena']['arenaName']
            arena_location = f"{data['arena']['arenaCity']}, {data['arena']['arenaState']}"
            
            # Get team scores
            team_names = [team['teamCity'] + ' ' + team['teamName'] for team in data['team_stats']]
            team_scores = [team['TEAM_SCORE'] for team in data['team_stats']]
            
            # Create a title for the visualization
            title = f"{team_names[0]} vs {team_names[1]}"
            subtitle = f"{arena_name}, {arena_location} | {game_status}"
            
            # Create box score tables for both teams
            def create_box_score_table(df, team_abbr):
                # Filter dataframe for this team
                team_df = df[df['TEAM_ABBREVIATION'] == team_abbr].copy()
                
                # Sort by starters first, then minutes played
                team_df['is_starter'] = team_df['START_POSITION'].apply(lambda x: 0 if x == '' else 1)
                team_df = team_df.sort_values(by=['is_starter', 'MIN_NUM'], ascending=[False, False])
                
                # Select relevant columns
                box_score = team_df[['PLAYER_NAME', 'MIN_NUM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TO', 
                                     'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT']].copy()
                
                # Format field goal and 3-point percentages
                box_score['FG'] = box_score.apply(lambda row: f"{row['FGM']}-{row['FGA']} ({row['FG_PCT']:.3f})", axis=1)
                box_score['3PT'] = box_score.apply(lambda row: f"{row['FG3M']}-{row['FG3A']} ({row['FG3_PCT']:.3f})", axis=1)
                
                # Drop original shooting columns
                box_score = box_score.drop(columns=['FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT'])

                # Set all 0 value to '-'
                box_score = box_score.replace(0, '-')
                box_score = box_score.fillna('-')
                
                # Rename columns
                box_score = box_score.rename(columns={
                    'PLAYER_NAME': 'PLAYER', 
                    'MIN_NUM': 'MIN',
                    'TO': 'TOV'
                })
                
                return box_score
            
            # Get the team abbreviations
            team_abbrs = df['TEAM_ABBREVIATION'].unique()
            
            # Create box score tables
            team1_box = create_box_score_table(df, team_abbrs[0])
            team2_box = create_box_score_table(df, team_abbrs[1])
            
            # Set up the figure with appropriate size
            fig_height = (len(team1_box) + len(team2_box) + 3) * 0.4  # Adjust for spacing
            plt.figure(figsize=(12, fig_height))
            
            # Create a grid layout
            plt.subplot(2, 1, 1)
            plt.title(f"{team_names[0]} ({team_scores[0]})", fontsize=14, fontweight='bold')
            plt.axis('off')
            
            # First team table
            team1_table = plt.table(
                cellText=team1_box.values,
                colLabels=team1_box.columns,
                loc='center',
                cellLoc='center'
            )
            team1_table.auto_set_font_size(False)
            team1_table.set_fontsize(9)
            team1_table.scale(1, 1.5)
            
            # Style header row
            for k, cell in team1_table._cells.items():
                if k[0] == 0:  # Header row
                    cell.set_text_props(weight='bold', color='white')
                    cell.set_facecolor('#3498db')  # Clean blue
                elif k[0] % 2 == 1:  # Alternating row colors
                    cell.set_facecolor('#f2f2f2')
            
            plt.subplot(2, 1, 2)
            plt.title(f"{team_names[1]} ({team_scores[1]})", fontsize=14, fontweight='bold')
            plt.axis('off')
            
            # Second team table
            team2_table = plt.table(
                cellText=team2_box.values,
                colLabels=team2_box.columns,
                loc='center',
                cellLoc='center'
            )
            team2_table.auto_set_font_size(False)
            team2_table.set_fontsize(9)
            team2_table.scale(1, 1.5)
            
            # Style header row
            for k, cell in team2_table._cells.items():
                if k[0] == 0:  # Header row
                    cell.set_text_props(weight='bold', color='white')
                    cell.set_facecolor('#2c3e50')  # Dark slate
                elif k[0] % 2 == 1:  # Alternating row colors
                    cell.set_facecolor('#f2f2f2')
            
            # Add main title
            plt.suptitle(f"{title}\n{subtitle}", fontsize=16, y=0.98)
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.9, hspace=0.3)
            
            # Instead of saving to file, save to memory buffer
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format='png', dpi=300, bbox_inches='tight')
            img_buf.seek(0)
            plt.close()  # Explicitly close the figure
            
            return Response(img_buf, mimetype='image/png')
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500