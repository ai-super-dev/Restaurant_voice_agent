# Testing Webhook Server Guide

## 🧪 Complete Testing Guide for webhook_server.py

This guide covers all the ways to test your webhook server, from basic health checks to full phone call integration.

---

## 1️⃣ Basic Local Testing (No Phone Required)

### Step 1: Start the Webhook Server

```bash
# Activate your virtual environment
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Mac/Linux

# Start the webhook server
python webhook_server.py
```

**Expected output:**
```
✓ Configuration loaded successfully
============================================================
🚀 Starting Voice Agent Webhook Server
============================================================
Host: 0.0.0.0
Port: 8000
Max concurrent calls: 150
============================================================

📝 Configure your Twilio phone number webhook to:
   https://your-domain.com/incoming-call

💡 For local testing with ngrok:
   1. Run: ngrok http 8000
   2. Copy the HTTPS URL from ngrok
   3. Set Twilio webhook to: https://YOUR-NGROK-URL/incoming-call
============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **If you see this, your webhook server is running!**

---

## 2️⃣ Test Health Endpoints

### Test 1: Root Endpoint

**Using Browser:**
- Open: http://localhost:8000

**Using curl:**
```bash
curl http://localhost:8000
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "Voice Agent Webhook Server",
  "active_calls": 0
}
```

### Test 2: Health Check Endpoint

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "active_calls": 0
}
```

### Test 3: Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

**Expected Response:**
```json
{
  "active_calls": 0,
  "max_concurrent_calls": 150,
  "utilization_percent": 0.0
}
```

✅ **If all three work, your basic endpoints are good!**

---

## 3️⃣ Test Incoming Call Endpoint (Simulated)

### Test with Simulated Twilio Data

**Using curl:**
```bash
curl -X POST http://localhost:8000/incoming-call \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=CA1234567890abcdef1234567890abcdef" \
  -d "From=%2B15551234567" \
  -d "To=%2B15559876543" \
  -d "CallStatus=ringing"
```

**Using PowerShell (Windows):**
```powershell
$body = @{
    CallSid = "CA1234567890abcdef1234567890abcdef"
    From = "+15551234567"
    To = "+15559876543"
    CallStatus = "ringing"
}

Invoke-WebRequest -Uri http://localhost:8000/incoming-call -Method POST -Body $body
```

**Expected Response (TwiML XML):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="ws://localhost:8000/media-stream">
            <Parameter name="callSid" value="CA1234567890abcdef1234567890abcdef"/>
            <Parameter name="roomName" value="call-CA1234567890abcdef1234567890abcdef"/>
            <Parameter name="fromNumber" value="+15551234567"/>
        </Stream>
    </Connect>
</Response>
```

**Check Server Logs:**
You should see:
```
📞 Incoming call: CA1234567890abcdef1234567890abcdef from +15551234567 to +15559876543
✓ Created room 'call-CA1234567890abcdef1234567890abcdef' for call CA1234567890abcdef1234567890abcdef
🔗 Stream URL: ws://localhost:8000/media-stream
✓ TwiML response created for CA1234567890abcdef1234567890abcdef
Active calls: 1
```

✅ **If you see this TwiML response and logs, your webhook endpoint works!**

---

## 4️⃣ Test with Postman (GUI Method)

### Step 1: Download Postman
- Get it from: https://www.postman.com/downloads/

### Step 2: Test Health Check

1. Create a new request
2. **Method:** GET
3. **URL:** `http://localhost:8000/health`
4. Click **Send**
5. Should see: `{"status":"ok","active_calls":0}`

### Step 3: Test Incoming Call

1. Create a new request
2. **Method:** POST
3. **URL:** `http://localhost:8000/incoming-call`
4. **Headers:**
   - Key: `Content-Type`
   - Value: `application/x-www-form-urlencoded`
5. **Body** (x-www-form-urlencoded):
   - `CallSid`: `CA1234567890abcdef1234567890abcdef`
   - `From`: `+15551234567`
   - `To`: `+15559876543`
   - `CallStatus`: `ringing`
6. Click **Send**
7. Should see TwiML XML response

### Step 4: Test Metrics

1. Create a new request
2. **Method:** GET
3. **URL:** `http://localhost:8000/metrics`
4. Click **Send**
5. Should see metrics JSON

---

## 5️⃣ Test with Real Phone Calls (Local + ngrok)

### Step 1: Install ngrok

**Download ngrok:**
- https://ngrok.com/download

**Or using package managers:**
```bash
# Windows (Chocolatey)
choco install ngrok

# Mac (Homebrew)
brew install ngrok

# Linux
snap install ngrok
```

### Step 2: Start ngrok Tunnel

**Terminal 1 - Start ngrok:**
```bash
ngrok http 8000
```

