#!/usr/bin/env python3
"""
Comprehensive backend fix script
"""
import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} error: {str(e)}")
        return False

def fix_imports():
    """Fix all circular imports"""
    print("\n🔧 Fixing circular imports...")
    
    # Fix models
    run_command(
        'Get-ChildItem models\\*.py | ForEach-Object { (Get-Content $_.FullName) -replace "from app import db", "from extensions import db" | Set-Content $_.FullName }',
        "Fixed model imports"
    )
    
    # Fix services
    run_command(
        'Get-ChildItem services\\*.py | ForEach-Object { (Get-Content $_.FullName) -replace "from app import db", "from extensions import db" | Set-Content $_.FullName }',
        "Fixed service imports"
    )
    
    # Fix routes
    run_command(
        'Get-ChildItem routes\\*.py | ForEach-Object { (Get-Content $_.FullName) -replace "from app import db", "from extensions import db" | Set-Content $_.FullName }',
        "Fixed route imports"
    )

def install_requirements():
    """Install Python requirements"""
    print("\n📦 Installing requirements...")
    return run_command("pip install -r requirements.txt", "Installing requirements")

def create_missing_directories():
    """Create missing directories"""
    print("\n📁 Creating missing directories...")
    
    directories = [
        "assets/img/widgets",
        "assets/img/categories", 
        "assets/img/products",
        "migrations/versions"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")

def check_database():
    """Check database connection"""
    print("\n🗄️ Checking database...")
    
    # This would need to be implemented based on your database setup
    print("⚠️ Please check your database connection in config.py")

def main():
    """Main fix function"""
    print("🚀 Starting Backend Fix Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ Error: Please run this script from the backend directory")
        sys.exit(1)
    
    # Run fixes
    fix_imports()
    install_requirements()
    create_missing_directories()
    check_database()
    
    print("\n" + "=" * 50)
    print("🎉 Backend fix completed!")
    print("\nNext steps:")
    print("1. Start the backend: python app.py")
    print("2. Test routes: python test_routes.py")
    print("3. Check for any remaining errors")

if __name__ == "__main__":
    main()
