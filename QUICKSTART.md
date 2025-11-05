# Quick Start Guide (5 Minutes)

Get your voice agent running in 5 minutes!

## Prerequisites
- Python 3.9+
- Twilio account with US phone number
- LiveKit Cloud account
- OpenAI API key

If you don't have accounts yet, see [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup.

---

## Step 1: Install (1 minute)

```bash
# Navigate to project
cd Ireland_Voice_Agent

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Configure (2 minutes)

```bash
# Copy environment template
copy env.example .env  # Windows
# cp env.example .env  # Mac/Linux

# Edit .env with your text editor
notepad .env  # Windows
# nano .env  # Mac/Linux
```

Fill in your credentials:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxx...
TWILIO_AUTH_TOKEN=xxxxxxxxx...
TWILIO_PHONE_NUMBER=+15551234567

LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx...
LIVEKIT_API_SECRET=xxxxxxxxx...

OPENAI_API_KEY=sk-xxxxxxxxx...
```

**Test configuration:**
```bash
python test_setup.py
```

---

## Step 3: Start Services (2 minutes)

### Option A: Quick Start Script (Windows)
```bash
start.bat
```
This opens 3 windows automatically!

### Option B: Manual Start

**Terminal 1 - Webhook Server:**
```bash
python webhook_server.py
```

**Terminal 2 - ngrok:**
```bash
ngrok http 8000
```
Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

**Terminal 3 - AI Agent:**
```bash
python agent.py
```

---

## Step 4: Configure Twilio Webhook

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to: **Phone Numbers** → **Manage** → **Active numbers**
3. Click your phone number
4. Under "A CALL COMES IN":
   - Select: **Webhook**
   - URL: `https://YOUR-NGROK-URL.ngrok.io/incoming-call`
   - Method: **HTTP POST**
5. Click **Save**

---

## Step 5: Test! 🎉

1. **Call your Twilio number** from any phone
2. You should hear: "Connecting you to the AI assistant..."
3. Then: "Hello! I'm your AI assistant. How can I help you today?"
4. **Speak to the agent** - it will respond!

---

## Verify Everything Works

### Check Terminals
- **Terminal 1 (Webhook)**: Should show incoming call logs
- **Terminal 2 (ngrok)**: Should show HTTP requests
- **Terminal 3 (Agent)**: Should show conversation transcripts

### Check Metrics
Open in browser: http://localhost:8000/metrics

Should show:
```json
{
  "active_calls": 1,
  "max_concurrent_calls": 150,
  "utilization_percent": 0.67
}
```

---

## Common Issues

### "Configuration error: Missing required environment variables"
→ Check your `.env` file has all credentials filled in

### "Connection refused" when calling
→ Make sure all 3 terminals are running and ngrok URL is correct in Twilio

### High latency (>2 seconds)
→ Make sure you're using `gpt-4o-mini` in config (not `gpt-4o`)

### Agent doesn't respond
→ Check OpenAI API key is valid and has credits

---

## What's Next?

### Improve Performance
Read [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md) for:
- Reducing latency to <1s
- Scaling to 100+ concurrent calls
- Load testing strategies

### Production Deployment
See [PRODUCTION.md](PRODUCTION.md) for:
- AWS/GCP deployment
- Security best practices
- Monitoring and alerting

### Customize Agent
Edit `config.py` to change:
- Agent personality (SYSTEM_PROMPT)
- Greeting message
- AI model
- Voice settings

Example:
```python
# config.py
SYSTEM_PROMPT = """You are a friendly customer service agent for Acme Corp.
You help customers with order tracking and product questions.
Keep responses concise and helpful."""

AGENT_GREETING = "Thanks for calling Acme Corp! How can I help you today?"
```

---

## Architecture Overview

```
Your Phone
    ↓
Twilio (phone network)
    ↓
Webhook Server (your computer)
    ↓
LiveKit (media server)
    ↓
AI Agent (your computer)
    ↓
OpenAI (AI processing)
```

---

## Stop Services

Press `Ctrl+C` in each terminal to stop:
1. Agent
2. ngrok
3. Webhook server

Or just close all terminal windows.

---

## Costs (POC Testing)

Approximate costs for testing:
- **Twilio**: $0.013/min (~$0.39 for 30 min of testing)
- **LiveKit**: Free tier (10,000 participant-minutes/month)
- **OpenAI**: ~$0.01-0.02 per call (~$0.50 for 30 calls)

**Total for 30 test calls**: ~$1

---

## Getting Help

If stuck:
1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
2. Run `python test_setup.py` to diagnose issues
3. Check terminal logs for error messages
4. Review [Troubleshooting](SETUP_GUIDE.md#troubleshooting) section

---

## Next Steps Summary

✅ System is running
✅ Test call successful
✅ Agent responding

**Now:**
1. ✨ **Test latency**: Time how fast agent responds
2. 📊 **Monitor**: Watch the metrics endpoint
3. 🎯 **Customize**: Change agent personality
4. 🚀 **Scale**: Test with multiple calls
5. 📖 **Learn**: Read PERFORMANCE_GUIDE.md

---

**Congratulations! Your voice AI agent is live!** 🎉

Call your number again to test it more. The agent will:
- Respond to your questions
- Maintain conversation context
- Handle interruptions gracefully
- Work 24/7 without breaks

Ready to scale to 100+ calls? Check out [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md)!

