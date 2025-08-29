# utils/auth.py
from functools import wraps
from flask import request, jsonify
import jwt
from config import Config

def require_customer_auth(f):
    """Decorator to require customer authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Login required"}), 401
        
        token = auth_header.split(" ", 1)[1].strip()
        try:
            # Decode token to get customer ID
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            customer_id = payload.get("id")
            if not customer_id:
                return jsonify({"success": False, "error": "Invalid token"}), 401
            
            # Create current_customer context for compatibility
            current_customer = {"id": customer_id}
            
            # Call the function with current_customer
            return f(current_customer, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"success": False, "error": "Authentication failed"}), 401
    
    return decorated_function

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Admin login required"}), 401
        
        token = auth_header.split(" ", 1)[1].strip()
        try:
            # Decode token to get admin ID
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            admin_id = payload.get("id")
            if not admin_id:
                return jsonify({"success": False, "error": "Invalid admin token"}), 401
            
            # Create current_admin context for compatibility
            current_admin = {"id": admin_id}
            
            # Call the function with current_admin
            return f(current_admin, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Admin token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "error": "Invalid admin token"}), 401
        except Exception as e:
            return jsonify({"success": False, "error": "Admin authentication failed"}), 401
    
    return decorated_function
