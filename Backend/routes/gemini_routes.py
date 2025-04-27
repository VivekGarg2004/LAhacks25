from flask import Blueprint, jsonify, request
from nba_stats.data.database import MongoDBClient
from nba_stats.api.nba_client import NBAClient
import requests
import os
import json
import logging
import math
import numpy as np
import dotenv
dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None  # Convert NaN and Infinity to null
        elif isinstance(obj, np.ndarray):
            return obj.tolist()  # Convert numpy arrays to lists
        elif isinstance(obj, np.integer):
            return int(obj)  # Convert numpy integers to Python int
        elif isinstance(obj, np.floating):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return float(obj)  # Convert numpy floats to Python float
        return super(CustomJSONEncoder, self).default(obj)



gemini_bp = Blueprint('gemini', __name__)
@gemini_bp.route('/gemini', methods=['POST'])
def ask_gemini():
    """Put in a request, get Gemini response"""
    data = request.get_json()
    logger.info(f"Received request data: {data}")
    live_scoreboard = NBAClient.get_scoreboard()
    games = live_scoreboard.games
    active_game_ids = [
        game['gameId']
        for game in games
        if game.get('gameStatus', 0) == 2  # 2 = Live
    ]
    game_id = active_game_ids[0] if active_game_ids else "0042400153"
    conversation_history = data.get('contents')
    logger.info(f"Conversation history: {conversation_history}")
    generation_config = data.get('generation_config')
    
    try:
        base_url = "http://127.0.0.1:3000/api/v1"

        # Get box score data
        boxscore_response = requests.get(f"{base_url}/boxscore/{game_id}")
        boxscore_response.raise_for_status()
        boxscore_data = boxscore_response.json()
        
        # Get play-by-play data
        pbp_response = requests.get(f"{base_url}/play-by-play/{game_id}")
        pbp_response.raise_for_status()
        pbp_data = pbp_response.json()

        # Gemini API Key
        gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not gemini_api_key:
            return jsonify({"error": "GEMINI_API_KEY not set in environment"}), 500
        
        gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"

        # Create a system message with context
        # Create a simple text variable with context information
        context_text = f"You are a sports analyst. You have access to live NBA game data. The current game ID is {game_id}. " \
                    f"Box score data: {json.dumps(boxscore_data, indent=2, cls=CustomJSONEncoder)}. " \
                    f"Play-by-play data: {json.dumps(pbp_data, indent=2, cls=CustomJSONEncoder)}."
        
        
        # append the context to the start of data['contents']
        contents = data.get('contents', [])

        parts = contents[0].get('parts', [])
        parts.insert(0, {
            "text": context_text
        })

        contents[0]['parts'] = parts

        #contents.append(context_message)
                # Simple test payload that follows Gemini API format exactly
        logger.info(f"Contents for Gemini API: {json.dumps(contents, indent=2, cls=CustomJSONEncoder)}")
        payload = {
            "contents": contents,
            
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 300
            }
        }

        # logger.info(f"Payload for Gemini API: {json.dumps(payload, indent=2, cls=CustomJSONEncoder)}")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add better error logging
        
        response = requests.post(gemini_endpoint, json=payload, headers=headers)
        logger.info(f"Gemini API status code: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Gemini API error response: {response.text}")
        response.raise_for_status()
        gemini_response = response.json()
        
        # Extract text from the response
        reply = gemini_response
        
        return reply
        
    except requests.exceptions.RequestException as e:
            logger.error(f"Request to Gemini API failed: {e}")
            return jsonify({"error": f"Failed to retrieve data or process request: {str(e)}"}), 500