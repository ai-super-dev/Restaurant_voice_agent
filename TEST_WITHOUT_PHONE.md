# Test Phone Calls Without a Real Phone

## 🎯 Overview

You can **fully test the phone call functionality** without making a real phone call! The `test_phone_simulation.py` script simulates everything Twilio does during a phone call.

---

## 🚀 Quick Start

### Step 1: Start Webhook Server

**Terminal 1:**
```bash
python webhook_server.py
```

Wait for: `🚀 Starting Voice Agent Webhook Server`

### Step 2: (Optional) Start Agent

**Terminal 2:**
```bash
python agent.py
```

Wait for: `✅ Realtime agent ready`

**Note:** The test works even without the agent running, but you won't get simulated responses.

### Step 3: Run the Test

**Terminal 3:**
```bash
python test_phone_simulation.py
```

---

## 📋 What Gets Tested

The simulation test will:

✅ **Test 1: Health Check**
- Verifies webhook server is running
- Tests `/health` endpoint

✅ **Test 2: Incoming Call Webhook**
- Simulates Twilio POST request
- Verifies TwiML response with Stream element
- Tests room creation

✅ **Test 3: WebSocket Connection**
- Opens WebSocket (like Twilio does)
- Sends "start" event
- Sends simulated audio data (3 seconds of 440Hz tone)
- Listens for agent responses
- Sends "stop" event
- **This simulates a complete phone call!**

✅ **Test 4: Call Status**
- Simulates call completion callback
- Verifies cleanup

---

## 🎮 Test Modes

### Full Test (Default)
```bash
python test_phone_simulation.py
```
- Tests everything including WebSocket
- Takes about 10-15 seconds
- Shows detailed progress

### Quick Test
```bash
python test_phone_simulation.py --quick
```
- Tests only health check and incoming call
- Takes about 2 seconds
- Good for quick validation

### Help
```bash
python test_phone_simulation.py --help
```
- Shows usage information

---

## 📊 Expected Output

### Successful Test Output:

```
╔==========================================================╗
║          PHONE CALL SIMULATION TEST SUITE                ║
╚==========================================================╝

Testing webhook at: http://localhost:8000
Make sure webhook_server.py is running!

============================================================
TEST 1: Health Check
============================================================
✅ Status: 200
✅ Response: {'status': 'ok', 'active_calls': 0}

============================================================
TEST 2: Incoming Call Webhook
============================================================
✅ Status: 200
✅ TwiML Response:
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="ws://localhost:8000/media-stream">
...
✅ TwiML contains Stream element - Ready for WebSocket!

============================================================
TEST 3: WebSocket Media Stream
============================================================
This simulates a real phone call's audio stream...

✅ WebSocket connected!

📤 Sending START event...
✅ Start event sent

📤 Sending simulated audio (440Hz tone for 3 seconds)...
   ... sent 10/150 chunks (200ms)
   ... sent 20/150 chunks (400ms)
   ... sent 30/150 chunks (600ms)
   [continues...]
✅ Audio sent successfully!

📥 Listening for agent responses...
   (Note: Agent will only respond if agent.py is running)
✅ Received first audio response from agent!
   ... received 50 audio chunks
   ... received 100 audio chunks
✅ Total audio chunks received: 127

📤 Sending STOP event...
✅ Stop event sent

✅ WebSocket test completed!

============================================================
TEST 4: Call Status Callback
============================================================
✅ Status: 200
✅ Response: OK

============================================================
TEST SUMMARY
============================================================
Health: ✅ PASSED
Incoming Call: ✅ PASSED
Websocket: ✅ PASSED
Call Status: ✅ PASSED

Total: 4/4 tests passed

🎉 ALL TESTS PASSED! Your webhook is working perfectly!

Next steps:
1. If you haven't already, start agent.py for full functionality
2. Test with a real phone call using ngrok
3. Deploy to production!

============================================================
```

---

## 🔍 What's Being Simulated

### The Test Simulates:

```
┌─────────────────────┐
│   test_phone_       │  ← This script
│   simulation.py     │
└──────────┬──────────┘
           │
           │ 1. POST /incoming-call
           │    (simulates Twilio webhook)
           ▼
┌──────────────────────┐
│  webhook_server.py   │
│  (Your Server)       │
└──────────┬───────────┘
           │
           │ 2. Returns TwiML with <Stream>
           ▼
┌─────────────────────┐
│  test_phone_        │
│  simulation.py      │
└──────────┬──────────┘
           │
           │ 3. Opens WebSocket
           │    ws://localhost:8000/media-stream
           ▼
┌──────────────────────┐
│  webhook_server.py   │  4. Connects to LiveKit
│  (/media-stream)     │     Creates room
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  LiveKit Room        │
│  (call-CA_TEST_...)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  agent.py            │  5. Joins room
│  (AI Agent)          │     Listens for audio
└──────────────────────┘
```

### Audio Flow:

```
Test Script → WebSocket → Webhook → LiveKit → Agent
   (440Hz)    (mulaw)     (PCM)     (PCM)    (Processes)

Agent → LiveKit → Webhook → WebSocket → Test Script
 (TTS)   (PCM)     (mulaw)  (base64)   (Receives)
```

---

## 🧪 Test Scenarios

### Scenario 1: Without Agent

```bash
# Only start webhook
python webhook_server.py

# Run test in another terminal
python test_phone_simulation.py
```

**Result:**
- ✅ Tests 1, 2, 4 will pass
- ⚠️  Test 3 will pass but won't receive audio responses
- This tests webhook functionality only

### Scenario 2: With Agent (Full Test)

```bash
# Terminal 1
python agent.py

# Terminal 2
python webhook_server.py

# Terminal 3
python test_phone_simulation.py
```

