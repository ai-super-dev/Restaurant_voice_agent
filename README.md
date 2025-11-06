# Voice Phone Call Agent with LiveKit and Twilio

A scalable voice AI agent that supports 100+ concurrent calls with low latency (<1s) using LiveKit and Twilio.

## Architecture Overview

```
Phone Call → Twilio → SIP/WebRTC → LiveKit → AI Agent → Response
```

- **Twilio**: Handles phone number and call routing
- **LiveKit**: Manages real-time voice connections and AI agent processing
- **Agent**: Processes voice input and generates responses

## Prerequisites

- Python 3.9 or higher
- Twilio account with a US phone number
- LiveKit Cloud account (or self-hosted LiveKit server)
- OpenAI API key (for AI responses)
- ngrok or similar tunneling tool (for local development)

---

## Step 1: Set Up Twilio

### 1.1 Create Twilio Account
1. Go to https://www.twilio.com/try-twilio
2. Sign up for a free account
3. Verify your email and phone number

### 1.2 Get a US Phone Number
1. Go to **Phone Numbers** → **Manage** → **Buy a number**
2. Select **United States** as country
3. Check **Voice** capabilities
4. Purchase a number (free trial gives you credits)

### 1.3 Get Twilio Credentials
1. Go to **Console Dashboard**
2. Note down:
   - **Account SID** (starts with AC...)
   - **Auth Token** (click to reveal)
3. Keep these secure - you'll need them later

---

## Step 2: Set Up LiveKit

### 2.1 Create LiveKit Cloud Account
1. Go to https://cloud.livekit.io/
2. Sign up for a free account
3. Create a new project

