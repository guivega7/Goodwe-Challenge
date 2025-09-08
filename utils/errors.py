"""
Error handling utilities for Flask application.

This module provides centralized error handling for HTTP errors
and application exceptions.
"""

from flask import Flask, render_template, jsonify, request
from typing import Tuple, Union


def init_error_handlers(app: Flask) -> None:
    """
    Initialize error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request_error(error) -> Tuple[Union[str, dict], int]:
        """Handle 400 Bad Request errors."""
        if request.is_json:
            return jsonify({
                'error': 'Bad Request',
                'message': 'The request could not be understood by the server.'
            }), 400
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized_error(error) -> Tuple[Union[str, dict], int]:
        """Handle 401 Unauthorized errors."""
        if request.is_json:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required.'
            }), 401
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden_error(error) -> Tuple[Union[str, dict], int]:
        """Handle 403 Forbidden errors."""
        if request.is_json:
            return jsonify({
                'error': 'Forbidden',
                'message': 'Access denied.'
            }), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error) -> Tuple[Union[str, dict], int]:
        """Handle 404 Not Found errors."""
        if request.is_json:
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found.'
            }), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error) -> Tuple[Union[str, dict], int]:
        """Handle 500 Internal Server errors."""
        if request.is_json:
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred.'
            }), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(503)
    def service_unavailable_error(error) -> Tuple[Union[str, dict], int]:
        """Handle 503 Service Unavailable errors."""
        if request.is_json:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'The service is temporarily unavailable.'
            }), 503
        return render_template('errors/503.html'), 503