from flask import Blueprint, jsonify, request
from nba_stats.data.database import MongoDBClient
from nba_stats.api.nba_client import NBAClient
from nba_stats.data.models import BoxScoreData

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