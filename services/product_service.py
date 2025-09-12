from models.product import Product
from extensions import db
from utils.crypto import encrypt_payload, decrypt_payload
from utils.barcode_generator import generate_unique_barcode, regenerate_barcode
import json
def get_all_products():
    return Product.query.order_by(Product.id.desc()).all()

def get_customer_products():
    """Get products visible to customers (active and visible)"""
    return Product.query.filter(
        Product.is_active == True,
        Product.visibility == True
    ).order_by(Product.id.desc()).all()

def get_product_by_id(pid):
    return Product.query.get(pid)

def create_product(data):
    # Validate required fields
    required_fields = ["pname", "price", "cid"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    # Validate category exists
    from models.category import Category
    category = Category.query.get(data.get("cid"))
    if not category:
        raise ValueError(f"Category with ID {data.get('cid')} does not exist")
    
    # Validate subcategory if provided
    if data.get("sid"):
        from models.subcategory import SubCategory
        subcategory = SubCategory.query.get(data.get("sid"))
        if not subcategory:
            raise ValueError(f"Subcategory with ID {data.get('sid')} does not exist")
    
    # Handle images - support both new structure and legacy
    images_value = data.get("images")
    if isinstance(images_value, list):
        image_field = ",".join([str(u).strip() for u in images_value if str(u).strip()])
    else:
        image_field = data.get("image")

    try:
        # Handle colors - new structure
        colors_data = data.get("colors", [])
        if colors_data and isinstance(colors_data, list):
            # New color-based structure
            colors_field = json.dumps(colors_data)
            
            # Calculate total stock from all colors
            total_stock = 0
            for color in colors_data:
                if isinstance(color, dict) and color.get("sizeCounts"):
                    total_stock += sum(int(v or 0) for v in color["sizeCounts"].values())
        else:
            # Legacy single color/size structure
            colors_field = None
            size_value = data.get("size")
            if isinstance(size_value, dict):
                size_field = json.dumps(size_value)
                total_stock = sum(int(v or 0) for v in size_value.values())
            else:
                size_field = size_value
                total_stock = data.get("stock", 0)

        # Generate unique barcode for new product
        try:
            barcode = generate_unique_barcode()
        except Exception as barcode_error:
            raise ValueError(f"Failed to generate barcode: {str(barcode_error)}")
        
        product = Product(
            pname=data.get("pname"),
            pdescription=data.get("pdescription"),
            size=size_field if not colors_data else None,
            color=data.get("color") if not colors_data else None,
            colors=colors_field,
            price=float(data.get("price")),
            cid=int(data.get("cid")),
            sid=int(data.get("sid")) if data.get("sid") else None,
            stock=int(total_stock),
            visibility=data.get("visibility", True),
            is_active=data.get("is_active", True),
            quantity=int(total_stock),
            is_returnable=data.get("is_returnable", True),
            is_cod_available=data.get("is_cod_available", True),
            rating=float(data.get("rating", 0)),
            is_featured=data.get("is_featured", False),
            is_latest=data.get("is_latest", False),
            is_trending=data.get("is_trending", False),
            is_new=data.get("is_new", False),
            discount_value=float(data.get("discount_value", 0)),
            shared_count=int(data.get("shared_count", 0)),
            barcode=barcode,
            image=image_field,
            tag=data.get("tag"),
        )
        db.session.add(product)
        db.session.commit()
        return product
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error creating product: {str(e)}")

def update_product(pid, data):
    product = Product.query.get(pid)
    if not product:
        return None
    
    # Normalize images input
    if "images" in data and isinstance(data["images"], list):
        data["image"] = ",".join([str(u).strip() for u in data["images"] if str(u).strip()])

    allowed_fields = {
        "pname",
        "pdescription",
        "size",
        "color",
        "colors",
        "price",
        "tag",
        "cid",
        "sid",
        "image",
        "stock",
        "visibility",
        "is_active",
        "quantity",
        "is_returnable",
        "is_cod_available",
        "rating",
        "is_featured",
        "is_latest",
        "is_trending",
        "is_new",
        "shared_count",
        "coupon_id",
        "discount_value",
        "barcode",
    }
    
    # Handle colors - new structure
    if "colors" in data and data["colors"]:
        colors_data = data["colors"]
        if isinstance(colors_data, list):
            # Calculate total stock from all colors
            total_stock = 0
            for color in colors_data:
                if isinstance(color, dict) and color.get("sizeCounts"):
                    total_stock += sum(int(v or 0) for v in color["sizeCounts"].values())
            
            data["colors"] = json.dumps(colors_data)
            data["stock"] = total_stock
            data["quantity"] = total_stock
            # Clear legacy fields when using new structure
            data["size"] = None
            data["color"] = None
    elif "size" in data and isinstance(data["size"], dict):
        # Legacy size handling
        try:
            total = sum(int(v or 0) for v in data["size"].values())
        except Exception:
            total = None
        data = {
            **data,
            "size": json.dumps(data["size"]),
            **({"stock": total, "quantity": total} if total is not None else {}),
        }

    for key, value in data.items():
        if key in allowed_fields:
            setattr(product, key, value)
    
    db.session.commit()
    return product

def delete_product(pid):
    product = Product.query.get(pid)
    if not product:
        return False
    db.session.delete(product)
    db.session.commit()
    return True

def regenerate_product_barcode(pid):
    """
    Regenerate barcode for an existing product
    """
    try:
        new_barcode = regenerate_barcode(pid)
        return {"success": True, "barcode": new_barcode}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Failed to regenerate barcode: {str(e)}"}
