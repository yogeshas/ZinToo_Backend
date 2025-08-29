from models.product import Product
from extensions import db
from utils.crypto import encrypt_payload, decrypt_payload
import json
def get_all_products():
    return Product.query.order_by(Product.id.desc()).all()

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
    
    # support multiple images as comma-joined string
    images_value = data.get("images")
    if isinstance(images_value, list):
        image_field = ",".join([str(u).strip() for u in images_value if str(u).strip()])
    else:
        image_field = data.get("image")

    try:
        # Normalize sizes: accept dict (size->count) or list/CSV
        size_value = data.get("size")
        if isinstance(size_value, dict):
            size_field = json.dumps(size_value)
        else:
            size_field = size_value

        # Auto-calc stock/quantity from size map if provided
        auto_stock = None
        if isinstance(size_value, dict):
            try:
                auto_stock = sum(int(v or 0) for v in size_value.values())
            except Exception:
                auto_stock = None

        product = Product(
            pname=data.get("pname"),
            pdescription=data.get("pdescription"),
            size=size_field,
            color=data.get("color"),
            price=float(data.get("price")),
            cid=int(data.get("cid")),
            sid=int(data.get("sid")) if data.get("sid") else None,
            stock=int(auto_stock if auto_stock is not None else data.get("stock", 0)),
            visibility=data.get("visibility", True),
            is_active=data.get("is_active", True),
            quantity=int(auto_stock if auto_stock is not None else data.get("quantity", 1)),
            
            
            is_returnable=data.get("is_returnable", True),
            is_cod_available=data.get("is_cod_available", True),
            rating=float(data.get("rating", 0)),
            is_featured=data.get("is_featured", False),
            is_latest=data.get("is_latest", False),
            is_trending=data.get("is_trending", False),
            is_new=data.get("is_new", False),
            discount_value=float(data.get("discount_value", 0)),
            shared_count=int(data.get("shared_count", 0)),
            
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
    }
    # If sizes map provided, normalize and auto-calc stock/quantity
    if "size" in data and isinstance(data["size"], dict):
        try:
            total = sum(int(v or 0) for v in data["size"].values())
        except Exception:
            total = None
        data = {
            **data,
            "size": data["size"],
            **({"stock": total, "quantity": total} if total is not None else {}),
        }

    for key, value in data.items():
        if key in allowed_fields:
            if key == "size" and isinstance(value, dict):
                setattr(product, key, json.dumps(value))
            else:
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
