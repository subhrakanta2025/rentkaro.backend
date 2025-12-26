"""
Utilities for Flask application
"""

from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify

def admin_required(fn):
    """Decorator to check if user is admin"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

def agency_required(fn):
    """Decorator to check if user is agency"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') not in ['agency', 'admin']:
            return jsonify({'error': 'Agency access required'}), 403
        return fn(*args, **kwargs)
    return wrapper
