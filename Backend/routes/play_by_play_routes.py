from flask import Blueprint, jsonify, request
from nba_stats.data.database import MongoDBClient
from nba_stats.api.nba_client import NBAClient
from nba_stats.data.models import PlayByPlayData

play_by_play_bp = Blueprint('play_by_play', __name__)

@play_by_play_bp.route('/play-by-play/<game_id>', methods=['GET'])
def get_play_by_play(game_id):
    """Get play-by-play data for a specific game"""
    try:

        # First try to get from database
        with MongoDBClient() as db_client:
            play_by_play_data = db_client.get(
                obj_id=game_id,
                obj_class=PlayByPlayData,
                db_name="PlayByPlay",
                collection_name="play_by_play"
            )
            
            # If not in database, fetch from API
            if not play_by_play_data:
                play_by_play_data = NBAClient.get_live_play_by_play(game_id)
                if play_by_play_data:
                    # Save to database for future requests
                    db_client.save(play_by_play_data, "PlayByPlay", "play_by_play")
            
            if not play_by_play_data:
                return jsonify({"error": "Play-by-play data not found"}), 404
            
            plays = play_by_play_data.plays
            limit = request.args.get('limit', default=len(plays), type=int)
            limit = min(limit, len(plays))

            last_plays = plays[-limit:]

            redundant_fields = ['x', 'y', 'xLegacy', 'yLegacy', 'otherField', 'edited', 'isFieldGoal', 
                                'isTargetScoreLastPeriod', 'orderNumber', 'personId', 'personIdsFilter', 
                                'playerName', 'qualifiers', 'assistPersonId', 'descriptor', 'shotResult', 
                                'subType', 'officialId', 'foulDrawnPersonId', 'foulPersonalTotal', 'foulTechnicalTotal', 
                                'periodType', 'reboundDefensiveTotal', 'reboundOffensiveTotal', 'shotActionNumber', 
                                'assistPlayerNameInitial', 'assistTotal', 'playerNameI', 'pointsTotal', 'turnoverTotal']

            filtered_plays = []
            for play in last_plays:
                filtered_play = {field: play.get(field, None) for field in play if field not in redundant_fields}
                filtered_plays.append(filtered_play)

            # Return the last 30 plays
            return jsonify({"last_plays": filtered_plays})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500