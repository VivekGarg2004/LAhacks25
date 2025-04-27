from flask import Blueprint, jsonify, request, Response
from nba_stats.data.database import MongoDBClient
from nba_stats.api.nba_client import NBAClient
import io
import traceback
import matplotlib
# Force matplotlib to use non-interactive backend that works in Flask threads
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import logging
from nba_stats.data.models import PlayByPlayData


play_by_play_image_bp = Blueprint('play_by_play_image', __name__)


@play_by_play_image_bp.route('/play-by-play-image/<game_id>', methods=['GET'])
def get_play_by_play_image(game_id):
    """Generate a play-by-play image from the database"""
    try:
        # Fetch play-by-play data from the database
        with MongoDBClient() as db_client:
            play_by_play_data = db_client.get(
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
                    
        logging.info(f"Play-by-play data: {play_by_play_data}")

        if not play_by_play_data:
            return jsonify({"error": "Play-by-play data not found"}), 404

        # Convert the plays list to a DataFrame
        plays = play_by_play_data.plays
        df = pd.DataFrame(plays)


        # Create a figure with the non-interactive backend
        fig, ax = plt.subplots(figsize=(10, 6))

        # Create a table visualization
        ax.axis('tight')
        ax.axis('off')
        table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')

        # Save the plot to a BytesIO object
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight', dpi=150, transparent=True)
        img.seek(0)
        plt.close(fig)  # Explicitly close the figure

        # Return the image as a response
        return Response(img, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500