**Expected output:**
```
Session Status                online
Account                       Your Account
Version                       3.x.x
Region                        United States (us)
Latency                       25ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

✅ **Copy the HTTPS URL:** `https://abc123.ngrok.io`

### Step 3: Start Your Services

**Terminal 2 - Start Agent:**
```bash
python agent.py
```

Wait for: `✅ Realtime agent ready`

**Terminal 3 - Start Webhook:**
```bash
python webhook_server.py
```

Wait for: `🚀 Starting Voice Agent Webhook Server`

### Step 4: Configure Twilio

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click your phone number
3. Under "Voice Configuration":
   - **A Call Comes In:** Webhook, POST
   - **URL:** `https://abc123.ngrok.io/incoming-call` ⚠️ Use YOUR ngrok URL!
4. **Save configuration**

### Step 5: Make a Test Call

1. **Call your Twilio phone number from your phone**
2. **Wait 1-2 seconds** for connection
3. **Say "Hello!"**
4. **Agent should respond!**

### Step 6: Monitor Logs

**Webhook Server (Terminal 3) should show:**
```
📞 Incoming call: CA... from +1234567890 to +1987654321
✓ Created room 'call-CA...'
🔗 Stream URL: wss://abc123.ngrok.io/media-stream
✓ TwiML response created
📡 Media stream WebSocket connected
🎬 Stream started: MZ... for call CA...
🎯 Connecting to LiveKit room: call-CA...
✓ Connected to LiveKit room: call-CA...
✓ Published phone audio track to room
🎧 Subscribed to agent audio track from agent-default
📤 Starting to stream agent audio to Twilio
```

**Agent (Terminal 2) should show:**
```
🎯 New agent session started
Room: call-CA...
✓ Connected to room: call-CA...
👤 Participant joined: phone-+1234567890
🚀 Creating OpenAI Realtime agent
✅ Realtime agent ready
```

✅ **If you see both sets of logs and hear the agent, it's working perfectly!**

---

## 6️⃣ Test WebSocket Connection (Advanced)

### Using wscat (WebSocket CLI tool)

**Install wscat:**
```bash
npm install -g wscat
```

**Test WebSocket endpoint:**
```bash
wscat -c ws://localhost:8000/media-stream
```

**Send a test message:**
```json
{"event":"start","streamSid":"MZ1234","start":{"callSid":"CA1234","customParameters":{"roomName":"test-room","fromNumber":"+15551234567"}}}
```

**Expected in server logs:**
```
📡 Media stream WebSocket connected
🎬 Stream started: MZ1234 for call CA1234
🎯 Connecting to LiveKit room: test-room
```

**To stop:**
Press `Ctrl+C`

---

## 7️⃣ Test on Production (Render.com)

### After Deploying to Render.com

### Test 1: Health Check

```bash
curl https://your-app.onrender.com/health
```

**Expected:**
```json
{"status":"ok","active_calls":0}
```

### Test 2: Configure Twilio

1. Go to Twilio Console
2. Set webhook to: `https://your-app.onrender.com/incoming-call`
3. Save

### Test 3: Make a Call

1. Call your Twilio number
2. Say "Hello!"
3. Agent should respond

### Test 4: Check Render Logs

1. Go to: https://dashboard.render.com
2. Click your service
3. Click "Logs" tab
4. Should see the same log messages as local testing

---

## 8️⃣ Debug Tools

### ngrok Web Interface

While ngrok is running, open: http://127.0.0.1:4040

**Features:**
- See all HTTP requests in real-time
- View request/response details
- Replay requests
- Inspect WebSocket traffic

**Very useful for debugging!**

### Twilio Debugger

Go to: https://console.twilio.com/us1/monitor/logs/debugger

**Shows:**
- All webhook requests from Twilio
- Response status codes
- Error messages
- Call flow issues

**Perfect for diagnosing Twilio-specific issues!**

---

## 9️⃣ Common Test Scenarios

### Test Scenario 1: Single Call
```
1. Start agent
2. Start webhook
3. Call number
4. Say "Hello"
5. Have conversation
6. Hang up
7. Check logs for cleanup
```

### Test Scenario 2: Multiple Concurrent Calls
```
1. Start agent
2. Start webhook
3. Call from Phone 1
4. Immediately call from Phone 2
5. Both should work simultaneously
6. Check metrics: /metrics should show 2 active calls
```

### Test Scenario 3: Error Handling
```
1. Start webhook WITHOUT starting agent
2. Call number
3. Should connect but no agent response
4. Check logs for connection attempts
5. Start agent
6. Make another call
7. Should work now
```

### Test Scenario 4: Quick Hang-up
```
1. Start both services
2. Call number
3. Hang up immediately (before saying anything)
4. Check logs for proper cleanup
5. active_calls should return to 0
```

---

## 🔟 Verification Checklist

