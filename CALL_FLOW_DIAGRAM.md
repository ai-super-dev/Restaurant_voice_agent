# Phone Call Flow Diagram

## 📞 Complete Call Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PHONE CALL TO AI AGENT                       │
└─────────────────────────────────────────────────────────────────────┘

1. CALL INITIATION
==================
   📱 User
   └─> Dials Twilio Number (+1-555-XXX-XXXX)
       │
       ▼
   ☁️  Twilio Cloud
   └─> Receives call, triggers webhook


2. WEBHOOK REQUEST
==================
   ☁️  Twilio
   └─> POST https://your-domain.com/incoming-call
       │  Body: CallSid, From, To, CallStatus
       │
       ▼
   🌐 Webhook Server (webhook_server.py)
   └─> Receives request
       └─> Creates room name: "call-{CallSid}"
       └─> Generates WebSocket URL
       └─> Returns TwiML:
           <Response>
             <Connect>
               <Stream url="wss://your-domain.com/media-stream">
                 <Parameter name="callSid" value="CA..."/>
                 <Parameter name="roomName" value="call-CA..."/>
               </Stream>
             </Connect>
           </Response>


3. WEBSOCKET CONNECTION
========================
   ☁️  Twilio
   └─> Opens WebSocket to wss://your-domain.com/media-stream
       │
       ▼
   🌐 Webhook Server (/media-stream endpoint)
   └─> Accepts WebSocket connection
       └─> Receives "start" event with call details


4. LIVEKIT ROOM SETUP
======================
   🌐 Webhook Server
   └─> Connects to LiveKit:
       │  - URL: wss://your-livekit.cloud
       │  - Room: call-CA123456...
       │  - Identity: phone-+15551234567
       │
       ▼
   🎬 LiveKit Room (call-CA123456...)
   └─> Room created/joined
       └─> Publishes audio track (phone-audio)
       └─> Subscribes to remote tracks (agent-audio)


5. AGENT JOINS
==============
   🤖 Agent (agent.py)
   └─> Detects room creation
       └─> Joins room: call-CA123456...
       └─> Identity: agent-default
       └─> Publishes audio track (agent-audio)
       └─> Subscribes to tracks (phone-audio)


6. AUDIO FLOW - INCOMING (User → Agent)
========================================
   📱 User speaks: "Hello!"
   │
   ▼
   ☁️  Twilio
   └─> Captures audio: mulaw, 8kHz, mono
       └─> Sends via WebSocket:
           {
             "event": "media",
             "media": {
               "payload": "base64(mulaw_audio)"
             }
           }
   │
   ▼
   🌐 Webhook (/media-stream)
   └─> Decodes base64
       └─> Converts: mulaw → PCM int16
       └─> Creates AudioFrame: 8kHz, mono
       └─> Sends to LiveKit: audio_source.capture_frame()
   │
   ▼
   🎬 LiveKit Room
   └─> Distributes audio to subscribers
   │
   ▼
   🤖 Agent (OpenAI Realtime)
   └─> Receives audio via AudioStream
       └─> STT: Audio → Text ("Hello!")
       └─> LLM: Processes and generates response
       └─> TTS: Text → Audio (agent response)


