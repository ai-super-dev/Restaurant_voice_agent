# Debug Webhook Error - "Error connecting your call"

## 🔴 Error Analysis

**Message**: "Sorry, there was an error connecting your call. Please try again later."

**Location**: This comes from webhook_server.py exception handler (lines 105-109)

**Meaning**: An exception is happening when processing the call

## 🔍 Most Likely Causes

### 1. Missing Environment Variables (Most Common!)

**Check Render.com** has ALL these variables:

```bash
LIVEKIT_URL=wss://your-livekit-url
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxx
OPENAI_API_KEY=sk-xxxxx
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1xxxxx
```

**Without these**, the webhook will crash!

### 2. Invalid LiveKit Credentials

**The webhook creates a LiveKit token** (lines 65-78)

If credentials are wrong → Exception → Error message

### 3. Config Validation Failing

**Line 11**: `from config import Config`

If Config.validate() fails → Exception → Error message

## 🔧 How to Find the Exact Error

### Check Render.com Logs

1. Go to Render.com dashboard
2. Click your **webhook service**
3. Click **"Logs"** tab
4. Make a test call
5. Look for the actual error message

**You'll see something like**:
```
Error handling incoming call: [ACTUAL ERROR HERE]
```

## 🚀 Quick Fixes to Try

### Fix 1: Check Environment Variables

**On Render.com**:
1. Dashboard → Your webhook service
2. Click "Environment"
3. Verify ALL variables are set
4. If any missing → Add them
5. Service will auto-redeploy

### Fix 2: Check LiveKit Credentials

Test your LiveKit credentials work:

```python
# Quick test script
from livekit import api

token = api.AccessToken(
    "YOUR_API_KEY",
    "YOUR_API_SECRET"
)
token.with_identity("test")
token.with_grants(api.VideoGrants(room_join=True, room="test"))
jwt = token.to_jwt()
print("Token generated successfully!")
```

### Fix 3: Simplify Webhook for Testing

Let's add better error logging to see what's failing:

```python
# Add to webhook_server.py, line 49, after "try:"
logger.info(f"Processing call from {form_data.get('From')}")
logger.info(f"LIVEKIT_URL: {Config.LIVEKIT_URL[:20]}...")  # First 20 chars
logger.info(f"LIVEKIT_API_KEY set: {bool(Config.LIVEKIT_API_KEY)}")
```

## 📝 Updated webhook_server.py with Better Logging

Let me update your webhook to show exactly what's failing:

