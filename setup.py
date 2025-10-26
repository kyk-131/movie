#!/usr/bin/env python3
"""
Setup script for AI Movie Generator
This script helps set up the environment and install dependencies.
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version}")

def install_dependencies():
    """Install required dependencies"""
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    directories = [
        'static/uploads',
        'static/output',
        'static/css',
        'static/js'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created {directory}")

def check_env_file():
    """Check if .env file exists"""
    print("\nChecking environment configuration...")
    if not os.path.exists('.env'):
        print("⚠ .env file not found")
        print("Create a .env file with the following variables:")
        print("  GEMINI_API_KEY=your_gemini_api_key")
        print("  ELEVENLABS_API_KEY=your_elevenlabs_api_key")
        print("  NGROK_AUTHTOKEN=your_ngrok_authtoken (optional)")
    else:
        print("✓ .env file found")

def main():
    """Main setup function"""
    print("=" * 50)
    print("AI Movie Generator - Setup")
    print("=" * 50)
    
    check_python_version()
    create_directories()
    check_env_file()
    
    response = input("\nInstall dependencies now? (y/n): ")
    if response.lower() == 'y':
        install_dependencies()
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Create a .env file with your API keys")
    print("2. Run: python app.py")
    print("3. Access at http://localhost:5000")

if __name__ == "__main__":
    main()
