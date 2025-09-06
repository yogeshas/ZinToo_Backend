import os
import io
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import base64

def generate_barcode_image(barcode_text, product_name=None, product_id=None):
    """
    Generate a barcode image with the barcode number and optional product info
    
    Args:
        barcode_text (str): The barcode text to encode
        product_name (str, optional): Product name to display
        product_id (int, optional): Product ID to display
    
    Returns:
        str: Base64 encoded image data
    """
    try:
        # Create barcode
        barcode = Code128(barcode_text, writer=ImageWriter())
        
        # Generate barcode image with better scanning properties
        barcode_buffer = io.BytesIO()
        barcode.write(barcode_buffer, options={
            'module_width': 0.6,  # Increased for better scanning
            'module_height': 20.0,  # Increased height for better scanning
            'quiet_zone': 8.0,  # Increased quiet zone
            'font_size': 12,  # Larger font for better readability
            'text_distance': 8.0,  # More space between barcode and text
            'background': 'white',
            'foreground': 'black',
            'write_text': True,  # Ensure text is written
            'center_text': True,  # Center the text
        })
        
        # Open the barcode image
        barcode_image = Image.open(barcode_buffer)
        
        # Create a larger canvas for the sticker (increased size for better scanning)
        sticker_width = 400
        sticker_height = 250
        sticker = Image.new('RGB', (sticker_width, sticker_height), 'white')
        
        # Calculate positions
        barcode_width, barcode_height = barcode_image.size
        barcode_x = (sticker_width - barcode_width) // 2
        barcode_y = 20
        
        # Paste barcode onto sticker
        sticker.paste(barcode_image, (barcode_x, barcode_y))
        
        # Add text
        draw = ImageDraw.Draw(sticker)
        
        # Try to use a better font, fallback to default
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
        except:
            try:
                font_large = ImageFont.truetype("arial.ttf", 20)
                font_medium = ImageFont.truetype("arial.ttf", 16)
                font_small = ImageFont.truetype("arial.ttf", 12)
            except:
                try:
                    # Try to load default font with larger size
                    font_large = ImageFont.load_default()
                    font_medium = ImageFont.load_default()
                    font_small = ImageFont.load_default()
                except:
                    font_large = None
                    font_medium = None
                    font_small = None
        
        # Add company name at top
        company_text = "ZinToo"
        company_bbox = draw.textbbox((0, 0), company_text, font=font_large)
        company_width = company_bbox[2] - company_bbox[0]
        company_x = (sticker_width - company_width) // 2
        draw.text((company_x, 5), company_text, fill='black', font=font_large)
        
        # Add barcode number below barcode
        barcode_number_y = barcode_y + barcode_height + 10
        barcode_bbox = draw.textbbox((0, 0), barcode_text, font=font_medium)
        barcode_text_width = barcode_bbox[2] - barcode_bbox[0]
        barcode_text_x = (sticker_width - barcode_text_width) // 2
        draw.text((barcode_text_x, barcode_number_y), barcode_text, fill='black', font=font_medium)
        
        # Add product info if provided
        y_offset = barcode_number_y + 25
        
        if product_name:
            # Truncate product name if too long
            display_name = product_name[:25] + "..." if len(product_name) > 25 else product_name
            name_bbox = draw.textbbox((0, 0), display_name, font=font_small)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = (sticker_width - name_width) // 2
            draw.text((name_x, y_offset), display_name, fill='black', font=font_small)
            y_offset += 20
        
        if product_id:
            id_text = f"ID: {product_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=font_small)
            id_width = id_bbox[2] - id_bbox[0]
            id_x = (sticker_width - id_width) // 2
            draw.text((id_x, y_offset), id_text, fill='black', font=font_small)
        
        # Convert to base64
        output_buffer = io.BytesIO()
        sticker.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        
        # Encode as base64
        image_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{image_base64}"
        
    except Exception as e:
        print(f"Error generating barcode image: {str(e)}")
        return None

def generate_barcode_sticker_html(barcode_text, product_name=None, product_id=None):
    """
    Generate HTML for printing barcode stickers
    
    Args:
        barcode_text (str): The barcode text
        product_name (str, optional): Product name
        product_id (int, optional): Product ID
    
    Returns:
        str: HTML content for printing
    """
    image_data = generate_barcode_image(barcode_text, product_name, product_id)
    
    if not image_data:
        return "<p>Error generating barcode image</p>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Barcode Sticker - {barcode_text}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                box-sizing: border-box;
            }}
            
            @media print {{
                @page {{
                    size: 4in 2.5in;
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
                    width: 3.9in;
                    height: 2.4in;
                    border: 1px solid #000;
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
                width: 400px;
                height: 250px;
                border: 2px solid #333;
                margin: 20px auto;
                display: block;
                text-align: center;
                background: white;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                border-radius: 8px;
            }}
            
            .barcode-image {{
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
                display: block;
            }}
            
            .print-button {{
                background-color: #007bff;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                margin: 20px;
                display: block;
                margin-left: auto;
                margin-right: auto;
            }}
            
            .print-button:hover {{
                background-color: #0056b3;
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
        </style>
    </head>
    <body>
        <div class="no-print">
            <div class="header">
                <h2>Barcode Sticker - {barcode_text}</h2>
                <p>Product: {product_name or 'N/A'}</p>
                <p>ID: {product_id or 'N/A'}</p>
            </div>
            
            <button class="print-button" onclick="window.print()">🖨️ Print Sticker</button>
            
            <div class="info">
                <h3>Print Instructions:</h3>
                <ul>
                    <li>Use 4" x 2.5" sticker paper</li>
                    <li>Set printer to high quality</li>
                    <li>Ensure margins are set to minimum</li>
                    <li>Test print on regular paper first</li>
                </ul>
            </div>
        </div>
        
        <div class="sticker">
            <img src="{image_data}" alt="Barcode {barcode_text}" class="barcode-image">
        </div>
        
        <script>
            // Auto-print when page loads (uncomment to enable)
            // window.onload = function() {{ 
            //     setTimeout(() => {{ window.print(); }}, 1000);
            // }};
            
            // Handle print events
            window.addEventListener('beforeprint', function() {{
                console.log('Printing barcode sticker...');
            }});
            
            window.addEventListener('afterprint', function() {{
                console.log('Print completed');
            }});
        </script>
    </body>
    </html>
    """
    
    return html
