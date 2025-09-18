import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # Flask secret (JWT signing, sessions, etc.)
    SECRET_KEY = os.getenv("SECRET_KEY", "4e8f3d1c90b2a6d73a7f8b19c4d2f50a")

    # AES encryption key (must match frontend VITE_CRYPTO_SECRET)
    CRYPTO_SECRET = os.getenv("CRYPTO_SECRET", "my_super_secret_key_32chars!!")
    
    # MySQL connection (adjust your .env accordingly)
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "mydatabase")

    # URL encode the password to handle special characters
    from urllib.parse import quote_plus
    encoded_password = quote_plus(DB_PASSWORD)
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://{DB_USER}:{encoded_password}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "yogeshas12345665@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "wfcqecjlqjjcsiya")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "hatchybyte@gmail.com")
    
    # Google OAuth configuration
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    
    # AWS S3 configuration - All required from environment
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    S3_CATEGORY_FOLDER = os.getenv("S3_CATEGORY_FOLDER")
    S3_PRODUCT_FOLDER = os.getenv("S3_PRODUCT_FOLDER")
    S3_REVIEW_FOLDER = os.getenv("S3_REVIEW_FOLDER")
    S3_WIDGET_FOLDER = os.getenv("S3_WIDGET_FOLDER")
    S3_VIDEO_FOLDER = os.getenv("S3_VIDEO_FOLDER")
    S3_DOCUMENT_FOLDER = os.getenv("S3_DOCUMENT_FOLDER")
    
    # AWS SNS configuration for push notifications
    SNS_APPLICATION_ARN_ANDROID = os.getenv("SNS_APPLICATION_ARN_ANDROID")
    SNS_APPLICATION_ARN_IOS = os.getenv("SNS_APPLICATION_ARN_IOS")
    FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")  # For direct FCM integration
    FCM_SERVICE_ACCOUNT_PATH = os.getenv("FCM_SERVICE_ACCOUNT_PATH")  # For Firebase Admin SDK
    
    # Validate required S3 environment variables
    required_s3_vars = {
        "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
        "AWS_REGION": AWS_REGION,
        "S3_BUCKET_NAME": S3_BUCKET_NAME,
        "S3_CATEGORY_FOLDER": S3_CATEGORY_FOLDER,
        "S3_PRODUCT_FOLDER": S3_PRODUCT_FOLDER,
        "S3_REVIEW_FOLDER": S3_REVIEW_FOLDER,
        "S3_WIDGET_FOLDER": S3_WIDGET_FOLDER,
        "S3_VIDEO_FOLDER": S3_VIDEO_FOLDER,
        "S3_DOCUMENT_FOLDER": S3_DOCUMENT_FOLDER
    }
    
    missing_vars = [var for var, value in required_s3_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"❌ Missing required S3 environment variables: {', '.join(missing_vars)}. Please set all S3 configuration variables in your .env file.")