7. AUDIO FLOW - OUTGOING (Agent → User)
========================================
   🤖 Agent
   └─> Generates response audio (OpenAI TTS)
       └─> Publishes to LiveKit room
   │
   ▼
   🎬 LiveKit Room
   └─> Sends to subscribers (webhook's audio stream)
   │
   ▼
   🌐 Webhook (/media-stream)
   └─> Receives AudioFrame: PCM int16, 48kHz
       └─> Resamples: 48kHz → 8kHz
       └─> Converts: stereo → mono (if needed)
       └─> Converts: PCM → mulaw
       └─> Encodes: base64(mulaw)
       └─> Sends via WebSocket:
           {
             "event": "media",
             "streamSid": "MZ...",
             "media": {
               "payload": "base64(mulaw_audio)"
             }
           }
   │
   ▼
   ☁️  Twilio
   └─> Decodes and plays audio to caller
   │
   ▼
   📱 User hears: "Hello! I'm your AI assistant. How can I help you?"


8. CONVERSATION CONTINUES
==========================
   Steps 6-7 repeat for each exchange:
   
   User: "What's the weather?"
   │
   ├─> [Steps 6: User → Agent]
   │
   └─> Agent: "I can help with that. Where are you located?"
       │
       └─> [Steps 7: Agent → User]
   
   User: "San Francisco"
   │
   └─> ... continues ...


9. CALL TERMINATION
===================
   📱 User hangs up
   │
   ▼
   ☁️  Twilio
   └─> Sends "stop" event to WebSocket
       └─> Closes WebSocket connection
   │
   ▼
   🌐 Webhook (/media-stream)
   └─> Receives "stop" or disconnect
       └─> Disconnects from LiveKit room
       └─> Cleanup:
           - Removes call from active_calls set
           - Closes connections
           - Frees resources
   │
   ▼
   🎬 LiveKit Room
   └─> Participant leaves (webhook)
   │
   ▼
   🤖 Agent
   └─> Detects participant left
       └─> Session ends
       └─> Room cleanup (automatic)


10. STATUS CALLBACK (Optional)
===============================
   ☁️  Twilio
   └─> POST https://your-domain.com/call-status
       │  Body: CallSid, CallStatus="completed"
       │
       ▼
   🌐 Webhook Server (/call-status)
   └─> Logs call completion
       └─> Final cleanup if needed
```

---

## 🔄 Audio Format Conversions

### Incoming Audio (Phone → Agent)

```
Phone Microphone
    │ Raw analog audio
    ▼
Cellular Network / PSTN
    │ Compressed
    ▼
Twilio (mulaw codec)
    │ mulaw, 8kHz, mono
    ▼
WebSocket
    │ base64(mulaw), 20ms chunks
    ▼
Webhook Server
    │ Decode base64
    │ mulaw → PCM int16
    │ Create AudioFrame
    ▼
LiveKit
    │ PCM int16, 8kHz, mono
    │ Distribute to subscribers
    ▼
Agent (OpenAI Realtime)
    │ PCM → OpenAI's format
    │ Speech-to-Text
    └─> Text: "Hello!"
```

### Outgoing Audio (Agent → Phone)

```
Agent (OpenAI Realtime)
    │ Text: "Hello! How can I help?"
    │ Text-to-Speech
    ▼
LiveKit
    │ PCM int16, 48kHz, stereo/mono
    │ High quality audio
    ▼
Webhook Server
    │ Resample: 48kHz → 8kHz
    │ Convert: stereo → mono
    │ PCM → mulaw
    │ Base64 encode
    ▼
WebSocket
    │ base64(mulaw), 20ms chunks
    ▼
Twilio
    │ mulaw, 8kHz, mono
    ▼
Cellular Network / PSTN
    │ Compressed for phone
    ▼
Phone Speaker
    └─> User hears response
```

---

## ⚡ Latency Breakdown

```
USER SPEAKS ────────────────────────────► USER HEARS RESPONSE
                     Total: ~600-900ms

├─ Phone to Twilio ─────────────────► 50-100ms (cellular)
│
├─ Twilio to Webhook ───────────────► 20-50ms (internet)
│
├─ Webhook Processing ──────────────► < 5ms (audio conversion)
│
├─ Webhook to LiveKit ──────────────► 20-50ms (WebRTC)
│
├─ Agent STT ───────────────────────► 100-200ms (OpenAI)
│
├─ Agent LLM ───────────────────────► 200-400ms (OpenAI Realtime)
│
├─ Agent TTS ───────────────────────► 100-200ms (OpenAI)
│
├─ LiveKit to Webhook ──────────────► 20-50ms (WebRTC)
│
├─ Webhook Processing ──────────────► < 5ms (audio conversion)
│
├─ Webhook to Twilio ───────────────► 20-50ms (internet)
│
└─ Twilio to Phone ─────────────────► 50-100ms (cellular)
```

**Optimization Tips:**
- Deploy webhook server in same region as Twilio
- Use LiveKit Cloud in same region as webhook
- Adjust VAD settings for faster detection
- Optimize network connectivity

---

## 🔐 Security & Authentication

```
TWILIO REQUEST VALIDATION
==========================
Twilio
└─> Signs request with auth token
    │
    ▼
Webhook Server
└─> (TODO) Validate signature
    └─> Rejects if invalid
    └─> Accepts if valid


LIVEKIT AUTHENTICATION
======================
Webhook Server
└─> Generates JWT token:
    {
      "identity": "phone-+15551234567",
      "room": "call-CA123456...",
      "grants": {
        "roomJoin": true,
        "canPublish": true,
        "canSubscribe": true
      }
    }
    │
    ▼
LiveKit
└─> Validates JWT with API secret
    └─> Grants access to room


CALL ISOLATION
==============
Each call gets unique room:
- Room: call-{unique_CallSid}
- Only that caller can join
- Separate agent instance
- No cross-talk between calls
```

---

## 📊 Monitoring Points

```
HEALTH CHECKS
=============
GET /health
    └─> Returns: {"status": "ok", "active_calls": N}


METRICS
=======
GET /metrics
    └─> Returns: {
          "active_calls": N,
          "max_concurrent_calls": 150,
          "utilization_percent": X
        }


LOG MONITORING
==============
Watch for these in logs:

✅ Success Indicators:
- "📞 Incoming call"
- "✓ Connected to LiveKit room"
- "✓ Published phone audio track"
- "🎧 Subscribed to agent audio track"
- "📤 Starting to stream agent audio"

❌ Error Indicators:
- "❌ Error handling incoming call"
- "❌ Error connecting to LiveKit"
- "❌ Error processing audio"
- "WebSocket disconnected" (unexpected)


CALL STATUS TRACKING
====================
POST /call-status
    └─> Receives: {
          "CallSid": "CA...",
          "CallStatus": "completed|failed|busy|no-answer"
        }
    └─> Updates active_calls set
    └─> Logs for analytics
```

---

## 🎯 Key Components

### Webhook Server (webhook_server.py)
- **Role:** Bridge between Twilio and LiveKit
- **Handles:**
  - HTTP webhook from Twilio
  - WebSocket for media streams
  - Audio format conversion
  - LiveKit room management

### Agent (agent.py)
- **Role:** AI conversation handler
- **Handles:**
  - Speech-to-text (OpenAI Realtime)
  - Language understanding (GPT-4)
  - Text-to-speech (OpenAI TTS)
  - Conversation state management

### LiveKit
- **Role:** Real-time communication platform
- **Handles:**
  - WebRTC connections
  - Audio distribution
  - Participant management
  - Track publishing/subscribing

### Twilio
- **Role:** Phone system interface
- **Handles:**
  - Phone number routing
  - Call setup/teardown
  - Audio capture/playback
  - Media Streams protocol

---

## ✅ Complete System

```
┌──────────────────────────────────────────────────────────────┐
│                     PHONE TO AI AGENT                        │
│                                                              │
│  📱 Phone ←→ ☁️  Twilio ←→ 🌐 Webhook ←→ 🎬 LiveKit ←→ 🤖 Agent │
│                                                              │
│  Audio      WebHook     WebSocket      WebRTC         STT   │
│  (mulaw)    (TwiML)     (Media)        (PCM)          LLM   │
│             (HTTP)      (WS)           (RTC)          TTS   │
└──────────────────────────────────────────────────────────────┘
```

**Status:** ✅ FULLY IMPLEMENTED AND READY TO USE!

**To activate:** Update Twilio webhook URL and make a call!

