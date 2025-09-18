import os
import io
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import base64

def generate_delivery_barcode_image(barcode_text, product_name=None, product_id=None):
    """
    Generate a high-quality barcode image optimized for delivery personnel scanning
    
    Args:
        barcode_text (str): The barcode text to encode
        product_name (str, optional): Product name to display
        product_id (int, optional): Product ID to display
    
    Returns:
        str: Base64 encoded image data
    """
    try:
        # Create barcode with delivery-optimized settings
        barcode = Code128(barcode_text, writer=ImageWriter())
        
        # Generate barcode image with maximum scanning quality
        barcode_buffer = io.BytesIO()
        barcode.write(barcode_buffer, options={
            'module_width': 0.6,  # Slightly smaller bars to fit better
            'module_height': 20.0,  # Shorter bars to leave room for text
            'quiet_zone': 6.0,  # Smaller quiet zone
            'font_size': 12,  # Smaller font for barcode
            'text_distance': 5.0,  # Less space between barcode and text
            'background': 'white',
            'foreground': 'black',
            'write_text': False,  # Don't write text in barcode, we'll add it separately
            'center_text': True,
            'dpi': 300,  # High DPI for crisp printing
        })
        
        # Open the barcode image
        barcode_image = Image.open(barcode_buffer)
        
        # Create a larger canvas for the delivery sticker
        sticker_width = 500
        sticker_height = 300
        sticker = Image.new('RGB', (sticker_width, sticker_height), 'white')
        
        # Calculate positions - leave more room for text below
        barcode_width, barcode_height = barcode_image.size
        barcode_x = (sticker_width - barcode_width) // 2
        barcode_y = 20  # Start higher to leave room for text below
        
        # Paste barcode onto sticker
        sticker.paste(barcode_image, (barcode_x, barcode_y))
        
        # Add text with better fonts
        draw = ImageDraw.Draw(sticker)
        
        # Try to use better fonts for delivery scanning
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
            font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
        except:
            try:
                font_large = ImageFont.truetype("arial.ttf", 24)
                font_medium = ImageFont.truetype("arial.ttf", 18)
                font_small = ImageFont.truetype("arial.ttf", 14)
            except:
                try:
                    # Try DejaVu Sans font (common on Linux)
                    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                    font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
                except:
                    try:
                        # Try Liberation Sans font
                        font_large = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 24)
                        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 18)
                        font_small = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 14)
                    except:
                        # Use default font with larger size
                        font_large = ImageFont.load_default()
                        font_medium = ImageFont.load_default()
                        font_small = ImageFont.load_default()
        
        # Add company name at top with delivery branding
        company_text = "ZinToo Delivery"
        if font_large:
            company_bbox = draw.textbbox((0, 0), company_text, font=font_large)
            company_width = company_bbox[2] - company_bbox[0]
            company_x = (sticker_width - company_width) // 2
            draw.text((company_x, 5), company_text, fill='black', font=font_large)
        
        # Add barcode number below barcode with better visibility
        barcode_number_y = barcode_y + barcode_height + 15
        
        # Make sure the text fits within the image bounds
        if barcode_number_y > sticker_height - 30:
            barcode_number_y = sticker_height - 30
        
        if font_medium:
            barcode_bbox = draw.textbbox((0, 0), barcode_text, font=font_medium)
            barcode_text_width = barcode_bbox[2] - barcode_bbox[0]
            barcode_text_x = (sticker_width - barcode_text_width) // 2
            draw.text((barcode_text_x, barcode_number_y), barcode_text, fill='black', font=font_medium)
        else:
            # Fallback: draw text without font
            draw.text((sticker_width//2, barcode_number_y), barcode_text, fill='black')
        
        # Add product info if provided
        y_offset = barcode_number_y + 30
        
        if product_name and font_small:
            # Truncate product name if too long
            display_name = product_name[:30] + "..." if len(product_name) > 30 else product_name
            name_bbox = draw.textbbox((0, 0), display_name, font=font_small)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = (sticker_width - name_width) // 2
            draw.text((name_x, y_offset), display_name, fill='black', font=font_small)
            y_offset += 25
        
        if product_id and font_small:
            id_text = f"Product ID: {product_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=font_small)
            id_width = id_bbox[2] - id_bbox[0]
            id_x = (sticker_width - id_width) // 2
            draw.text((id_x, y_offset), id_text, fill='black', font=font_small)
            y_offset += 25
        
        # Add delivery instructions
        if font_small:
            delivery_text = "SCAN FOR DELIVERY"
            delivery_bbox = draw.textbbox((0, 0), delivery_text, font=font_small)
            delivery_width = delivery_bbox[2] - delivery_bbox[0]
            delivery_x = (sticker_width - delivery_width) // 2
            draw.text((delivery_x, y_offset), delivery_text, fill='red', font=font_small)
        
        # Add border for better visibility
        draw.rectangle([0, 0, sticker_width-1, sticker_height-1], outline='black', width=2)
        
        # Convert to base64
        output_buffer = io.BytesIO()
        sticker.save(output_buffer, format='PNG', dpi=(300, 300))
        output_buffer.seek(0)
        
        # Encode as base64
        image_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{image_base64}"
        
    except Exception as e:
        print(f"Error generating delivery barcode image: {str(e)}")
        return None

def generate_delivery_barcode_sticker_html(barcode_text, product_name=None, product_id=None):
    """
    Generate HTML for printing delivery barcode stickers
    
    Args:
        barcode_text (str): The barcode text
        product_name (str, optional): Product name
        product_id (int, optional): Product ID
    
    Returns:
        str: HTML content for printing
    """
    image_data = generate_delivery_barcode_image(barcode_text, product_name, product_id)
    
    if not image_data:
        return "<p>Error generating delivery barcode image</p>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Delivery Barcode Sticker - {barcode_text}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                box-sizing: border-box;
            }}
            
            @media print {{
                @page {{
                    size: 5in 3in;
                    margin: 0.05in;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    background: white;
                }}
                .no-print {{
                    display: none !important;
                }}
                .sticker {{
                    width: 4.9in;
                    height: 2.9in;
                    border: 2px solid #000;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    page-break-inside: avoid;
                    background: white;
                }}
                .barcode-image {{
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                    image-rendering: -webkit-optimize-contrast;
                    image-rendering: crisp-edges;
                }}
            }}
            
            body {{
                margin: 20px;
                font-family: Arial, sans-serif;
                background: #f5f5f5;
            }}
            
            .sticker {{
                width: 500px;
                height: 300px;
                border: 3px solid #333;
                margin: 20px auto;
                display: block;
                text-align: center;
                background: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                border-radius: 8px;
            }}
            
            .barcode-image {{
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
                display: block;
            }}
            
            .print-button {{
                background-color: #28a745;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 18px;
                margin: 20px;
                display: block;
                margin-left: auto;
                margin-right: auto;
                font-weight: bold;
            }}
            
            .print-button:hover {{
                background-color: #218838;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            
            .info {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .delivery-info {{
                background: #e8f5e8;
                border: 2px solid #28a745;
                padding: 15px;
                border-radius: 8px;
                margin: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="no-print">
            <div class="header">
                <h2>🚚 Delivery Barcode Sticker - {barcode_text}</h2>
                <p><strong>Product:</strong> {product_name or 'N/A'}</p>
                <p><strong>ID:</strong> {product_id or 'N/A'}</p>
            </div>
            
            <button class="print-button" onclick="window.print()">🖨️ Print Delivery Sticker</button>
            
            <div class="delivery-info">
                <h3>📦 Delivery Instructions:</h3>
                <ul>
                    <li><strong>Size:</strong> 5" x 3" sticker paper recommended</li>
                    <li><strong>Quality:</strong> Set printer to highest quality</li>
                    <li><strong>Paper:</strong> Use white sticker paper or labels</li>
                    <li><strong>Scanning:</strong> Optimized for mobile barcode scanners</li>
                    <li><strong>Visibility:</strong> High contrast for easy scanning</li>
                </ul>
            </div>
            
            <div class="info">
                <h3>🔍 Scanning Tips for Delivery Personnel:</h3>
                <ul>
                    <li>Ensure good lighting when scanning</li>
                    <li>Hold scanner 6-12 inches from barcode</li>
                    <li>Keep barcode flat and straight</li>
                    <li>Clean barcode if dirty or damaged</li>
                </ul>
            </div>
        </div>
        
        <div class="sticker">
            <img src="{image_data}" alt="Delivery Barcode {barcode_text}" class="barcode-image">
        </div>
        
        <script>
            // Handle print events
            window.addEventListener('beforeprint', function() {{
                console.log('Printing delivery barcode sticker...');
            }});
            
            window.addEventListener('afterprint', function() {{
                console.log('Delivery sticker print completed');
            }});
        </script>
    </body>
    </html>
    """
    
    return html
