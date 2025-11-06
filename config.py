"""
Configuration module for Voice Agent
Loads environment variables and provides configuration settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the voice agent"""
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    
    # LiveKit Configuration
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
    
    # LiveKit SIP Configuration (for phone calls)
    LIVEKIT_SIP_DOMAIN = os.getenv("LIVEKIT_SIP_DOMAIN", "sip.livekit.cloud")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Agent Configuration
    AGENT_NAME = os.getenv("AGENT_NAME", "AI Assistant")
    AGENT_GREETING = os.getenv(
        "AGENT_GREETING",
        "Hello! I'm your AI assistant. How can I help you today?"
    )
    
    # Server Configuration
    WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))
    WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    
    # Performance Settings - ULTRA-LOW LATENCY OPTIMIZED
    MAX_CONCURRENT_CALLS = int(os.getenv("MAX_CONCURRENT_CALLS", "200"))
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")  # Reduced logging for performance
    
    # Webhook server settings for high concurrency
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))  # Async worker threads (webhook server only)
    
    # AI Model Settings - ULTRA-LOW LATENCY OPTIMIZED
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-realtime-preview")
    
    # Voice settings for Realtime API (alloy = fastest)
    VOICE_MODEL = os.getenv("VOICE_MODEL", "alloy")
    
    # System prompt - ULTRA-SHORT for MAXIMUM SPEED
    # Every word here adds latency - keep it minimal!
    SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", """Friendly AI assistant. Be brief. 1 sentence answers. Speak fast.""")
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            ("TWILIO_ACCOUNT_SID", cls.TWILIO_ACCOUNT_SID),
            ("TWILIO_AUTH_TOKEN", cls.TWILIO_AUTH_TOKEN),
            ("TWILIO_PHONE_NUMBER", cls.TWILIO_PHONE_NUMBER),
            ("LIVEKIT_URL", cls.LIVEKIT_URL),
            ("LIVEKIT_API_KEY", cls.LIVEKIT_API_KEY),
            ("LIVEKIT_API_SECRET", cls.LIVEKIT_API_SECRET),
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
        ]
        
        missing = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing.append(var_name)
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file."
            )
        
        return True


# Validate configuration on import
try:
    Config.validate()
    print("✓ Configuration loaded successfully")
except ValueError as e:
    print(f"✗ Configuration error: {e}")
    print("Please create a .env file based on env.example and fill in your credentials.")

