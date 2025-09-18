# routes/barcode_verification.py
from flask import Blueprint, request, jsonify
from models.order import Order
from models.delivery_track import DeliveryTrack
from extensions import db
from datetime import datetime
import json
import io
from PIL import Image
try:
    import cv2
except ImportError:
    cv2 = None
try:
    import numpy as np
except ImportError:
    np = None
try:
    from pyzbar import pyzbar
except ImportError:
    pyzbar = None

try:
    import zxingcpp
except ImportError:
    zxingcpp = None

barcode_verification_bp = Blueprint("barcode_verification", __name__)

def require_delivery_auth(f):
    """Decorator to require delivery guy authentication"""
    from functools import wraps
    from services.delivery_auth_service import verify_auth_token
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"success": False, "error": "No authorization header"}), 401
        
        try:
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
            result = verify_auth_token(token)
            if not result or not result.get("success"):
                return jsonify({"success": False, "error": "Invalid token"}), 401
            
            # Extract the user from the result
            delivery_guy = result.get("user", {})
            return f(delivery_guy, *args, **kwargs)
        except Exception as e:
            print(f"Auth error: {str(e)}")
            return jsonify({"success": False, "error": "Authentication failed"}), 401
    
    return decorated_function

@barcode_verification_bp.route("/verify-barcode", methods=["POST"])
@require_delivery_auth
def verify_barcode(current_delivery_guy):
    """Verify barcode from captured image"""
    try:
        print(f"Barcode verification request from delivery guy: {current_delivery_guy.get('id', 'unknown') if isinstance(current_delivery_guy, dict) else getattr(current_delivery_guy, 'id', 'unknown')}")
        
        if 'image' not in request.files:
            print("No image provided in request")
            return jsonify({"success": False, "error": "No image provided"}), 400
        
        image_file = request.files['image']
        expected_barcode = request.form.get('expected_barcode')
        
        print(f"Expected barcode: {expected_barcode}")
        
        if not expected_barcode:
            print("No expected barcode provided")
            return jsonify({"success": False, "error": "Expected barcode not provided"}), 400
        
        if image_file.filename == '':
            print("Empty image filename")
            return jsonify({"success": False, "error": "No image selected"}), 400
        
        # Read image
        image_data = image_file.read()
        print(f"Image size: {len(image_data)} bytes")
        
        image = Image.open(io.BytesIO(image_data))
        print(f"Image mode: {image.mode}, size: {image.size}")
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Check if required libraries are available
        if cv2 is None:
            print("OpenCV not available - barcode verification cannot proceed")
            return jsonify({
                "success": False,
                "verified": False,
                "error": "Barcode verification requires OpenCV library. Please contact administrator."
            }), 500
        
        if np is None:
            print("NumPy not available - barcode verification cannot proceed")
            return jsonify({
                "success": False,
                "verified": False,
                "error": "Barcode verification requires NumPy library. Please contact administrator."
            }), 500
        
        if pyzbar is None and zxingcpp is None:
            print("Neither pyzbar nor zxing-cpp available - barcode verification cannot proceed")
            return jsonify({
                "success": False,
                "verified": False,
                "error": "Barcode verification requires either pyzbar or zxing-cpp library. Please contact administrator."
            }), 500
        
        # Convert PIL image to numpy array for OpenCV
        try:
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            print("Image converted to OpenCV format")
            
            # Simple barcode detection like your example
            def simple_barcode_reader(img):
                """Simple barcode reader based on your example"""
                barcodes = []
                
                # Try pyzbar first (simple approach)
                if pyzbar is not None:
                    detected_barcodes = pyzbar.decode(img)
                    print(f"🔍 Simple pyzbar detection: {len(detected_barcodes)} barcodes")
                    
                    for barcode in detected_barcodes:
                        if barcode.data != "":
                            barcode_data = barcode.data.decode('utf-8')
                            barcode_type = barcode.type
                            print(f"📋 Detected: {barcode_data} (Type: {barcode_type})")
                            barcodes.append({
                                'data': barcode_data,
                                'type': barcode_type
                            })
                
                # If no barcodes found, try zxing-cpp
                if not barcodes and zxingcpp is not None:
                    print("🔍 Trying zxing-cpp...")
                    try:
                        results = zxingcpp.read_barcodes(img)
                        print(f"🔍 ZXing detection: {len(results)} barcodes")
                        
                        for result in results:
                            barcode_data = result.text
                            barcode_type = str(result.format)
                            print(f"📋 ZXing: {barcode_data} (Type: {barcode_type})")
                            barcodes.append({
                                'data': barcode_data,
                                'type': barcode_type
                            })
                    except Exception as e:
                        print(f"🔍 ZXing error: {e}")
                
                return barcodes
            
            # Use simple detection
            detected_barcodes = simple_barcode_reader(opencv_image)
            print(f"🔍 Total barcodes found: {len(detected_barcodes)}")
            
            if detected_barcodes:
                for barcode in detected_barcodes:
                    barcode_data = barcode['data']
                    barcode_type = barcode['type']
                    
                    print(f"Detected barcode: {barcode_data} (Type: {barcode_type})")
                    
                    # Check if barcode matches expected
                    if barcode_data == expected_barcode:
                        print("Barcode matches expected!")
                        return jsonify({
                            "success": True,
                            "verified": True,
                            "message": "Barcode verified successfully",
                            "detected_barcode": barcode_data,
                            "barcode_type": barcode_type
                        })
                
                # If we found barcodes but none matched
                detected_barcodes_list = [b['data'] for b in detected_barcodes]
                print(f"Barcodes found but none matched. Expected: {expected_barcode}, Detected: {detected_barcodes_list}")
                return jsonify({
                    "success": True,
                    "verified": False,
                    "message": f"Barcode detected but doesn't match. Expected: {expected_barcode}, Detected: {detected_barcodes_list}",
                    "detected_barcodes": detected_barcodes_list
                })
            else:
                print("No barcodes detected in image")
                return jsonify({
                    "success": True,
                    "verified": False,
                    "message": "No barcode detected in image"
                })
                
        except Exception as cv_error:
            print(f"OpenCV processing error: {str(cv_error)}")
            return jsonify({
                "success": False,
                "verified": False,
                "error": f"Barcode verification failed due to processing error: {str(cv_error)}"
            })
            
    except Exception as e:
        print(f"Barcode verification error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500

@barcode_verification_bp.route("/test", methods=["GET"])
def test_barcode_verification():
    """Test endpoint to check if barcode verification is working"""
    try:
        return jsonify({
            "success": True,
            "message": "Barcode verification endpoint is working",
            "libraries": {
                "opencv": cv2 is not None,
                "numpy": np is not None,
                "pyzbar": pyzbar is not None,
                "zxingcpp": zxingcpp is not None
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@barcode_verification_bp.route("/<int:order_id>/status", methods=["PUT"])
@require_delivery_auth
def update_delivery_status(current_delivery_guy, order_id):
    """Update delivery status after verification"""
    try:
        print(f"Status update request for order {order_id}")
        data = request.get_json()
        print(f"Request data: {data}")
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        new_status = data.get('status')
        notes = data.get('notes', '')
        verified = data.get('verified', False)
        
        print(f"New status: {new_status}, Notes: {notes}, Verified: {verified}")
        
        if not new_status:
            return jsonify({"success": False, "error": "Status not provided"}), 400
        
        # Find the order
        print(f"Looking for order with ID: {order_id}")
        order = Order.query.get(order_id)
        if not order:
            print(f"Order {order_id} not found")
            return jsonify({"success": False, "error": "Order not found"}), 404
        
        print(f"Found order: {order.id}, current status: {order.status}")
        
        # Update order status
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        # Get delivery guy ID safely
        delivery_guy_id = current_delivery_guy.get('id') if isinstance(current_delivery_guy, dict) else getattr(current_delivery_guy, 'id', None)
        
        # Debug: Print the current_delivery_guy structure
        print(f"Current delivery guy structure: {current_delivery_guy}")
        print(f"Type: {type(current_delivery_guy)}")
        
        # If still None, try alternative field names
        if delivery_guy_id is None:
            if isinstance(current_delivery_guy, dict):
                delivery_guy_id = current_delivery_guy.get('delivery_guy_id') or current_delivery_guy.get('user_id') or current_delivery_guy.get('id')
            else:
                delivery_guy_id = getattr(current_delivery_guy, 'delivery_guy_id', None) or getattr(current_delivery_guy, 'user_id', None) or getattr(current_delivery_guy, 'id', None)
        
        print(f"Final delivery_guy_id: {delivery_guy_id}")
        
        # If still None, we need to handle this case
        if delivery_guy_id is None:
            print("Warning: Could not extract delivery guy ID, using placeholder")
            delivery_guy_id = 1  # Use a default delivery guy ID or handle this differently
        
        # Add verification note
        if verified:
            verification_note = f"Verified by delivery guy {delivery_guy_id} at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            if notes:
                notes = f"{notes}\n{verification_note}"
            else:
                notes = verification_note
        
        # Create delivery track entry
        print(f"Creating delivery track entry for order {order_id}, delivery guy {delivery_guy_id}")
        track_entry = DeliveryTrack(
            order_id=order_id,
            delivery_guy_id=delivery_guy_id,
            status=new_status,
            notes=notes,
            created_at=datetime.utcnow()
        )
        
        print(f"Adding track entry to database session")
        db.session.add(track_entry)
        
        print(f"Committing database changes")
        db.session.commit()
        
        print(f"Status update successful for order {order_id}")
        return jsonify({
            "success": True,
            "message": "Delivery status updated successfully",
            "order_id": order_id,
            "new_status": new_status,
            "verified": verified
        })
        
    except Exception as e:
        print(f"Update delivery status error: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": "Internal server error"}), 500

@barcode_verification_bp.route('/detect-barcode', methods=['POST'])
@require_delivery_auth
def detect_barcode(current_delivery_guy):
    """Detect barcode from image without verification"""
    try:
        print("🔍 Starting barcode detection...")
        
        # Check if image is provided
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image provided'
            }), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No image selected'
            }), 400
        
        print(f"📸 Processing image: {image_file.filename}")
        print(f"📸 Image content type: {image_file.content_type}")
        
        # Read image data
        image_data = image_file.read()
        print(f"📊 Image size: {len(image_data)} bytes")
        print(f"📊 First 100 bytes: {image_data[:100]}")
        
        # Convert to PIL Image
        from PIL import Image
        import io
        
        pil_image = Image.open(io.BytesIO(image_data))
        print(f"🖼️ Image dimensions: {pil_image.size}")
        
        # Try to detect barcodes
        detected_barcodes = []
        
        try:
            import cv2
            import numpy as np
            from pyzbar import pyzbar
            
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Save debug image with timestamp
            try:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_filename = f'/tmp/debug_barcode_{timestamp}.jpg'
                cv2.imwrite(debug_filename, opencv_image)
                print(f"🔍 Debug: Saved image to {debug_filename} for inspection")
            except Exception as e:
                print(f"🔍 Debug: Could not save image: {e}")
            
            # Simple barcode detection like your example
            def simple_barcode_reader(img):
                """Simple barcode reader based on your example"""
                barcodes = []
                
                # Try pyzbar first (simple approach)
                if pyzbar is not None:
                    detected_barcodes = pyzbar.decode(img)
                    print(f"🔍 Simple pyzbar detection: {len(detected_barcodes)} barcodes")
                    
                    for barcode in detected_barcodes:
                        if barcode.data != "":
                            barcode_data = barcode.data.decode('utf-8')
                            barcode_type = barcode.type
                            print(f"📋 Detected: {barcode_data} (Type: {barcode_type})")
                            barcodes.append({
                                'data': barcode_data,
                                'type': barcode_type
                            })
                
                # If no barcodes found, try zxing-cpp
                if not barcodes and zxingcpp is not None:
                    print("🔍 Trying zxing-cpp...")
                    try:
                        results = zxingcpp.read_barcodes(img)
                        print(f"🔍 ZXing detection: {len(results)} barcodes")
                        
                        for result in results:
                            barcode_data = result.text
                            barcode_type = str(result.format)
                            print(f"📋 ZXing: {barcode_data} (Type: {barcode_type})")
                            barcodes.append({
                                'data': barcode_data,
                                'type': barcode_type
                            })
                    except Exception as e:
                        print(f"🔍 ZXing error: {e}")
                
                return barcodes
            
            # Use simple detection
            processed_barcodes = simple_barcode_reader(opencv_image)
            print(f"🔍 Total barcodes found: {len(processed_barcodes)}")
                
        except ImportError as e:
            print(f"❌ Library import error: {e}")
            return jsonify({
                'success': False,
                'error': f'Required libraries not available: {str(e)}'
            }), 500
        except Exception as e:
            print(f"❌ Barcode detection error: {e}")
            return jsonify({
                'success': False,
                'error': f'Barcode detection failed: {str(e)}'
            }), 500
        
        if processed_barcodes:
            # Return the first detected barcode
            detected_barcode = processed_barcodes[0]['data']
            print(f"✅ Detected barcode: {detected_barcode}")
            
            return jsonify({
                'success': True,
                'detected_barcode': detected_barcode,
                'barcode_type': processed_barcodes[0]['type'],
                'total_detected': len(processed_barcodes),
                'message': f'Barcode detected: {detected_barcode}'
            })
        else:
            print("❌ No barcodes detected")
            print("🔍 Debug: Supported barcode types: QRCODE, CODE128, CODE39, EAN13, EAN8, UPC_A, UPC_E, ITF, PDF417, DATAMATRIX")
            return jsonify({
                'success': False,
                'detected_barcode': None,
                'error': 'No barcodes detected. Please ensure:\n1. Barcode is fully visible in frame\n2. Good lighting conditions\n3. Barcode is not blurry or damaged\n4. Try different angles or distances\n5. Supported formats: QR, CODE128, CODE39, EAN13, EAN8, UPC'
            }), 400
            
    except Exception as e:
        print(f"❌ Detection endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': f'Detection failed: {str(e)}'
        }), 500