### Basic Functionality ✅
- [ ] Server starts without errors
- [ ] `/health` endpoint returns 200 OK
- [ ] `/metrics` endpoint returns data
- [ ] `/incoming-call` returns valid TwiML

### Phone Integration ✅
- [ ] Call connects (doesn't hang up immediately)
- [ ] WebSocket connection established
- [ ] Audio flows to LiveKit
- [ ] Agent joins room
- [ ] Agent responds to speech
- [ ] Bidirectional conversation works
- [ ] Call ends cleanly

### Monitoring ✅
- [ ] Logs show all expected events
- [ ] Twilio debugger shows successful webhooks
- [ ] ngrok shows HTTP/WebSocket traffic
- [ ] Metrics update correctly
- [ ] Active calls tracked properly

### Error Handling ✅
- [ ] Graceful handling when agent offline
- [ ] Proper cleanup on disconnect
- [ ] Error TwiML returned on exceptions
- [ ] No memory leaks on multiple calls

---

## 🚨 Troubleshooting Test Issues

### Issue: Health check fails

**Symptoms:** `curl: (7) Failed to connect`

**Fix:**
```bash
# Check if webhook is running
# Look for: "Uvicorn running on http://0.0.0.0:8000"

# Try different port if 8000 is in use:
# In .env file:
WEBHOOK_PORT=8001

# Restart webhook server
```

### Issue: Incoming call test returns 405

**Symptoms:** `405 Method Not Allowed`

**Fix:**
```bash
# Make sure you're using POST, not GET
curl -X POST http://localhost:8000/incoming-call -d "CallSid=CA123..."
```

### Issue: WebSocket won't connect

**Symptoms:** `WebSocket connection failed`

**Fix:**
```bash
# Check websockets is installed
pip install websockets

# For ngrok, use wss:// not ws://
wss://abc123.ngrok.io/media-stream  ✅
ws://abc123.ngrok.io/media-stream   ❌
```

### Issue: Call connects but no audio

**Symptoms:** Call stays connected, no voice

**Fix:**
1. **Check agent is running**
2. **Speak first** - say "Hello!"
3. **Check logs** for "Published phone audio track"
4. **Wait 2-3 seconds** for initial response

### Issue: ngrok URL changes

**Symptoms:** Webhook works, then stops after ngrok restart

**Fix:**
```bash
# ngrok free gives you a new URL each time
# Must update Twilio webhook URL each time

# OR use ngrok paid for static URL
ngrok http 8000 --domain=your-static.ngrok.io
```

---

## 📊 Expected Response Times

### Local Testing
- Health check: < 10ms
- Incoming call endpoint: < 50ms
- WebSocket connection: < 100ms

### With ngrok
- Health check: 20-50ms (includes tunnel)
- Incoming call: 50-150ms
- WebSocket: 100-200ms

### Production (Render.com)
- Health check: 50-200ms (depending on region)
- Incoming call: 100-300ms
- WebSocket: 200-500ms

### Full Call Latency
- Your voice → Agent response: 600-900ms
- Includes: network, STT, LLM, TTS, audio conversion

---

## ✅ Success Indicators

### When Everything is Working:

**✅ Server logs show:**
- No error messages
- Incoming call events
- WebSocket connections
- LiveKit room connections
- Audio streaming events

**✅ You can:**
- Access all health endpoints
- Receive test POST requests
- Connect via WebSocket
- Make real phone calls
- Have conversations with agent

**✅ Monitoring shows:**
- Active calls tracked correctly
- Metrics update in real-time
- Proper cleanup on disconnect
- No memory leaks

---

## 📚 Quick Test Commands

**Copy-paste these for quick testing:**

```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# Simulated incoming call (Mac/Linux)
curl -X POST http://localhost:8000/incoming-call \
  -d "CallSid=CA123456789" \
  -d "From=%2B15551234567" \
  -d "To=%2B15559876543"

# Simulated incoming call (PowerShell)
Invoke-WebRequest -Uri http://localhost:8000/incoming-call -Method POST -Body @{CallSid="CA123456789";From="+15551234567";To="+15559876543"}

# Check if webhook is listening
netstat -an | grep 8000

# Watch logs in real-time (Mac/Linux)
tail -f webhook.log

# Watch logs in real-time (PowerShell)
Get-Content webhook.log -Wait -Tail 10
```

---

## 🎯 Summary

**Testing Levels:**
1. ✅ **Basic** - Health endpoints (no phone needed)
2. ✅ **Endpoint** - Test webhook with curl/Postman
3. ✅ **Local** - Full test with ngrok + real phone
4. ✅ **Production** - Test on Render.com

**Start with Level 1, progress to Level 4.**

**Most Important Test:**
- Make a real phone call and talk to the agent! 🎉

---

**Questions? Issues? Check the logs - they tell you everything!**

