from flask import Blueprint, jsonify, request, Response
from nba_stats.data.database import MongoDBClient
from nba_stats.api.nba_client import NBAClient
import io
import traceback
import matplotlib
# Force matplotlib to use non-interactive backend that works in Flask threads
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import pandas as pd
import numpy as np
import json
import logging
from nba_stats.data.models import PlayByPlayData
import re
import textwrap
import requests


play_by_play_image_bp = Blueprint('play_by_play_image', __name__)

def clean_time_string(time_string):
    """
    Cleans a time string in ISO 8601 duration format (e.g., PT03M51.00S)
    to extract the minutes and seconds as "MM:SS".

    Args:
        time_string: The time string to clean.

    Returns:
        The cleaned time string in "MM:SS" format, or None if the input
        string is not in the expected format.
    """
    match = re.search(r"PT(\d{2})M(\d{2}(?:\.\d+)?)S", time_string)
    if match:
        minutes = match.group(1)
        seconds = match.group(2)
        # Remove fractional seconds
        seconds = seconds.split('.')[0]
        return f"{minutes}:{seconds}"
    else:
        return None


def wrap_text(text, width=40):  # Increase default width for Play column
    """
    Wraps text to a specified width.
    """
    if not isinstance(text, str):
        return str(text)
    return '\n'.join(textwrap.wrap(text, width=width))


