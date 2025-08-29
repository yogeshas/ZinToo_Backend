# utils/crypto.py
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import json
import os
from flask import current_app

def _normalize_key(secret_str: str):
    key = secret_str.encode("utf-8")
    padded = False
    truncated = False
    if len(key) < 32:
        key = key.ljust(32, b'\0')
        padded = True
    elif len(key) > 32:
        key = key[:32]
        truncated = True
    return key, padded, truncated

def _is_debug_enabled() -> bool:
    try:
        cfg_val = current_app.config.get("CRYPTO_DEBUG")
    except Exception:
        cfg_val = None
    env_val = os.getenv("CRYPTO_DEBUG")
    flag = cfg_val if cfg_val is not None else env_val
    if isinstance(flag, str):
        return flag.lower() in ("1", "true", "yes", "on")
    return bool(flag)

def encrypt_payload(data):
    """Encrypt data using AES-256-CBC with PKCS7 padding"""
    try:
        secret = current_app.config.get("CRYPTO_SECRET", "default_secret")
        key, padded, truncated = _normalize_key(secret)
        debug = _is_debug_enabled()

        json_data = json.dumps(data)
        if debug:
            print(f"[crypto][enc] json_len={len(json_data)} key_len_in={len(secret)} key_len_used={len(key)} padded={padded} truncated={truncated}")

        iv = os.urandom(16)
        if debug:
            print(f"[crypto][enc] iv={iv.hex()}")

        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(json_data.encode('utf-8'), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)

        result = iv + encrypted_data
        base64_result = base64.b64encode(result).decode('utf-8')
        if debug:
            print(f"[crypto][enc] ciphertext_len={len(encrypted_data)} b64_len={len(base64_result)} b64_head={base64_result[:24]}")
        return base64_result
    except Exception as e:
        print(f"❌ Backend encryption failed: {str(e)}")
        raise ValueError(f"Encryption failed: {str(e)}")

def decrypt_payload(encrypted_data):
    """Decrypt data using AES-256-CBC with PKCS7 padding"""
    try:
        secret = current_app.config.get("CRYPTO_SECRET", "default_secret")
        key, padded, truncated = _normalize_key(secret)
        debug = _is_debug_enabled()

        raw_data = base64.b64decode(encrypted_data)
        iv = raw_data[:16]
        ciphertext = raw_data[16:]
        if debug:
            print(f"[crypto][dec] key_len_in={len(secret)} key_len_used={len(key)} padded={padded} truncated={truncated} raw_len={len(raw_data)} iv={iv.hex()} ct_len={len(ciphertext)}")

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(ciphertext)
        decrypted_data = unpad(decrypted_padded, AES.block_size)
        json_data = decrypted_data.decode('utf-8')
        result = json.loads(json_data)
        if debug:
            print(f"[crypto][dec] ok json_len={len(json_data)}")
        return result
    except Exception as e:
        print(f"❌ Backend decryption failed: {str(e)}")
        hint = "Ensure frontend NEXT_PUBLIC_CRYPTO_SECRET equals backend CRYPTO_SECRET and both are exactly 32 ASCII characters."
        raise ValueError(f"Decryption failed: {str(e)}. {hint}")

def hash_password(password):
    """Hash password using bcrypt"""
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    except Exception as e:
        print(f"❌ Password hashing failed: {str(e)}")
        raise ValueError(f"Password hashing failed: {str(e)}")

def verify_password(password, hashed_password):
    """Verify password against hash"""
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, hashed_password)
    except Exception as e:
        print(f"❌ Password verification failed: {str(e)}")
        return False

def generate_secure_token(length=32):
    """Generate secure random token"""
    try:
        return os.urandom(length).hex()
    except Exception as e:
        print(f"❌ Token generation failed: {str(e)}")
        raise ValueError(f"Token generation failed: {str(e)}")

def hash_data(data):
    """Hash data using SHA256"""
    try:
        import hashlib
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"❌ Data hashing failed: {str(e)}")
        raise ValueError(f"Data hashing failed: {str(e)}") 