### 2.2 Get LiveKit Credentials
1. Go to **Settings** → **Keys**
2. Create a new API Key/Secret pair
3. Note down:
   - **API Key** (starts with API...)
   - **API Secret** (long string)
   - **WebSocket URL** (wss://your-project.livekit.cloud)

### 2.3 Configure SIP for Twilio Integration
1. In LiveKit Cloud dashboard, go to **SIP**
2. Click **Create SIP Trunk**
3. Name it "Twilio"
4. You'll get a SIP URI - note this down (e.g., sip:abc123@sip.livekit.io)

---

## Step 3: Set Up OpenAI

1. Go to https://platform.openai.com/
2. Create an account or log in
3. Go to **API Keys**
4. Create a new API key
5. Copy and save it securely

---

## Step 4: Install and Configure the Project

### 4.1 Clone/Setup Project
```bash
# Navigate to your project directory
cd Ireland_Voice_Agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4.2 Configure Environment Variables
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` with your credentials:
   - Add Twilio Account SID and Auth Token
   - Add LiveKit URL, API Key, and API Secret
   - Add OpenAI API Key
   - Set your Twilio phone number

---

## Step 5: Connect Twilio to LiveKit

### 5.1 Start the Webhook Server
```bash
# In your project directory with venv activated
python webhook_server.py
```

This starts a server on port 8000.

### 5.2 Expose Local Server (for testing)
In a new terminal:
```bash
# Install ngrok from https://ngrok.com/
ngrok http 8000
```

Copy the HTTPS URL (e.g., https://abc123.ngrok.io)

### 5.3 Configure Twilio Webhook
1. Go to Twilio Console → **Phone Numbers** → **Manage** → **Active numbers**
2. Click on your purchased number
3. Scroll to **Voice Configuration**
4. Under "A CALL COMES IN":
   - Select **Webhook**
   - Enter: `https://your-ngrok-url.ngrok.io/incoming-call`
   - Method: **HTTP POST**
5. Click **Save**

---

## Step 6: Run the AI Agent

In a new terminal (keep webhook server running):
```bash
# Activate venv
venv\Scripts\activate

# Run the agent
python agent.py
```

The agent will:
- Connect to LiveKit
- Wait for incoming calls
- Handle multiple concurrent calls
- Process voice with low latency

---

## Step 7: Test the System

### 7.1 Make a Test Call
1. Call your Twilio phone number from any phone
2. You should hear the AI agent greeting you
3. Speak to the agent and it will respond

### 7.2 Monitor Performance
- Check terminal logs for latency metrics
- LiveKit dashboard shows active sessions
- Twilio console shows call logs

### 7.3 Load Testing (100+ concurrent calls)
- Use Twilio's load testing tools or third-party services
- Monitor CPU/memory usage
- Check LiveKit dashboard for connection quality

---

## Architecture for Scale and Low Latency

### Concurrency (100+ calls)
- **Async/await**: All I/O operations are asynchronous
- **Connection pooling**: Reuses LiveKit connections
- **Worker processes**: Can run multiple agent instances
- **LiveKit rooms**: Each call gets its own room for isolation

### Low Latency (<1s)
- **Streaming responses**: AI streams partial responses
- **VAD (Voice Activity Detection)**: Detects speech instantly
- **Optimized codecs**: Uses Opus codec for efficient audio
- **WebRTC**: Direct peer-to-peer where possible
- **Server location**: Use LiveKit regions close to users

### Optimizations Applied
1. **Voice streaming**: Real-time audio streaming without buffering
2. **Interrupt handling**: Can interrupt AI mid-sentence
3. **Connection reuse**: Maintains persistent LiveKit connections
4. **Efficient serialization**: Minimal data transformation
5. **OpenAI streaming**: Uses streaming API for faster responses

---

## Configuration Options

Edit `config.py` to customize:
- AI model (default: gpt-4o-mini for speed)
- Voice settings (default: Eleven Labs or OpenAI TTS)
- Agent personality and prompt
- Timeout settings
- Concurrency limits

---

## Troubleshooting

### Calls not connecting
- Check webhook URL is correct in Twilio
- Ensure webhook server is running
- Check ngrok is active
- Verify firewall allows incoming connections

### High latency
- Use LiveKit region closest to you
- Switch to faster AI model (gpt-4o-mini vs gpt-4)
- Reduce STT/TTS model complexity
- Check internet connection speed

### Agent not responding
- Check OpenAI API key is valid
- Verify LiveKit credentials
- Look for errors in terminal logs
- Check API rate limits

### Audio quality issues
- Ensure good internet connection
- Check microphone/speaker settings
- Verify codec settings in LiveKit
- Test with different phone networks

---

## Production Deployment

For production with 100+ concurrent calls:

1. **Deploy to cloud**:
   - Use AWS/GCP/Azure with auto-scaling
   - Deploy in region close to your users
   - Use managed LiveKit Cloud for reliability

2. **Remove ngrok**:
   - Use proper domain with SSL certificate
   - Point Twilio webhook to your domain

3. **Monitoring**:
   - Add logging (CloudWatch, Datadog, etc.)
   - Set up alerts for failures
   - Monitor latency metrics
   - Track concurrent call counts

4. **Load balancing**:
   - Run multiple agent instances
   - Use load balancer (ALB, nginx)
   - Scale based on CPU/memory usage

5. **Cost optimization**:
   - Monitor API usage
   - Use cheaper models where appropriate
   - Set up billing alerts

---

## Project Structure

```
Ireland_Voice_Agent/
├── agent.py              # Main AI agent with LiveKit integration
├── webhook_server.py     # Twilio webhook handler
├── config.py            # Configuration and settings
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .env                # Your actual credentials (don't commit!)
└── README.md           # This file
```

---

## Cost Estimates (POC)

- Twilio: ~$0.013/min for US calls
- LiveKit Cloud: Free tier covers 100+ concurrent for testing
- OpenAI: ~$0.002-0.01 per call (depending on length)

For 100 concurrent calls at 5 min each:
- Per hour: ~$39 (Twilio) + ~$6 (OpenAI) = ~$45/hour
- Free tier LiveKit should handle POC testing

---

## Next Steps

1. Complete the setup steps above
2. Test with a single call
3. Gradually increase concurrent calls
4. Monitor performance and latency
5. Optimize based on your specific use case
6. Plan production deployment

---

## Support

- LiveKit Docs: https://docs.livekit.io/
- Twilio Docs: https://www.twilio.com/docs
- LiveKit Agents SDK: https://docs.livekit.io/agents/

## License

MIT License - feel free to use for your POC and beyond!

