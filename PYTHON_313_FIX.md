# Python 3.13 Compatibility Fix

## Issue

When deploying to Render.com (or any platform using Python 3.13+), you may encounter:

```
ModuleNotFoundError: No module named 'audioop'
```

## Root Cause

**Python 3.13 removed the built-in `audioop` module** that was used for audio format conversion (mulaw ↔ PCM).

This affects the phone call integration which needs to convert audio between:
- **Twilio format:** mulaw, 8kHz, mono
- **LiveKit format:** PCM int16, 8-48kHz

## Solution

### ✅ Fixed in Latest Version

The code now uses `audioop-lts`, a maintained package that provides the same functionality:

**requirements.txt:**
```python
audioop-lts>=0.2.1  # audioop replacement for Python 3.13+
```

**webhook_server.py:**
```python
# Use audioop-lts for Python 3.13+ compatibility
try:
    import audioop
except ModuleNotFoundError:
    # Python 3.13+ removed audioop, use audioop-lts instead
    import audioop_lts as audioop
```

This provides **backward and forward compatibility**:
- ✅ Python 3.12 and earlier: Uses built-in `audioop`
- ✅ Python 3.13+: Uses `audioop-lts` package

## Deployment Steps

### 1. Ensure Latest Code

Make sure you have the updated files:
- `requirements.txt` includes `audioop-lts>=0.2.1`
- `webhook_server.py` has the compatibility import

### 2. Deploy to Render.com

```bash
git add requirements.txt webhook_server.py
git commit -m "Fix Python 3.13 compatibility - add audioop-lts"
git push
```

### 3. Verify Deployment

Check Render.com logs for successful startup:
```
✓ Configuration loaded successfully
🚀 Starting Voice Agent Webhook Server
```

## Local Testing

If you're using Python 3.13+ locally:

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Mac/Linux

# Install/update dependencies
pip install -r requirements.txt

# Should now include audioop-lts
pip list | grep audioop
# Output: audioop-lts    0.2.1
```

## Verification

### Check Python Version

**On Render.com:**
- Check build logs for Python version
- Look for: `Python 3.13.x`

**Locally:**
```bash
python --version
```

### Check Module Import

```python
# Test the import works
python -c "from webhook_server import audioop; print('audioop imported successfully')"
```

## Audio Conversion Functions Used

The following `audioop` functions are used in webhook_server.py:

1. **`audioop.ulaw2lin(data, width)`** - Convert mulaw to PCM
   - Used when receiving phone audio from Twilio

2. **`audioop.lin2ulaw(data, width)`** - Convert PCM to mulaw
   - Used when sending agent audio to Twilio

3. **`audioop.ratecv(data, width, nchannels, inrate, outrate, state)`** - Resample audio
   - Used to convert 48kHz (LiveKit) to 8kHz (Twilio)

4. **`audioop.tomono(data, width, lfactor, rfactor)`** - Convert stereo to mono
   - Used when agent audio is stereo but Twilio needs mono

All these functions are available in `audioop-lts` with the same API.

## Alternative Solutions (Not Recommended)

### Option 1: Pin Python Version to 3.12

**Not recommended** - You'd miss out on Python 3.13 improvements and security updates.

```yaml
# render.yaml (not recommended)
services:
  - type: web
    runtime: python
    pythonVersion: "3.12"
```

### Option 2: Use Different Audio Library

**More complex** - Would require rewriting audio conversion code.

Alternatives:
- `pydub` - Requires ffmpeg
- `soundfile` - Different API
- `wave` + manual conversion - More code

### Option 3: LiveKit SIP (Best for Production)

**Recommended for production** - No audio conversion needed!

Use LiveKit's built-in SIP trunk integration:
- No manual audio conversion
- More reliable
- Better audio quality
- Automatic scaling

See `PHONE_CALL_SETUP.md` for details.

## Timeline

- **Python 3.13.0** - Released October 2023
- **audioop removed** - PEP 594
- **audioop-lts created** - Community-maintained replacement
- **Fix applied** - November 2025 (this fix)

## Testing the Fix

### Test Locally (Python 3.13+)

```bash
# Install dependencies
pip install -r requirements.txt

# Start webhook server
python webhook_server.py

# Should start successfully without errors
# Look for: "🚀 Starting Voice Agent Webhook Server"
```

### Test on Render.com

1. **Deploy the fix:**
   ```bash
   git push
   ```

2. **Watch build logs:**
   - Should see: `Successfully installed audioop-lts-0.2.1`

3. **Watch deployment logs:**
   - Should see: `✓ Configuration loaded successfully`
   - Should NOT see: `ModuleNotFoundError: No module named 'audioop'`

4. **Test phone call:**
   - Call your Twilio number
   - Should connect successfully

## Related Issues

This fix resolves:
- ✅ `ModuleNotFoundError: No module named 'audioop'`
- ✅ Python 3.13+ compatibility
- ✅ Render.com deployment failures
- ✅ Any hosting platform using Python 3.13+

## Resources

- **PEP 594:** [Removing dead batteries from the standard library](https://peps.python.org/pep-0594/)
- **audioop-lts:** [PyPI Package](https://pypi.org/project/audioop-lts/)
- **Python 3.13 Release:** [What's New](https://docs.python.org/3.13/whatsnew/3.13.html)

## Summary

✅ **Fixed!** Your code now works with both Python 3.12 and Python 3.13+

**What changed:**
- Added `audioop-lts` to requirements.txt
- Updated import to handle both versions
- No changes to actual audio processing code

**What you need to do:**
1. Deploy the updated code
2. That's it! Should work now.

---

**Status:** ✅ Resolved  
**Impact:** Phone call integration now works on Python 3.13+  
**Backward compatible:** Yes (works with Python 3.12 and earlier too)

