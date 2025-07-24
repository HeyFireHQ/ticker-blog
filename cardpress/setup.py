#!/usr/bin/env python3
"""
CardPress Setup Script
Automated setup for the local Python-based CardPress system
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command):
    """Run a shell command"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {command}")
        print(f"Error: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version < (3, 8):
        print(f"❌ Python {version.major}.{version.minor} detected. CardPress requires Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("⚠️  Not in a virtual environment. Creating one...")
        
        # Create virtual environment
        venv_path = Path(__file__).parent / 'venv'
        result = run_command(f"python -m venv {venv_path}")
        if result is None:
            return False
        
        # Show activation instructions
        if os.name == 'nt':  # Windows
            activate_cmd = f"{venv_path}\\Scripts\\activate"
        else:  # Unix/Linux/macOS
            activate_cmd = f"source {venv_path}/bin/activate"
        
        print(f"🔧 Virtual environment created at: {venv_path}")
        print(f"📋 To activate: {activate_cmd}")
        print("Please activate the virtual environment and run this setup again.")
        return False
    
    # Install requirements
    result = run_command("pip install -r requirements.txt")
    if result is None:
        return False
    
    print("✅ Dependencies installed successfully")
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = Path(__file__).parent / '.env'
    
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env file...")
    
    env_content = f"""# CardPress Configuration
SECRET_KEY=cardpress-local-{os.urandom(16).hex()}
ADMIN_EMAIL=admin@cardpress.local
ADMIN_PASSWORD=admin123

# Optional: Customize these settings
# FLASK_ENV=development
# FLASK_DEBUG=True
"""
    
    env_path.write_text(env_content)
    print("✅ .env file created with default settings")
    return True

def check_dependencies():
    """Check if all required dependencies are available"""
    required = ['flask', 'werkzeug', 'jinja2', 'markdown']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        return False
    
    print("✅ All dependencies are available")
    return True

def initialize_database():
    """Initialize the SQLite database"""
    print("🗄️  Initializing database...")
    
    try:
        from app import init_database
        init_database()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def show_instructions():
    """Show final instructions to the user"""
    print("\n" + "="*60)
    print("🎉 CardPress Setup Complete!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. Start the server:")
    print("   python app.py")
    
    print("\n2. Open your browser to:")
    print("   http://localhost:8000")
    
    print("\n3. Login with:")
    print("   Email: admin@cardpress.local")
    print("   Password: admin123")
    
    print("\n4. Create your first post:")
    print("   - Click '➕ Add Post'")
    print("   - Write your content")
    print("   - Drag to 'Deployed' when ready")
    
    print("\n5. Deploy your blog:")
    print("   - Click '🚀 Deploy Site' in admin")
    print("   - Or run: python deploy_to_pages.py")
    
    print("\n🔒 Security Note:")
    print("   Change the admin password in the admin interface or .env file")
    
    print("\n📖 Documentation:")
    print("   See README.md for full documentation")
    
    print("\n" + "="*60)

def main():
    """Main setup function"""
    print("🚀 CardPress Local Setup")
    print("="*30)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Check dependencies are available
    if not check_dependencies():
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Show final instructions
    show_instructions()

if __name__ == "__main__":
    main() 