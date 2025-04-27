from flask import Blueprint, jsonify, request
from nba_stats.data.database import MongoDBClient
from nba_stats.api.nba_client import NBAClient

scoreboard_bp = Blueprint('scoreboard', __name__)

@scoreboard_bp.route('/scoreboard', methods=['GET'])
def get_scoreboard():
    """Get the latest NBA scoreboard"""
    try:
        # Try to get from database first
        with MongoDBClient() as db_client:
            # Get fresh data from API
            scoreboard_data = NBAClient.get_scoreboard()
            if not scoreboard_data:
                return jsonify({"error": "Unable to fetch scoreboard data"}), 500
            
            # Return the data
            return jsonify({
                "games": scoreboard_data.games,
                "game_date": scoreboard_data.game_date
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500