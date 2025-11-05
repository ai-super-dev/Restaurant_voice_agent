# Detailed Setup Guide for Voice Agent

This guide provides step-by-step instructions for setting up your voice agent from scratch.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Account Setup](#account-setup)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the System](#running-the-system)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.9+** (Download from https://www.python.org/)
- **Git** (optional, for version control)
- **ngrok** (for local testing - Download from https://ngrok.com/)

### Required Accounts
- Twilio account (free trial available)
- LiveKit Cloud account (free tier available)
- OpenAI account with API access

---

## Account Setup

### Step 1: Twilio Setup (15 minutes)

#### 1.1 Create Account
1. Go to https://www.twilio.com/try-twilio
2. Click "Sign up"
3. Fill in your details:
   - Email address
   - Password
   - Phone number (for verification)
4. Verify your email
5. Complete phone verification

#### 1.2 Get Free Credits
- Free trial includes $15 in credits
- Enough for ~1000 minutes of testing
- No credit card required for trial

#### 1.3 Purchase Phone Number
1. In Twilio Console, go to **Phone Numbers** → **Buy a number**
2. Select **United States** from country dropdown
3. Check **Voice** capability
4. Optional: Check **SMS** if you want text capabilities
5. Click **Search**
6. Choose any number from the results
7. Click **Buy** (uses trial credits, costs ~$1/month)
8. Confirm purchase

#### 1.4 Get Credentials
1. Go to Twilio Console homepage
2. Find "Account Info" section
3. Copy these values:
   - **Account SID** (starts with "AC...")
   - **Auth Token** (click eye icon to reveal)
4. Copy your phone number (format: +1234567890)

---

### Step 2: LiveKit Cloud Setup (10 minutes)

#### 2.1 Create Account
1. Go to https://cloud.livekit.io/
2. Click "Sign up"
3. Choose sign-up method:
   - GitHub
   - Google
   - Email
4. Complete verification

#### 2.2 Create Project
1. After login, click "Create Project"
2. Enter project name (e.g., "voice-agent-poc")
3. Select region closest to you:
   - US: `us-west-2` or `us-east-1`
   - EU: `eu-central-1`
   - Asia: `ap-southeast-1`
4. Click "Create"

#### 2.3 Get API Credentials
1. In project dashboard, go to **Settings** → **Keys**
2. Click "Create New Key Pair"
3. Enter name: "agent-key"
4. Copy immediately (shown only once):
   - **API Key** (starts with "API...")
   - **API Secret** (long random string)
5. Store securely

#### 2.4 Get WebSocket URL
1. In project dashboard, find **WebSocket URL**
2. Format: `wss://your-project-name.livekit.cloud`
3. Copy this URL

#### 2.5 Note on Free Tier
- Free tier includes:
  - 10,000 participant minutes/month
  - Unlimited rooms
  - Standard SLA
- Sufficient for POC testing

---

### Step 3: OpenAI Setup (5 minutes)

#### 3.1 Create Account
1. Go to https://platform.openai.com/
2. Click "Sign up"
3. Choose sign-up method
4. Verify email

#### 3.2 Add Payment Method
1. Go to **Settings** → **Billing**
2. Click "Add payment method"
3. Add credit card
4. Set usage limit (e.g., $10/month for testing)

#### 3.3 Get API Key
1. Go to **API Keys** section
2. Click "Create new secret key"
3. Name it: "voice-agent"
4. Copy the key (starts with "sk-...")
5. Store securely - shown only once!

---

## Installation

### Step 1: Setup Project Directory

```bash
# Open Command Prompt or PowerShell
cd E:\Working_direction\Ireland_Voice_Agent
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Your prompt should now show (venv)
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# This will take 2-5 minutes
```

### Step 4: Verify Installation

```bash
# Check if livekit is installed
python -c "import livekit; print('LiveKit OK')"

# Check if other packages work
python -c "import fastapi; import twilio; print('All packages OK')"
```

---

## Configuration

### Step 1: Create .env File

```bash
# Copy the example file
copy env.example .env
```

### Step 2: Edit .env File

Open `.env` in your text editor and fill in your credentials:

```env
# Paste your Twilio credentials
TWILIO_ACCOUNT_SID=AC12345...  # From Twilio Console
TWILIO_AUTH_TOKEN=abc123...     # From Twilio Console
TWILIO_PHONE_NUMBER=+15551234567  # Your Twilio number

# Paste your LiveKit credentials
LIVEKIT_URL=wss://your-project.livekit.cloud  # From LiveKit dashboard
LIVEKIT_API_KEY=API123...       # From LiveKit Settings → Keys
LIVEKIT_API_SECRET=secret123... # From LiveKit Settings → Keys

# Paste your OpenAI key
OPENAI_API_KEY=sk-abc123...     # From OpenAI dashboard

# These can stay as defaults
AGENT_NAME=AI Assistant
AGENT_GREETING=Hello! I'm your AI assistant. How can I help you today?
WEBHOOK_PORT=8000
WEBHOOK_HOST=0.0.0.0
MAX_CONCURRENT_CALLS=150
ENABLE_METRICS=true
LOG_LEVEL=INFO
```

### Step 3: Verify Configuration

```bash
# Test configuration
python -c "from config import Config; Config.validate(); print('Config OK')"
```

You should see: "✓ Configuration loaded successfully"

---

## Running the System

### Step 1: Start Webhook Server

Open **Terminal 1**:

```bash
# Activate venv
cd E:\Working_direction\Ireland_Voice_Agent
venv\Scripts\activate

# Start webhook server
python webhook_server.py
```

You should see:
```
🚀 Starting Voice Agent Webhook Server
Host: 0.0.0.0
Port: 8000
```

Keep this terminal running.

### Step 2: Start ngrok (for local testing)

Open **Terminal 2**:

```bash
# Start ngrok
ngrok http 8000
```

You should see:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

Keep this terminal running.

### Step 3: Configure Twilio Webhook

1. Go to Twilio Console
2. Navigate to **Phone Numbers** → **Manage** → **Active numbers**
3. Click on your phone number
4. Scroll to **Voice & Fax** section
5. Under "A CALL COMES IN":
   - Select **Webhook**
   - Enter: `https://YOUR-NGROK-URL.ngrok.io/incoming-call`
   - Method: **HTTP POST**
6. Under "CALL STATUS CHANGES":
   - Enter: `https://YOUR-NGROK-URL.ngrok.io/call-status`
   - Method: **HTTP POST**
7. Click **Save**

### Step 4: Start AI Agent

Open **Terminal 3**:

```bash
# Activate venv
cd E:\Working_direction\Ireland_Voice_Agent
venv\Scripts\activate

# Start agent
python agent.py
```

You should see:
```
🎙️  AI VOICE AGENT WITH LIVEKIT
✓ Agent is ready and waiting for calls...
```

Keep this terminal running.

---

## Testing

### Test 1: Single Call

1. Call your Twilio phone number from any phone
2. You should hear: "Connecting you to the AI assistant..."
3. Then: "Hello! I'm your AI assistant. How can I help you today?"
4. Speak to the agent
5. The agent should respond

**Check Terminals:**
- Terminal 1 (webhook): Should show incoming call log
- Terminal 3 (agent): Should show conversation logs

### Test 2: Check Latency

While on a call, measure response time:
1. Say something short: "Hello"
2. Measure time until agent starts responding
3. Should be < 1 second for good latency
4. If > 2 seconds, see troubleshooting section

### Test 3: Monitor System

In a browser, go to:
- http://localhost:8000/metrics - See active calls
- http://localhost:8000/health - Check system health

### Test 4: Multiple Concurrent Calls

1. Get friends/colleagues to call simultaneously
2. Or use load testing service
3. Monitor metrics endpoint
4. Check agent logs for all sessions

---

## Troubleshooting

### Issue: "Configuration error: Missing required environment variables"

**Solution:**
1. Check `.env` file exists
2. Verify all credentials are filled in
3. No quotes around values
4. No spaces in variable names

### Issue: Webhook server starts but calls don't connect

**Solution:**
1. Verify ngrok is running
2. Check ngrok URL matches Twilio webhook
3. Ensure webhook URL ends with `/incoming-call`
4. Check Twilio webhook uses HTTPS, not HTTP

### Issue: Agent doesn't respond to voice

**Solution:**
1. Check OpenAI API key is valid
2. Verify LiveKit credentials are correct
3. Check microphone works on your phone
4. Look for errors in agent terminal

### Issue: High latency (>2 seconds)

**Solutions:**
1. Switch to faster OpenAI model in config.py:
   ```python
   OPENAI_MODEL = "gpt-4o-mini"  # Fastest
   ```
2. Use LiveKit region closer to you
3. Check internet connection speed
4. Reduce VAD sensitivity in agent.py

### Issue: "Connection refused" when calling

**Solutions:**
1. Ensure all three terminals are running
2. Check firewall isn't blocking ports
3. Verify ngrok is forwarding correctly:
   - Visit ngrok web interface: http://localhost:4040
4. Check webhook server logs for errors

### Issue: Agent cuts off while speaking

**Solution:**
Increase silence duration in agent.py:
```python
min_silence_duration=0.5,  # Increased from 0.3
```

### Issue: Multiple agents responding

**Solution:**
Ensure only ONE agent.py instance is running:
```bash
# Check running processes
tasklist | findstr python

# Kill duplicate if needed
```

---

## Monitoring & Logs

### Check Active Calls
```bash
# In browser
http://localhost:8000/metrics
```

Shows:
- `active_calls`: Current number of calls
- `max_concurrent_calls`: Maximum allowed
- `utilization_percent`: Load percentage

### View Logs

**Webhook Server Logs:**
- See in Terminal 1
- Shows incoming calls, room creation

**Agent Logs:**
- See in Terminal 3
- Shows transcriptions, responses, sessions

**Increase Log Detail:**
Edit `.env`:
```env
LOG_LEVEL=DEBUG
```

---

## Next Steps

After successful testing:

1. **Load Testing**: Test with 10, 50, 100 concurrent calls
2. **Customize Agent**: Edit `config.py` to change personality
3. **Add Features**: Extend agent.py for your use case
4. **Production Deployment**: See README.md for production guide
5. **Monitor Costs**: Check billing in Twilio, LiveKit, OpenAI dashboards

---

## Getting Help

If you encounter issues:

1. Check terminal logs for errors
2. Review this troubleshooting section
3. Check official documentation:
   - LiveKit: https://docs.livekit.io/
   - Twilio: https://www.twilio.com/docs
   - LiveKit Agents: https://docs.livekit.io/agents/

---

## Quick Reference

### Start All Services (Summary)

```bash
# Terminal 1: Webhook Server
cd E:\Working_direction\Ireland_Voice_Agent
venv\Scripts\activate
python webhook_server.py

# Terminal 2: ngrok
ngrok http 8000

# Terminal 3: Agent
cd E:\Working_direction\Ireland_Voice_Agent
venv\Scripts\activate
python agent.py
```

### Stop All Services

- Press `Ctrl+C` in each terminal
- Close ngrok
- Deactivate venv: `deactivate`

---

Good luck with your voice agent! 🎉