**Result:**
- ✅ All tests pass
- ✅ Receives audio responses from agent
- This tests the complete integration

### Scenario 3: Quick Validation

```bash
python webhook_server.py

# In another terminal
python test_phone_simulation.py --quick
```

**Result:**
- ✅ Tests basic endpoints only
- Very fast (< 3 seconds)
- Good for CI/CD or quick checks

---

## 🐛 Troubleshooting

### Error: Connection refused

**Symptom:**
```
❌ Error: Cannot connect to host localhost:8000
```

**Fix:**
Make sure `webhook_server.py` is running:
```bash
python webhook_server.py
```

### Error: Module not found

**Symptom:**
```
ModuleNotFoundError: No module named 'aiohttp'
```

**Fix:**
Install dependencies:
```bash
pip install aiohttp
# or
pip install -r requirements.txt
```

### No audio responses received

**Symptom:**
```
⚠️  No audio response received
```

**This is normal if:**
- agent.py is not running
- Agent hasn't joined the room yet
- LiveKit connection issues

**To fix:**
1. Make sure agent.py is running
2. Wait a few seconds after starting agent
3. Check agent logs for connection

### WebSocket errors

**Symptom:**
```
❌ WebSocket error: ...
```

**Check:**
1. webhook_server.py is running
2. Port 8000 is not blocked
3. No firewall issues
4. websockets package is installed

---

## 📈 Advanced Usage

### Test Different Scenarios

**Modify the test script to:**

1. **Test longer calls:**
   ```python
   # In test_phone_simulation.py, line ~140
   total_duration = 10  # Change to 10 seconds
   ```

2. **Test different audio:**
   ```python
   # In generate_test_audio() function
   frequency = 880  # Change tone frequency
   ```

3. **Test multiple concurrent calls:**
   Run multiple instances:
   ```bash
   python test_phone_simulation.py &
   python test_phone_simulation.py &
   python test_phone_simulation.py &
   ```

### Custom Test Data

Edit these constants in `test_phone_simulation.py`:

```python
WEBHOOK_URL = "http://localhost:8000"  # Change for remote testing
TEST_CALL_SID = "CA_TEST_123456789"    # Change call ID
TEST_FROM_NUMBER = "+15551234567"       # Change from number
TEST_TO_NUMBER = "+15559876543"         # Change to number
```

---

## ✅ Verification Checklist

After running the test, verify:

### In Test Output:
- [ ] All 4 tests show ✅ PASSED
- [ ] WebSocket connected successfully
- [ ] Audio chunks sent (150 chunks for 3 seconds)
- [ ] If agent running: Audio responses received
- [ ] Stop event sent successfully

### In webhook_server.py Logs:
- [ ] `📞 Incoming call: CA_TEST_123456789`
- [ ] `✓ Created room 'call-CA_TEST_123456789'`
- [ ] `📡 Media stream WebSocket connected`
- [ ] `🎬 Stream started`
- [ ] `✓ Connected to LiveKit room`
- [ ] `✓ Published phone audio track`

### In agent.py Logs (if running):
- [ ] `👤 Participant joined: phone-+15551234567`
- [ ] `🎤 Starting Realtime agent session`
- [ ] `✅ Realtime agent ready`

---

## 🎯 What This Proves

If all tests pass, it proves:

✅ **Webhook server is working**
- Responds to HTTP requests
- Generates valid TwiML
- Handles WebSocket connections

✅ **Audio pipeline works**
- Receives audio data
- Converts formats correctly
- Sends to LiveKit

✅ **Integration is ready**
- LiveKit connection works
- Room creation works
- Audio streaming works

✅ **Ready for real phone calls**
- All components functioning
- Can proceed to phone testing
- Production deployment ready

---

## 🚀 Next Steps After Successful Test

1. **✅ All tests passed locally?**
   → Test with ngrok + real phone call

2. **✅ ngrok test successful?**
   → Deploy to Render.com

3. **✅ Deployed successfully?**
   → Configure Twilio with production URL

4. **✅ Real calls working?**
   → You're done! 🎉

---

## 📚 Comparison: Simulated vs Real Call

| Aspect | Simulated Test | Real Phone Call |
|--------|---------------|-----------------|
| **Cost** | Free | Twilio charges apply |
| **Speed** | ~15 seconds | Real-time conversation |
| **Setup** | Just start servers | Needs ngrok or production |
| **Audio** | Generated sine wave | Real human voice |
| **Agent Response** | If agent running | If agent running |
| **Tests** | All components | All + actual phone network |
| **Good For** | Development, CI/CD | Final validation, demo |

**Recommendation:** Use simulated tests for development, real calls for final validation.

---

## 💡 Tips

1. **Run tests frequently** during development
2. **Use --quick** for fast iteration
3. **Use full test** before deploying
4. **Check both webhook and agent logs**
5. **Test with and without agent** to verify both work

---

## 🆘 Still Having Issues?

1. **Check server logs** - Most issues show up there
2. **Try quick test first** - Isolates the problem
3. **Verify all dependencies installed** - `pip install -r requirements.txt`
4. **Test one component at a time** - Webhook → WebSocket → Agent
5. **Check TESTING_WEBHOOK.md** - More detailed troubleshooting

---

## ✅ Summary

**YES!** You can test phone call functionality without a real phone:

```bash
# Start webhook
python webhook_server.py

# Run simulation (in another terminal)
python test_phone_simulation.py
```

**What you get:**
- Complete phone call simulation
- No Twilio account needed
- No ngrok needed
- No real phone needed
- Tests all functionality
- Fast feedback loop

**Perfect for:**
- Development
- Testing changes
- CI/CD pipelines
- Quick validation
- Before deploying

🎉 **Happy testing!**

