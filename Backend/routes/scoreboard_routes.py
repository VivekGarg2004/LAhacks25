from flask import Blueprint, jsonify, request
from nba_stats.data.database import MongoDBClient
from nba_stats.api.nba_client import NBAClient
from nba_stats.data.models import ScoreboardData
from datetime import date

scoreboard_bp = Blueprint('scoreboard', __name__)

@scoreboard_bp.route('/scoreboard', methods=['GET'])
def get_scoreboard():
    """Get the latest NBA scoreboard"""
    try:
        # Try to get from database first
        with MongoDBClient() as db_client:
            scoreboard_data = db_client.get(
                obj_id= date.today(),
                obj_class=ScoreboardData,  # Assuming no specific class for scoreboard
                db_name="Scoreboards",
                collection_name="scoreboard"
            )
            # Get fresh data from API
            
            if not scoreboard_data:
                scoreboard_data = NBAClient.get_scoreboard()
                if scoreboard_data:
                    # Save to database for future requests
                    db_client.save(scoreboard_data, "Scoreboards", "scoreboard")
            if not scoreboard_data:
                return jsonify({"error": "Scoreboard data not found"}), 404
            
            return jsonify(scoreboard_data.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500