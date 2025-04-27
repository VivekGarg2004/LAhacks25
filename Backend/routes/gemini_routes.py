from flask import Blueprint, jsonify, request
from nba_stats.data.database import MongoDBClient
from nba_stats.api.nba_client import NBAClient
import requests
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gemini_bp = Blueprint('gemini', __name__)

@gemini_bp.route('/gemini', methods=['POST'])
def ask_gemini():
    """Put in a request, get Gemini response"""
    data = request.get_json()
    
    prompt = data.get('prompt')
    game_id = data.get('game_id')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    if not game_id:
        return jsonify({"error": "Game ID is required for context"}), 400

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

        # Combine user prompt with NBA data as context
        context = (
            f"This is the box score data. It includes the current player stats and team stats at the time of the game.\n"
            f"GAME CONTEXT - BOX SCORE DATA:\n{json.dumps(boxscore_data, indent=2)}\n\n"
            f"This is the play by play data. It includes the last 20 plays that have happened in the game. Use this for time-specific questions, like someone asking what happened two minutes ago.\n"
            f"GAME CONTEXT - PLAY BY PLAY DATA:\n{json.dumps(pbp_data, indent=2)}\n\n"
            f"Given this context, please respond to the following question. Keep the answer concise.\n"
            f"USER QUESTION: {prompt}\n\n"
        )
        logger.info(f"This is the context{context}")

       

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to retrieve NBA data: {str(e)}"}), 500

    # Gemini API Key
    gemini_api_key = os.getenv('GEMINI_API_KEY')

    if not gemini_api_key:
        return jsonify({"error": "GEMINI_API_KEY not set in environment"}), 500
    
    gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"

    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": context + prompt}]
        }]
    }
    print(payload)

    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(gemini_endpoint, json=payload, headers=headers)
        response.raise_for_status()
        gemini_response = response.json()

        reply = gemini_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "")

        return jsonify({"response": reply})
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
