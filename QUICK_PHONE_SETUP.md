# Quick Phone Setup Guide

## 🚀 Get Phone Calls Working in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

**Note:** If using Python 3.13+, `audioop-lts` will be installed automatically for audio conversion (Python 3.13 removed the built-in `audioop` module).

### Step 2: Start Both Services

**Terminal 1 - Agent:**
```bash
python agent.py
```
Wait for: `✅ Realtime agent ready`

**Terminal 2 - Webhook:**
```bash
python webhook_server.py
```
Wait for: `🚀 Starting Voice Agent Webhook Server`

### Step 3: Get Public URL

**Option A - Production (Render.com, Railway, etc.):**
```
Your deployed URL: https://your-app.onrender.com
```

**Option B - Local Testing (ngrok):**
```bash
ngrok http 8000
```
Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### Step 4: Configure Twilio

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click your phone number
3. Under "Voice Configuration":
   - **A Call Comes In**: Webhook, POST
   - **URL**: `https://YOUR-DOMAIN/incoming-call`
4. Save

### Step 5: Test!

1. Call your Twilio phone number
2. Say "Hello!"
3. Agent should respond!

---

## ✅ Verification

Call should show these logs:

**Webhook Server:**
```
📞 Incoming call: CA... from +1234567890
✓ Created room 'call-CA...'
📡 Media stream WebSocket connected
✓ Connected to LiveKit room
```

**Agent:**
```
👤 Participant joined: phone-+1234567890
```

---

## 🔧 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Call hangs up immediately | Check Twilio webhook URL is correct |
| No audio | Speak first! Say "Hello!" |
| Agent not responding | Check agent.py is running |
| WebSocket errors | Install: `pip install websockets` |
| Python 3.13 audioop error | Fixed! Update to latest code with `audioop-lts` |

---

## 📋 What Changed

### webhook_server.py
- ✅ Added `/media-stream` WebSocket endpoint
- ✅ Bridges phone audio to LiveKit
- ✅ Converts audio formats automatically

### requirements.txt
- ✅ Added WebSocket support

### What You Need to Do
1. Update Twilio webhook to point to your `/incoming-call` endpoint
2. Make sure both agent.py and webhook_server.py are running
3. Call your number!

---

## 🎯 Expected Flow

```
You call Twilio number
    ↓
Twilio hits your webhook (/incoming-call)
    ↓
Webhook returns TwiML with Stream
    ↓
Twilio opens WebSocket to /media-stream
    ↓
Audio bridges to LiveKit room
    ↓
Your AI agent joins the room
    ↓
Conversation works!
```

---

## 💡 Testing Tips

1. **Test webhook is accessible:**
   ```bash
   curl https://your-domain.com/health
   # Should return: {"status":"ok"}
   ```

2. **Watch the logs** while making a test call

3. **Speak clearly** - phone microphones vary in quality

4. **Be patient** - first response may take 1-2 seconds

---

## 🆘 Still Not Working?

Check the detailed guide: `PHONE_CALL_SETUP.md`

Common issues:
- Webhook URL must be HTTPS (HTTP won't work)
- Both agent and webhook must be running
- Environment variables must be set (.env file)
- Twilio webhook must point to `/incoming-call` (not root)

---

## ✅ Success Indicators

✓ Call doesn't hang up immediately  
✓ You see "Media stream WebSocket connected" in logs  
✓ You see "Connected to LiveKit room" in logs  
✓ Agent responds when you say "Hello"  

**If you see all these, it's working!** 🎉

