from nba_api.stats.endpoints import BoxScoreTraditionalV2
import json

# Construct box score from play by play

box_score = BoxScoreTraditionalV2(game_id="0052000121", start_range=0, end_range=7200, range_type=2)
data = box_score.get_dict()

headers = data["resultSets"][0]["headers"]
rows = data["resultSets"][0]["rowSet"]

player_stats = [dict(zip(headers, row)) for row in rows]

print(json.dumps(player_stats, indent=4))