@play_by_play_image_bp.route('/play-by-play-image/<game_id>', methods=['GET'])
def get_play_by_play_image(game_id):
    """Generate a play-by-play image from the database"""
    try:
        # Fetch play-by-play data from the database
        with MongoDBClient() as db_client:
            play_by_play_data = db_client.get_latest(
                obj_id=game_id,
                obj_class=PlayByPlayData,
                db_name="PlayByPlay",
                collection_name="play_by_play"
            )
            
            
            # If not in database, fetch from API
            if not play_by_play_data:
                logging.info(f"Play-by-play data not found in database, fetching from API for game ID: {game_id}")
                play_by_play_data = NBAClient.get_live_play_by_play(game_id)
                if play_by_play_data:
                    # Save to database for future requests
                    db_client.save(play_by_play_data, "PlayByPlay", "play_by_play")
                

        if not play_by_play_data:
            return jsonify({"error": "Play-by-play data not found"}), 404

        # Process play-by-play data
        new_list = []
        prev_home_score = None
        prev_away_score = None
        
        for play in play_by_play_data.plays:
            temp_dict = {}
            
            # Process period
            period = play.get('period', None)
            if period:
                temp_dict['Period'] = period
            else:
                temp_dict['Period'] = None
                
            # Process clock
            clock = play.get('clock', None)
            clean_clock = clean_time_string(clock)
            if clean_clock:
                temp_dict['Time'] = clean_clock
            else:
                temp_dict['Time'] = None
                
            # Process team
            team_tricode = play.get('teamTricode', None)
            if team_tricode:
                temp_dict['Team'] = team_tricode
            else:
                temp_dict['Team'] = '-'
                
            # Process scores with indicators for changes
            home_score = play.get('scoreHome', None)
            away_score = play.get('scoreAway', None)
            
            # Format scores with indicators
            if home_score is not None and away_score is not None:
                # Check for score changes
                home_changed = prev_home_score is not None and home_score != prev_home_score
                away_changed = prev_away_score is not None and away_score != prev_away_score
                
                # Store scores
                temp_dict['Score'] = f"{home_score}-{away_score}"
                
                # Save current scores for next iteration
                prev_home_score = home_score
                prev_away_score = away_score
                
                # Store an indicator for highlighting
                if home_changed:
                    temp_dict['home_changed'] = True
                if away_changed:
                    temp_dict['away_changed'] = True
            else:
                temp_dict['Score'] = '-'
                
            # Process description
            description = play.get('description', None)
            if description:
                temp_dict['Play'] = description
            else:
                temp_dict['Play'] = '-'
                
            new_list.append(temp_dict)
        new_list.reverse()  # Reverse the list to show the latest plays at the top
        # Create DataFrame with better column names and order
        columns = ['Period', 'Time', 'Team', 'Score', 'Play']
        df = pd.DataFrame(new_list)[columns]
        #logging.info(f"DataFrame created with {len(df)} rows {df.head()}")
        
        # Create a figure with the non-interactive backend
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.axis('off')
        
        # Define colors
        header_color = '#1D428A'  # NBA blue
        row_colors = ['#FFFFFF', '#F0F0F0']  # White and light gray for alternating rows
        highlight_color = '#FDB927'  # NBA gold for highlighting
        border_color = '#000000'  # Black for borders
        
        # Create the table with explicit cell text creation
        cell_text = []
        for _, row in df.iterrows():
            # Create a list of wrapped text values for each row
            cell_text.append([wrap_text(str(val)) for val in row.values])

        # Create the table
        table = ax.table(
            cellText=cell_text,
            colLabels=[wrap_text(col, width=15) for col in df.columns],
            cellLoc='center',
            loc='center',
            # Adjust these values - give much more space to the Play column (last value)
            colWidths=[0.06, 0.06, 0.06, 0.10, 0.72]  # Total should be 1.0
        )

        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)

        # Style header row
        for col_idx in range(len(df.columns)):
            cell = table[(0, col_idx)]
            cell.set_text_props(color='white', fontweight='bold')
            cell.set_facecolor(header_color)
            cell.set_edgecolor(border_color)
            cell.set_linewidth(1)
            cell.set_height(0.06)  # Make header slightly taller

        # Style data rows with alternating colors and score highlights
        for row_idx in range(1, len(df) + 1):
            # Get the actual DataFrame index for this row
            df_idx = row_idx - 1
            row_color = row_colors[row_idx % 2]
        
            for col_idx, col_name in enumerate(df.columns):
                cell = table[(row_idx, col_idx)]
                cell.set_facecolor(row_color)
                cell.set_edgecolor(border_color)
                cell.set_linewidth(0.5)
            
            # For Play column (description), set left alignment
            if col_name == 'Play':
                cell.set_text_props(ha='left', va='center')
                cell.PAD = 0.1  # Increase padding
                # Ensure text is wrapped with a wider width for this column
                cell._text.set_text(wrap_text(df.iloc[df_idx][col_name], width=60))
            # Highlight score changes - fixed index lookup
            if col_name == 'Score' and df_idx < len(new_list):
                if new_list[df_idx].get('home_changed', False) or new_list[df_idx].get('away_changed', False):
                    cell.set_facecolor(highlight_color)
                    cell.set_text_props(fontweight='bold')
        
        # Adjust table appearance
        table.scale(1, 1.5)  # Stretch table vertically for better readability
        table.auto_set_column_width([0, 1, 2, 3])  # Let matplotlib handle width of first 4 columns
        
        # Add title
        plt.suptitle(f' Play by Play', fontsize=16, y=0.95)
        
        # Adjust layout
        plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
        
        # Save figure to bytesIO
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight', dpi=150)
        img.seek(0)
        plt.close(fig)

        return Response(img, mimetype='image/png')
    except Exception as e:
        logging.error(f"Error generating play-by-play image: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500



@play_by_play_image_bp.route('/play-by-play-image-current', methods=['GET'])
def get_play_by_play_image_current():
    """Generate a play-by-play image from the database"""
    try:
        base_url = "http://127.0.0.1:3000/api/v1"
        # Get current game ID
        game_id = requests.get(f"{base_url}/current_game_id").json().get('game_id')
        # Fetch play-by-play data from the database
        with MongoDBClient() as db_client:
            play_by_play_data = db_client.get_latest(
                obj_id=game_id,
                obj_class=PlayByPlayData,
                db_name="PlayByPlay",
                collection_name="play_by_play"
            )
            
            
            # If not in database, fetch from API
            if not play_by_play_data:
                logging.info(f"Play-by-play data not found in database, fetching from API for game ID: {game_id}")
                play_by_play_data = NBAClient.get_live_play_by_play(game_id)
                if play_by_play_data:
                    # Save to database for future requests
                    db_client.save(play_by_play_data, "PlayByPlay", "play_by_play")
                

        if not play_by_play_data:
            return jsonify({"error": "Play-by-play data not found"}), 404

        # Process play-by-play data
        new_list = []
        prev_home_score = None
        prev_away_score = None
        
        for play in play_by_play_data.plays:
            temp_dict = {}
            
            # Process period
            period = play.get('period', None)
            if period:
                temp_dict['Period'] = period
            else:
                temp_dict['Period'] = None
                
            # Process clock
            clock = play.get('clock', None)
            clean_clock = clean_time_string(clock)
            if clean_clock:
                temp_dict['Time'] = clean_clock
            else:
                temp_dict['Time'] = None
                
            # Process team
            team_tricode = play.get('teamTricode', None)
            if team_tricode:
                temp_dict['Team'] = team_tricode
            else:
                temp_dict['Team'] = '-'
                
            # Process scores with indicators for changes
            home_score = play.get('scoreHome', None)
            away_score = play.get('scoreAway', None)
            
            # Format scores with indicators
            if home_score is not None and away_score is not None:
                # Check for score changes
                home_changed = prev_home_score is not None and home_score != prev_home_score
                away_changed = prev_away_score is not None and away_score != prev_away_score
                
                # Store scores
                temp_dict['Score'] = f"{home_score}-{away_score}"
                
                # Save current scores for next iteration
                prev_home_score = home_score
                prev_away_score = away_score
                
                # Store an indicator for highlighting
                if home_changed:
                    temp_dict['home_changed'] = True
                if away_changed:
                    temp_dict['away_changed'] = True
            else:
                temp_dict['Score'] = '-'
                
            # Process description
            description = play.get('description', None)
            if description:
                temp_dict['Play'] = description
            else:
                temp_dict['Play'] = '-'
                
            new_list.append(temp_dict)
        new_list.reverse()  # Reverse the list to show the latest plays at the top
        # Create DataFrame with better column names and order
        columns = ['Period', 'Time', 'Team', 'Score', 'Play']
        df = pd.DataFrame(new_list)[columns]
        #logging.info(f"DataFrame created with {len(df)} rows {df.head()}")
        
        # Create a figure with the non-interactive backend
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.axis('off')
        
        # Define colors
        header_color = '#1D428A'  # NBA blue
        row_colors = ['#FFFFFF', '#F0F0F0']  # White and light gray for alternating rows
        highlight_color = '#FDB927'  # NBA gold for highlighting
        border_color = '#000000'  # Black for borders
        
        # Create the table with explicit cell text creation
        cell_text = []
        for _, row in df.iterrows():
            # Create a list of wrapped text values for each row
            cell_text.append([wrap_text(str(val)) for val in row.values])

        # Create the table
        table = ax.table(
            cellText=cell_text,
            colLabels=[wrap_text(col, width=15) for col in df.columns],
            cellLoc='center',
            loc='center',
            # Adjust these values - give much more space to the Play column (last value)
            colWidths=[0.06, 0.06, 0.06, 0.10, 0.72]  # Total should be 1.0
        )

        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)

        # Style header row
        for col_idx in range(len(df.columns)):
            cell = table[(0, col_idx)]
            cell.set_text_props(color='white', fontweight='bold')
            cell.set_facecolor(header_color)
            cell.set_edgecolor(border_color)
            cell.set_linewidth(1)
            cell.set_height(0.06)  # Make header slightly taller

        # Style data rows with alternating colors and score highlights
        for row_idx in range(1, len(df) + 1):
            # Get the actual DataFrame index for this row
            df_idx = row_idx - 1
            row_color = row_colors[row_idx % 2]
        
            for col_idx, col_name in enumerate(df.columns):
                cell = table[(row_idx, col_idx)]
                cell.set_facecolor(row_color)
                cell.set_edgecolor(border_color)
                cell.set_linewidth(0.5)
            
            # For Play column (description), set left alignment
            if col_name == 'Play':
                cell.set_text_props(ha='left', va='center')
                cell.PAD = 0.1  # Increase padding
                # Ensure text is wrapped with a wider width for this column
                cell._text.set_text(wrap_text(df.iloc[df_idx][col_name], width=60))
            # Highlight score changes - fixed index lookup
            if col_name == 'Score' and df_idx < len(new_list):
                if new_list[df_idx].get('home_changed', False) or new_list[df_idx].get('away_changed', False):
                    cell.set_facecolor(highlight_color)
                    cell.set_text_props(fontweight='bold')
        
        # Adjust table appearance
        table.scale(1, 1.5)  # Stretch table vertically for better readability
        table.auto_set_column_width([0, 1, 2, 3])  # Let matplotlib handle width of first 4 columns
        
        # Add title
        plt.suptitle(f' Play by Play', fontsize=16, y=0.95)
        
        # Adjust layout
        plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
        
        # Save figure to bytesIO
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight', dpi=150)
        img.seek(0)
        plt.close(fig)

        return Response(img, mimetype='image/png')
    except Exception as e:
        logging.error(f"Error generating play-by-play image: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
