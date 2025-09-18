# utils/s3_service.py
import boto3
import uuid
from botocore.exceptions import ClientError, NoCredentialsError
from werkzeug.utils import secure_filename
from config import Config
import os

class S3Service:
    def __init__(self):
        """Initialize S3 client with configuration from environment variables only"""
        try:
            # Validate all required environment variables are set
            if not Config.AWS_ACCESS_KEY_ID:
                raise ValueError("❌ AWS_ACCESS_KEY_ID environment variable is required")
            if not Config.AWS_SECRET_ACCESS_KEY:
                raise ValueError("❌ AWS_SECRET_ACCESS_KEY environment variable is required")
            if not Config.AWS_REGION:
                raise ValueError("❌ AWS_REGION environment variable is required")
            if not Config.S3_BUCKET_NAME:
                raise ValueError("❌ S3_BUCKET_NAME environment variable is required")
            
            # Initialize S3 client with environment variables
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_REGION
            )
            
            # Set bucket and folder configurations from environment
            self.bucket_name = Config.S3_BUCKET_NAME
            self.category_folder = Config.S3_CATEGORY_FOLDER
            self.product_folder = Config.S3_PRODUCT_FOLDER
            self.review_folder = Config.S3_REVIEW_FOLDER
            self.widget_folder = Config.S3_WIDGET_FOLDER
            self.video_folder = Config.S3_VIDEO_FOLDER
            self.document_folder = Config.S3_DOCUMENT_FOLDER
            self.delivery_onboarding_folder = "delivery_onboarding/"
            
            # Test S3 connection
            self._test_connection()
            
        except NoCredentialsError:
            raise ValueError("❌ AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file")
        except Exception as e:
            raise ValueError(f"❌ Error initializing S3 client: {str(e)}")
    
    def _test_connection(self):
        """Test S3 connection by listing buckets"""
        try:
            self.s3_client.list_buckets()
            print("✅ S3 connection successful")
        except Exception as e:
            raise ValueError(f"❌ S3 connection failed: {str(e)}. Please check your AWS credentials and region.")

    def upload_file(self, file, file_id, file_type="image", folder_type="category"):
        """
        Upload file to S3 and return the public URL
        
        Args:
            file: File object from request
            file_id: ID of the category/review/etc.
            file_type: Type of file (image, video, document, etc.)
            folder_type: Type of folder (category, product, review, widget, video, document)
        
        Returns:
            str: Public URL of the uploaded file or None if upload failed
        """
        try:
            if not file or not file.filename:
                raise ValueError("❌ No file provided for upload")
            
            # Get folder from environment configuration
            folder = self._get_folder_path(folder_type)
            if not folder:
                raise ValueError(f"❌ Invalid folder type: {folder_type}. Must be one of: category, product, review, widget, video, document")
            
            # Generate unique filename
            file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            unique_filename = f"{file_type}_{file_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
            
            # Create S3 key (path in bucket)
            s3_key = f"{folder}{unique_filename}"
            
            # Reset file pointer to beginning
            file.seek(0)
            
            # Upload file to S3
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': file.content_type or 'application/octet-stream'
                }
            )
            
            # Generate public URL
            public_url = f"https://{self.bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/{s3_key}"
            
            print(f"✅ File uploaded successfully: {public_url}")
            return public_url
            
        except ClientError as e:
            error_msg = f"❌ S3 upload error: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"❌ Upload error: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)
    
    def _get_folder_path(self, folder_type):
        """Get folder path from environment configuration"""
        folder_mapping = {
            "category": self.category_folder,
            "product": self.product_folder,
            "review": self.review_folder,
            "widget": self.widget_folder,
            "video": self.video_folder,
            "document": self.document_folder,
            "delivery_onboarding": self.delivery_onboarding_folder
        }
        return folder_mapping.get(folder_type)

    def upload_product_file(self, file, product_id, color_name=None, file_type="image"):
        """
        Upload product file to S3 with organized folder structure using environment configuration
        
        Args:
            file: File object from request
            product_id: ID of the product
            color_name: Name of the color (optional, for color-specific images)
            file_type: Type of file (image, video, document, etc.)
        
        Returns:
            str: Public URL of the uploaded file or None if upload failed
        """
        try:
            if not file or not file.filename:
                raise ValueError("❌ No file provided for product upload")
            
            if not self.product_folder:
                raise ValueError("❌ S3_PRODUCT_FOLDER environment variable is required for product uploads")
            
            # Generate unique filename
            file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            unique_filename = f"{file_type}_{product_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
            
            # Create organized folder structure using environment configuration
            if color_name:
                # Color-specific image
                folder_path = f"{self.product_folder}{product_id}/{color_name}/"
            else:
                # Main product image
                folder_path = f"{self.product_folder}{product_id}/main/"
            
            s3_key = f"{folder_path}{unique_filename}"
            
            # Reset file pointer to beginning
            file.seek(0)
            
            # Upload file to S3
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': file.content_type or 'application/octet-stream'
                }
            )
            
            # Generate public URL
            public_url = f"https://{self.bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/{s3_key}"
            
            print(f"✅ Product file uploaded successfully: {public_url}")
            return public_url
            
        except ClientError as e:
            error_msg = f"❌ S3 upload error: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"❌ Upload error: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)

    def delete_file(self, file_url):
        """
        Delete file from S3 using the public URL
        
        Args:
            file_url: Public URL of the file to delete
        
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if not file_url:
                return True
            
            # Extract S3 key from URL
            # URL format: https://bucket-name.s3.region.amazonaws.com/folder/filename
            if f"s3.{Config.AWS_REGION}.amazonaws.com/" in file_url:
                s3_key = file_url.split(f"s3.{Config.AWS_REGION}.amazonaws.com/", 1)[1]
            elif f"{self.bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/" in file_url:
                s3_key = file_url.split(f"{self.bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/", 1)[1]
            else:
                print(f"❌ Invalid S3 URL format: {file_url}")
                return False
            
            # Delete file from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            print(f"✅ File deleted successfully: {s3_key}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(f"⚠️ File not found in S3: {file_url}")
                return True  # Consider it successful if file doesn't exist
            print(f"❌ S3 delete error: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Delete error: {str(e)}")
            return False

    def file_exists(self, file_url):
        """
        Check if file exists in S3
        
        Args:
            file_url: Public URL of the file to check
        
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            if not file_url:
                return False
            
            # Extract S3 key from URL
            if f"s3.{Config.AWS_REGION}.amazonaws.com/" in file_url:
                s3_key = file_url.split(f"s3.{Config.AWS_REGION}.amazonaws.com/", 1)[1]
            elif f"{self.bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/" in file_url:
                s3_key = file_url.split(f"{self.bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/", 1)[1]
            else:
                return False
            
            # Check if object exists
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            print(f"❌ S3 check error: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Check error: {str(e)}")
            return False

    def upload_multiple_files(self, files, file_id, folder_type="review"):
        """
        Upload multiple files to S3 and return the public URLs using environment configuration
        
        Args:
            files: List of file objects from request
            file_id: ID of the review/category/etc.
            folder_type: Type of folder (category, product, review, widget, video, document)
        
        Returns:
            dict: Dictionary with 'images' and 'videos' lists containing URLs
        """
        try:
            if not files:
                raise ValueError("❌ No files provided for upload")
            
            image_urls = []
            video_urls = []
            
            # Define file type mappings
            image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            video_extensions = {'mp4', 'webm', 'mov', 'avi'}
            
            for file in files:
                if not file or not file.filename:
                    continue
                    
                # Get file extension
                file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                # Determine if it's an image or video
                if file_extension in image_extensions:
                    file_type_actual = "image"
                elif file_extension in video_extensions:
                    file_type_actual = "video"
                else:
                    print(f"⚠️ Skipping unsupported file type: {file_extension}")
                    continue  # Skip unsupported file types
                
                # Upload file using environment configuration
                s3_url = self.upload_file(file, file_id, file_type_actual, folder_type)
                if s3_url:
                    if file_type_actual == "image":
                        image_urls.append(s3_url)
                    else:
                        video_urls.append(s3_url)
            
            return {
                'images': image_urls,
                'videos': video_urls
            }
            
        except Exception as e:
            error_msg = f"❌ Multiple files upload error: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)

    def get_file_url(self, s3_key):
        """
        Generate public URL for a given S3 key
        
        Args:
            s3_key: S3 object key
        
        Returns:
            str: Public URL
        """
        return f"https://{self.bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/{s3_key}"

# Create a global instance
s3_service = S3Service()
