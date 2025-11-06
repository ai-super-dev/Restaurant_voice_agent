# API Fix - OpenAI Realtime Configuration

## Issue Fixed

**Error:** `AttributeError: module 'livekit.plugins.openai.realtime' has no attribute 'ServerVadOptions'`

## Root Cause

The initial implementation used an incorrect class name `ServerVadOptions` which doesn't exist in the LiveKit OpenAI plugin.

## Solution

Use the correct class `TurnDetection` from `livekit.plugins.openai.realtime.realtime_model`.

### Correct API Usage

```python
from livekit.agents import voice
from livekit.plugins import openai, silero
from livekit.plugins.openai.realtime.realtime_model import TurnDetection

# Create RealtimeModel with turn detection
realtime_model = openai.realtime.RealtimeModel(
    voice=Config.VOICE_MODEL,
    temperature=0.8,
    modalities=["text", "audio"],
    turn_detection=TurnDetection(
        type="server_vad",           # Required: specify VAD type
        threshold=0.5,               # Voice detection sensitivity
        prefix_padding_ms=300,       # Audio captured before speech
        silence_duration_ms=200,     # Silence duration to end turn
    ),
)

# Create voice.Agent with Realtime Model (replaces STT+LLM+TTS)
agent = voice.Agent(
    instructions=Config.SYSTEM_PROMPT,
    llm=realtime_model,              # Pass RealtimeModel as LLM
    vad=silero.VAD.load(
        min_speech_duration=0.05,    # 50ms
        min_silence_duration=0.2,    # 200ms
    ),
)

# Create session and start
session = voice.AgentSession()
await session.start(agent, room=ctx.room)

# Say greeting
await session.say(Config.AGENT_GREETING)
```

## Key Changes

1. **Import the correct class:**
   - ❌ `openai.realtime.ServerVadOptions` (doesn't exist)
   - ✅ `TurnDetection` from `openai.realtime.realtime_model`

2. **Set VAD type:**
   - Added required parameter: `type="server_vad"`

3. **Use voice.Agent with RealtimeModel:**
   - Create `RealtimeModel` without `instructions` parameter
   - Pass `RealtimeModel` as `llm` parameter to `voice.Agent`
   - `voice.Agent` accepts `instructions` parameter
   - Use `voice.AgentSession()` to start the session

4. **Key insight:**
   - `voice.Agent` can accept `llm.RealtimeModel` as the `llm` parameter
   - This replaces the need for separate STT, LLM, and TTS components
   - Instructions are set on `voice.Agent`, not on `RealtimeModel`

## TurnDetection Parameters

Available parameters for `TurnDetection`:

- `type`: `"server_vad"` or `"semantic_vad"` (required)
- `threshold`: Voice detection sensitivity (0.0-1.0, default 0.5)
- `prefix_padding_ms`: Audio before speech starts (default 300)
- `silence_duration_ms`: Silence to end turn (default 200)
- `create_response`: Auto-create response (optional)
- `interrupt_response`: Allow interruptions (optional)
- `eagerness`: Response eagerness level (optional: "low", "medium", "high", "auto")

## Performance Impact

✅ **No performance impact** - This was just an API naming issue.

The latency optimization is still achieved:
- **Target:** <1 second
- **Expected:** 300-700ms
- **Full-duplex:** Enabled

## Testing

After this fix, the agent should start without errors:

```bash
python agent.py
```

Expected output:
```
🎙️  AI VOICE AGENT WITH LIVEKIT (REALTIME API)
✓ Agent is ready with <1s latency optimization!
```

Then test in LiveKit Agents Playground to verify the low latency.

## Files Updated

1. `agent.py` - Fixed the API usage
2. `PERFORMANCE_GUIDE.md` - Updated documentation with correct API
3. `API_FIX_NOTES.md` - This file (for reference)

---

**Status:** ✅ Fixed and ready to test

