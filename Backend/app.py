from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging
from nba_stats.data.database import MongoDBClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Set default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        MONGO_URI=os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    )

    # Apply test config if provided
    if test_config:
        app.config.update(test_config)
    
    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Test database connection on startup
    with app.app_context():
        mongo_client = MongoDBClient(app.config['MONGO_URI'])
        if not mongo_client.connect():
            logger.error("Failed to connect to MongoDB on startup!")
        else:
            mongo_client.close()
            logger.info("Successfully connected to MongoDB")

    # Register blueprints for API routes
    from routes.scoreboard_routes import scoreboard_bp
    from routes.boxscore_routes import boxscore_bp
    from routes.play_by_play_routes import play_by_play_bp
    from routes.graph_routes import graph_bp
    from routes.gemini_routes import gemini_bp
    from routes.play_by_play_image_route import play_by_play_image_bp
    
    app.register_blueprint(scoreboard_bp, url_prefix='/api/v1')
    app.register_blueprint(boxscore_bp, url_prefix='/api/v1')
    app.register_blueprint(play_by_play_bp, url_prefix='/api/v1')
    app.register_blueprint(graph_bp, url_prefix='/api/v1')
    app.register_blueprint(gemini_bp, url_prefix='/api/v1')
    app.register_blueprint(play_by_play_image_bp, url_prefix='/api/v1')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        mongo_client = MongoDBClient(app.config['MONGO_URI'])
        health_status = {
            "status": "ok",
            "database": "connected" if mongo_client.connect() else "disconnected"
        }
        mongo_client.close()
        return jsonify(health_status)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))