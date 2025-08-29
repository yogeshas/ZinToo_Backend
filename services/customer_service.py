from models.customer import Customer
from models.order import Order  # Import Order to ensure relationship is loaded
from extensions import db
from services.referral_service import generate_referral_code, process_referral_signup
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_


def create_customer(data):
    customer = Customer(
        username=data.get("username") or data.get("email"),
        email=data.get("email") or f"{data.get('customerid','user')}@local",
        customerid=data.get("customerid"),
        status=data.get("status", "active"),
        referral_count=data.get("referral_count", 0),
    )

    # Optional social login identifiers
    if data.get("provider"):
        customer.provider = data.get("provider")
    if data.get("provider_id"):
        customer.provider_id = data.get("provider_id")

    if data.get("password"):
        # password is already plaintext after route-level decrypt
        customer.set_password(data["password"])
    else:
        # Social account might not have a password
        customer.set_password("social-login")

    if data.get("phone_number"):
        customer.set_phone_number(data["phone_number"])

    if data.get("location"):
        customer.set_location(data["location"])

    # Generate unique referral code for new customer
    username = data.get("username") or data.get("email", "user")
    referral_code = generate_referral_code(username)
    customer.set_referral_code(referral_code)

    try:
        db.session.add(customer)
        db.session.commit()

        # Process referral if provided
        referral_code_used = data.get("referral_code_used")
        if referral_code_used:
            process_referral_signup(customer.id, referral_code_used)

        return customer
    except IntegrityError:
        db.session.rollback()
        # Try to fetch existing if unique constraint fails
        existing = Customer.query.filter_by(username=customer.username).first()
        if existing:
            return existing
        raise


def get_customer_by_id(cid):
    return Customer.query.get(cid)


def get_all_customers():
    return Customer.query.order_by(Customer.id.desc()).all()


def get_customer_by_username(username):
    return Customer.query.filter_by(username=username).first()


def get_customer_by_email_or_username(identifier):
    return Customer.query.filter(
        or_(Customer.username == identifier, Customer.email == identifier)
    ).first()


def get_customer_by_email(email):
    return Customer.query.filter_by(email=email).first()


def update_customer(cid, data):
    print(f"Updating customer {cid} with data: {data}")
    customer = get_customer_by_id(cid)
    if not customer:
        print(f"Customer {cid} not found")
        return None

    print(
        f"Before update - Customer: {customer.username}, "
        f"Email: {customer.email}, "
        f"Phone: {customer.get_phone_number()}, "
        f"Location: {customer.get_location()}"
    )

    # Only allow certain fields to be updated
    for k in ("username", "email", "status", "provider", "provider_id"):
        if k in data:
            print(f"Setting {k} to {data[k]}")
            setattr(customer, k, data[k])

    # Handle phone/location updates via helpers
    if "phone_number" in data:
        print(f"Setting phone_number to {data['phone_number']}")
        customer.set_phone_number(data["phone_number"])

    if "location" in data:
        print(f"Setting location to {data['location']}")
        customer.set_location(data["location"])

    print(
        f"After setting values - Customer: {customer.username}, "
        f"Email: {customer.email}, "
        f"Phone: {customer.get_phone_number()}, "
        f"Location: {customer.get_location()}"
    )

    try:
        db.session.commit()
        print(f"Customer {cid} updated successfully")

        # Verify the update by fetching the customer again
        db.session.refresh(customer)
        print(
            f"After commit - Customer: {customer.username}, "
            f"Email: {customer.email}, "
            f"Phone: {customer.get_phone_number()}, "
            f"Location: {customer.get_location()}"
        )
        return customer
    except Exception as e:
        print(f"Error updating customer {cid}: {str(e)}")
        db.session.rollback()
        raise


def delete_customer(cid):
    customer = get_customer_by_id(cid)
    if not customer:
        return False

    try:
        # Delete related records first

        # Delete wallet transactions (through wallet)
        from models.wallet import Wallet, WalletTransaction
        wallet = Wallet.query.filter_by(customer_id=cid).first()
        if wallet:
            WalletTransaction.query.filter_by(wallet_id=wallet.id).delete()
            db.session.delete(wallet)

        # Delete orders and order items
        from models.order import Order, OrderItem
        orders = Order.query.filter_by(customer_id=cid).all()
        for order in orders:
            OrderItem.query.filter_by(order_id=order.id).delete()
        Order.query.filter_by(customer_id=cid).delete()

        # Delete cart items
        from models.cart import Cart
        Cart.query.filter_by(customer_id=cid).delete()

        # Delete wishlist items
        from models.wishlist import Wishlist
        Wishlist.query.filter_by(customer_id=cid).delete()

        # Delete addresses
        from models.address import Address
        Address.query.filter_by(uid=cid).delete()

        # Now delete the customer
        db.session.delete(customer)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Delete customer error: {str(e)}")
        db.session.rollback()
        raise


def set_customer_blocked(cid, blocked: bool = True):
    customer = get_customer_by_id(cid)
    if not customer:
        return None

    customer.status = "blocked" if blocked else "active"
    try:
        db.session.commit()
        db.session.refresh(customer)
        return customer
    except Exception as e:
        db.session.rollback()
        raise

def update_customer_admin(cid, data):
    print(f"[ADMIN] update_customer_admin CALLED for customer {cid} with {data}")
    customer = get_customer_by_id(cid)
    if not customer:
        print(f"[ADMIN] Customer {cid} not found")
        return None

    allowed_fields = ("username", "email", "status", "provider", "provider_id", "phone_number", "location")

    try:
        # Log current state before update
        print(f"[ADMIN] Before update - Location: '{customer.get_location()}', Phone: '{customer.get_phone_number()}'")
        
        for key in allowed_fields:
            if key in data:
                new_val = data[key]
                print(f"[ADMIN] Processing field '{key}' with value '{new_val}' (type: {type(new_val)})")
                
                if key == "phone_number":
                    # Handle phone number update
                    if new_val is not None:
                        customer.set_phone_number(str(new_val))
                        print(f"[ADMIN] Set phone_number to: '{customer.get_phone_number()}'")
                    else:
                        customer.set_phone_number(None)
                        print(f"[ADMIN] Cleared phone_number")
                        
                elif key == "location":
                    # Handle location update
                    if new_val is not None:
                        customer.set_location(str(new_val))
                        print(f"[ADMIN] Set location to: '{customer.get_location()}'")
                    else:
                        customer.set_location(None)
                        print(f"[ADMIN] Cleared location")
                        
                else:
                    # Handle regular fields
                    setattr(customer, key, new_val)
                    print(f"[ADMIN] Set {key} to: {new_val}")

        # Log state after setting values but before commit
        print(f"[ADMIN] After setting values - Location: '{customer.get_location()}', Phone: '{customer.get_phone_number()}'")

        db.session.commit()
        db.session.refresh(customer)
        
        # Log final state after commit
        print(f"[ADMIN] After commit - Location: '{customer.get_location()}', Phone: '{customer.get_phone_number()}'")
        print(f"[ADMIN] Commit SUCCESS for customer {customer.id}")
        return customer

    except Exception as e:
        db.session.rollback()
        print(f"[ADMIN] Commit FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        raise