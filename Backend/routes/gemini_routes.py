from flask import Blueprint, jsonify, request
from nba_stats.data.database import MongoDBClient
from nba_stats.api.nba_client import NBAClient
import requests
import os

gemini_bp = Blueprint('gemini', __name__)

@gemini_bp.route('/gemini', methods=['POST'])
def ask_gemini():
    """Put in a request, get Gemini response"""
    data = request.get_json()
    
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # Use your Gemini API Key
    gemini_api_key = os.getenv('GEMINI_API_KEY')

    if not gemini_api_key:
        return jsonify({"error": "GEMINI_API_KEY not set in environment"}), 500
    gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"

    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }]
    }

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
