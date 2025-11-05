"""
Setup Verification Script
Tests that all dependencies and configurations are correct
"""

import sys
import os


def test_python_version():
    """Check Python version"""
    print("🔍 Checking Python version...", end=" ")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro}")
        print(f"   ERROR: Python 3.9+ required")
        return False


def test_imports():
    """Check if all required packages are installed"""
    print("\n🔍 Checking dependencies...")
    
    packages = [
        ("livekit", "LiveKit SDK"),
        ("livekit.agents", "LiveKit Agents"),
        ("livekit.plugins.openai", "LiveKit OpenAI Plugin"),
        ("livekit.plugins.silero", "LiveKit Silero Plugin"),
        ("twilio", "Twilio SDK"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("dotenv", "python-dotenv"),
    ]
    
    all_ok = True
    for package, name in packages:
        try:
            __import__(package)
            print(f"   ✓ {name}")
        except ImportError:
            print(f"   ✗ {name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def test_config():
    """Check if configuration is valid"""
    print("\n🔍 Checking configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("   ✗ .env file not found")
        print("   Please create .env from env.example:")
        print("   copy env.example .env")
        return False
    
    print("   ✓ .env file exists")
    
    # Try to load configuration
    try:
        from config import Config
        print("   ✓ Configuration loaded")
        
        # Check required variables
        required = {
            "TWILIO_ACCOUNT_SID": Config.TWILIO_ACCOUNT_SID,
            "TWILIO_AUTH_TOKEN": Config.TWILIO_AUTH_TOKEN,
            "TWILIO_PHONE_NUMBER": Config.TWILIO_PHONE_NUMBER,
            "LIVEKIT_URL": Config.LIVEKIT_URL,
            "LIVEKIT_API_KEY": Config.LIVEKIT_API_KEY,
            "LIVEKIT_API_SECRET": Config.LIVEKIT_API_SECRET,
            "OPENAI_API_KEY": Config.OPENAI_API_KEY,
        }
        
        missing = []
        placeholder = []
        
        for var_name, var_value in required.items():
            if not var_value:
                missing.append(var_name)
            elif "xxx" in var_value.lower() or "your_" in var_value.lower():
                placeholder.append(var_name)
        
        if missing:
            print(f"\n   ✗ Missing variables: {', '.join(missing)}")
            return False
        
        if placeholder:
            print(f"\n   ⚠️  Variables with placeholder values: {', '.join(placeholder)}")
            print(f"   Please update these with your actual credentials")
            return False
        
        print("   ✓ All required variables configured")
        
        # Validate credentials format
        if not Config.TWILIO_ACCOUNT_SID.startswith("AC"):
            print("   ⚠️  TWILIO_ACCOUNT_SID should start with 'AC'")
        
        if not Config.LIVEKIT_API_KEY.startswith("API"):
            print("   ⚠️  LIVEKIT_API_KEY should start with 'API'")
        
        if not Config.OPENAI_API_KEY.startswith("sk-"):
            print("   ⚠️  OPENAI_API_KEY should start with 'sk-'")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Configuration error: {e}")
        return False


def test_connectivity():
    """Test basic connectivity (optional)"""
    print("\n🔍 Testing connectivity...")
    
    try:
        import socket
        
        # Test internet connectivity
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("   ✓ Internet connection")
        
        return True
        
    except OSError:
        print("   ✗ No internet connection")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("  Voice Agent Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Python Version", test_python_version()))
    results.append(("Dependencies", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Connectivity", test_connectivity()))
    
    # Summary
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"   {test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed! You're ready to start the voice agent.")
        print("\nNext steps:")
        print("   1. Start the webhook server: python webhook_server.py")
        print("   2. Start ngrok: ngrok http 8000")
        print("   3. Start the agent: python agent.py")
        print("\nOr use the quick start script:")
        print("   start.bat")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        print("\nNeed help? Check:")
        print("   - README.md for overview")
        print("   - SETUP_GUIDE.md for detailed setup")
        print("   - PERFORMANCE_GUIDE.md for optimization")
        return 1


if __name__ == "__main__":
    exit_code = main()
    print()
    input("Press Enter to exit...")
    sys.exit(exit_code)

