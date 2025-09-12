# Backend Startup Instructions - FIXED VERSION

## 🚀 Quick Start (Recommended)

### Option 1: Use the Fixed Startup Script
1. Right-click `start_backend_fixed.ps1` and select "Run with PowerShell"
2. This script will:
   - Activate virtual environment
   - Install requirements
   - Create missing directories
   - Fix circular imports
   - Start the backend server

### Option 2: Manual Steps
1. Open PowerShell in this directory
2. Activate virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Install requirements:
   ```powershell
   pip install -r requirements.txt
   ```
4. Start the server:
   ```powershell
   python app.py
   ```

## 🔧 What Was Fixed

1. **Circular Import Issues**: Fixed all `from app import db` to `from extensions import db`
2. **Missing Routes**: Added all missing route registrations:
   - `/api/subcategories/`
   - `/api/widgets/`
   - `/api/addresses/`
   - `/api/coupons/`
   - `/api/admin/`
3. **Missing Models**: Added all model imports
4. **Service Layer**: Fixed OTP and forgot password services
5. **Directory Structure**: Created missing asset directories

## 🧪 Testing

### Test All Routes
```powershell
python test_routes.py
```

### Test Health Endpoint
Visit: `http://localhost:5000/api/health`

Should return:
```json
{
  "success": true,
  "message": "Backend is running",
  "timestamp": "2024-01-XX..."
}
```

## 📋 Available Routes

✅ **Working Routes:**
- `GET /api/health` - Health check
- `GET /api/categories/` - Get all categories
- `GET /api/subcategories/` - Get all subcategories
- `GET /api/products/` - Get all products
- `GET /api/widgets/` - Get all widgets
- `GET /api/cart/` - Get user cart
- `GET /api/wishlist/` - Get user wishlist
- `GET /api/addresses/` - Get user addresses
- `GET /api/coupons/` - Get all coupons
- `POST /api/cart/add` - Add to cart
- `POST /api/wishlist/add` - Add to wishlist
- `DELETE /api/cart/remove/<id>` - Remove from cart
- `DELETE /api/wishlist/remove/<id>` - Remove from wishlist

## 🚨 Troubleshooting

### Common Issues:

1. **ModuleNotFoundError**: 
   - Make sure virtual environment is activated
   - Run: `pip install -r requirements.txt`

2. **Port already in use**: 
   - Change port in `app.py` or kill existing process
   - Use: `netstat -ano | findstr :5000` to find process

3. **Database errors**: 
   - Check `config.py` for database connection settings
   - Ensure database server is running

4. **404 errors**: 
   - All routes are now registered
   - Check if backend is running on correct port

### Debug Steps:

1. **Check if backend is running**:
   ```powershell
   curl http://localhost:5000/api/health
   ```

2. **Check specific route**:
   ```powershell
   curl http://localhost:5000/api/categories/
   ```

3. **View logs**: Check the console output for any error messages

## 🎯 Expected Output

When successful, you should see:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: xxx-xxx-xxx
```

And no more 404 errors for:
- `/api/subcategories/`
- `/api/widgets/`
- `/api/addresses/`
- `/api/coupons/`

## 🚀 Next Steps

1. **Start the backend** using the fixed startup script
2. **Test the health endpoint** at `http://localhost:5000/api/health`
3. **Start the frontend** in another terminal: `cd ../customer/frontend && npm run dev`
4. **Test the complete system** - cart and wishlist should now work properly
