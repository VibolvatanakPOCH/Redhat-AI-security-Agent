#!/usr/bin/env python3
"""
RedHat AI Security Agent - Main Application
A sophisticated AI agent for learning and simulating hacking techniques for ethical security testing.
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routes.knowledge_base import knowledge_bp
from routes.attack_engine import attack_bp
from routes.safety_layer import safety_bp
from utils.logger import setup_logging

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Enable CORS for all routes
    CORS(app, origins="*")
    
    # Setup logging
    setup_logging()
    
    # Register blueprints
    app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')
    app.register_blueprint(attack_bp, url_prefix='/api/attack')
    app.register_blueprint(safety_bp, url_prefix='/api/safety')
    
    @app.route('/')
    def index():
        """Root endpoint with API information."""
        return jsonify({
            "name": "RedHat AI Security Agent",
            "version": "1.0.0",
            "description": "AI agent for learning and simulating hacking techniques for ethical security testing",
            "endpoints": {
                "knowledge": "/api/knowledge",
                "attack": "/api/attack", 
                "safety": "/api/safety"
            },
            "status": "operational"
        })
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "timestamp": "2025-01-09T18:30:00Z"
        })
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found"
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({
            "error": "Internal Server Error",
            "message": "An internal error occurred"
        }), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"Starting RedHat AI Security Agent on {host}:{port}")
    app.run(host=host, port=port, debug=app.config['DEBUG'])
