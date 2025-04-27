from flask import Blueprint

# Import all blueprints
from .scoreboard_routes import scoreboard_bp
from .boxscore_routes import boxscore_bp
from .play_by_play_routes import play_by_play_bp

# Export blueprints for easy import in app.py
__all__ = ['scoreboard_bp', 'boxscore_bp', 'play_by_play_bp']

# Optional: function to register all blueprints at once
def register_all_blueprints(app):
    """Register all API blueprints with the Flask app"""
    app.register_blueprint(scoreboard_bp, url_prefix='/api/v1')
    app.register_blueprint(boxscore_bp, url_prefix='/api/v1')
    app.register_blueprint(play_by_play_bp, url_prefix='/api/v1')