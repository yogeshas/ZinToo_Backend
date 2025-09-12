from flask import Blueprint, request, jsonify, redirect, current_app
from services.customer_service import get_customer_by_email, create_customer
from utils.crypto import encrypt_payload, decrypt_payload
from config import Config
import jwt
import requests
from datetime import datetime, timedelta
import os

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/google", methods=["GET"])
def google_login():
    """Initiate Google OAuth login"""
    try:
        # Google OAuth URL
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={Config.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={Config.GOOGLE_REDIRECT_URI}&"
            "response_type=code&"
            "scope=openid email profile&"
            "access_type=offline"
        )
        
        return jsonify({
            "success": True,
            "auth_url": google_auth_url
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to generate Google auth URL: {str(e)}"
        }), 500

@auth_bp.route("/google/callback", methods=["GET"])
@auth_bp.route("/oauth2callback", methods=["GET"])  # Add support for the Google Console redirect URI
def google_callback():
    """Handle Google OAuth callback"""
    try:
        code = request.args.get("code")
        if not code:
            return jsonify({
                "success": False,
                "error": "Authorization code not provided"
            }), 400
        
        # Exchange code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": Config.GOOGLE_CLIENT_ID,
            "client_secret": Config.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": Config.GOOGLE_REDIRECT_URI
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_json = token_response.json()
        
        access_token = token_json.get("access_token")
        if not access_token:
            return jsonify({
                "success": False,
                "error": "Failed to get access token"
            }), 400
        
        # Get user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(user_info_url, headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()
        
        email = user_info.get("email")
        name = user_info.get("name", "")
        google_id = user_info.get("id")
        
        if not email:
            return jsonify({
                "success": False,
                "error": "Email not provided by Google"
            }), 400
        
        # Check if user exists
        customer = get_customer_by_email(email)
        
        if not customer:
            # User doesn't exist, ask them to register first
            return jsonify({
                "success": False,
                "error": "Account not found. Please register first.",
                "email": email,
                "name": name,
                "google_id": google_id
            }), 404
        
        # User exists, create JWT token
        payload = {
            "id": customer.id,
            "username": customer.username,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        secret_key = current_app.config.get("SECRET_KEY") or "dev-secret-key"
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Encrypt the response
        response_data = {
            "token": token,
            "user": customer.as_dict()
        }
        enc = encrypt_payload(response_data)
        
        return jsonify({
            "success": True,
            "encrypted_data": enc
        })
        
    except requests.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"Google API error: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Authentication failed: {str(e)}"
        }), 500

@auth_bp.route("/google/register", methods=["POST"])
def google_register():
    """Register user with Google OAuth data"""
    encrypted = request.json.get("data")
    try:
        data = decrypt_payload(encrypted)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    
    email = data.get("email")
    name = data.get("name", "")
    google_id = data.get("google_id")
    
    if not email:
        return jsonify({"success": False, "error": "Email is required"}), 400
    
    # Check if user already exists
    if get_customer_by_email(email):
        return jsonify({"success": False, "error": "Email already registered"}), 409
    
    try:
        # Create customer with Google OAuth data
        customer_data = {
            "username": email.split("@")[0],  # Use email prefix as username
            "email": email,
            "password": jwt.encode({"google_oauth": True, "google_id": google_id}, 
                                 current_app.config.get("SECRET_KEY"), algorithm="HS256"),
            "status": "active",
            "google_id": google_id,
            "name": name
        }
        
        customer = create_customer(customer_data)
        
        # Create JWT token
        payload = {
            "id": customer.id,
            "username": customer.username,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        secret_key = current_app.config.get("SECRET_KEY") or "dev-secret-key"
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Encrypt the response
        response_data = {
            "token": token,
            "user": customer.as_dict()
        }
        enc = encrypt_payload(response_data)
        
        return jsonify({
            "success": True,
            "encrypted_data": enc
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Registration failed: {str(e)}"
        }), 500
