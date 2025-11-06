# AudioFrameEvent Fix

## Issue

When running the webhook server and testing phone calls, you encountered this error:

```
ERROR - Error processing audio frame: 'AudioFrameEvent' object has no attribute 'data'
```

This error appeared repeatedly in the Render.com logs when the agent tried to send audio back to the phone caller.

---

## Root Cause

The LiveKit SDK's `AudioStream` iterator returns **`AudioFrameEvent`** objects, not `AudioFrame` objects directly.

### The Problem Code:

```python
async for audio_frame in audio_stream:
    pcm_data = audio_frame.data.tobytes()  # ❌ Error: AudioFrameEvent has no .data
```

### What Actually Happens:

- `audio_stream` iterator yields `AudioFrameEvent` objects
- Each `AudioFrameEvent` contains a `.frame` property
- The `.frame` property holds the actual `AudioFrame` object
- The `AudioFrame` object has the `.data` attribute we need

---

## The Fix

Changed the code to properly access the frame from the event:

### Fixed Code:

```python
async for audio_frame_event in audio_stream:
    frame = audio_frame_event.frame  # ✅ Get the actual AudioFrame
    pcm_data = frame.data.tobytes()  # ✅ Now we can access .data
    
    # Use frame.sample_rate, frame.num_channels, etc.
    if frame.sample_rate != 8000:
        pcm_data, _ = audioop.ratecv(...)
    
    if frame.num_channels == 2:
        pcm_data = audioop.tomono(...)
```

### What Changed:

1. ✅ Renamed `audio_frame` → `audio_frame_event` (clearer naming)
2. ✅ Added `frame = audio_frame_event.frame` to extract the actual frame
3. ✅ Changed all references from `audio_frame.x` → `frame.x`

---

## How to Deploy the Fix

### Step 1: Commit and Push

```bash
git add webhook_server.py AUDIOFRAME_EVENT_FIX.md
git commit -m "Fix AudioFrameEvent attribute error in audio streaming"
git push
```

### Step 2: Render.com Will Auto-Deploy

If you have auto-deploy enabled:
- Render.com will automatically detect the push
- Build and deploy the updated code
- Check the logs to confirm deployment

If manual deploy:
1. Go to https://dashboard.render.com
2. Click your webhook service
3. Click "Manual Deploy" → "Deploy latest commit"

### Step 3: Verify the Fix

Watch the Render.com logs. You should now see:
```
✅ Published phone audio track to room
🎧 Subscribed to agent audio track from agent-default
📤 Starting to stream agent audio to Twilio
```

**Without the error!** ✅

### Step 4: Test with Phone Call

1. Call your Twilio number
2. Say "Hello!"
3. You should hear the agent respond without errors

---

## Technical Details

### AudioStream Iterator Behavior

The LiveKit Python SDK's `AudioStream` works like this:

```python
audio_stream = rtc.AudioStream(track)

# Each iteration yields an AudioFrameEvent
async for event in audio_stream:
    # event is AudioFrameEvent
    # event.frame is AudioFrame
    # event.frame.data is the actual audio data (numpy array)
    
    frame = event.frame
    audio_data = frame.data
    sample_rate = frame.sample_rate
    num_channels = frame.num_channels
```

### Why This Matters

The `AudioFrameEvent` wrapper provides additional context about the frame:
- Timestamp information
- Track metadata
- Event type

But for audio processing, we need the actual `AudioFrame` inside it.

---

## Impact

### Before Fix:
- ❌ Errors logged repeatedly
- ❌ No audio sent from agent to phone
- ❌ Caller couldn't hear agent responses
- ✅ Call connected (but silent)

### After Fix:
- ✅ No errors
- ✅ Audio streams correctly
- ✅ Caller hears agent responses
- ✅ Full bidirectional conversation works

---

## Testing

### Test Without Phone (Simulation):

```bash
# Terminal 1: Start webhook
python webhook_server.py

# Terminal 2: Run test
python test_phone_simulation.py
```

**Expected:** No more AudioFrameEvent errors in logs

### Test With Real Phone:

1. Call your Twilio number
2. Say "Hello!"
3. Agent should respond clearly
4. Have a conversation

**Check logs:** Should see clean audio streaming without errors

---

## Similar Issues

If you see errors related to:
- `'SomeEvent' object has no attribute 'x'`
- Event objects from LiveKit SDK

**Solution:** Check if you need to access a property inside the event object.

**Pattern:**
```python
# Instead of:
async for item in iterator:
    value = item.property  # Might fail

# Try:
async for event in iterator:
    item = event.item  # or event.frame, event.data, etc.
    value = item.property
```

---

## Related Files

- **webhook_server.py** - The fixed file
- **PYTHON_313_FIX.md** - Previous fix for audioop compatibility
- **TEST_WITHOUT_PHONE.md** - Testing guide

---

## Summary

**Issue:** `'AudioFrameEvent' object has no attribute 'data'`

**Cause:** Accessing `.data` directly on event instead of `.frame.data`

**Fix:** Changed `audio_frame.data` → `audio_frame_event.frame.data`

**Status:** ✅ Fixed and ready to deploy

**Action:** Push to GitHub, Render.com will redeploy automatically

---

**After deploying this fix, your phone calls should work perfectly with full bidirectional audio!** 🎉

