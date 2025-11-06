# Deployment Guide - LiveKit SIP Version

## 🎯 Goal

Deploy your AI voice agent with LiveKit SIP for ultra-low latency phone calls (500-700ms).

---

## 📋 Prerequisites Checklist

Before deploying, ensure you have:

- [ ] **LiveKit Cloud account** with SIP/Telephony enabled
- [ ] **Twilio account** with a phone number
- [ ] **OpenAI API key** with Realtime API access
- [ ] **Render.com account** (or similar hosting)
- [ ] **Git repository** with your code

---

## 🚀 Deployment Steps

### Step 1: Prepare Environment Variables

Create a list of your credentials:

```bash
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxx
LIVEKIT_API_SECRET=your_secret_key
LIVEKIT_SIP_DOMAIN=sip.livekit.cloud

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+16266813821

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional
VOICE_MODEL=alloy
LOG_LEVEL=INFO
MAX_CONCURRENT_CALLS=150
```

---

### Step 2: Deploy Webhook Server

#### On Render.com:

1. **Go to:** https://dashboard.render.com

2. **Click:** New + → Web Service

3. **Connect Repository:**
   - Connect your GitHub/GitLab repo
   - Or paste repository URL

4. **Configure Service:**
   ```
   Name: voice-agent-webhook
   Runtime: Python 3
   Region: US West (or closest to your users)
   Branch: main
   ```

5. **Build Settings:**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: python webhook_server.py
   ```

6. **Environment Variables:**
   - Click "Advanced" → "Add Environment Variable"
   - Add ALL variables from Step 1
   - Double-check spelling!

7. **Instance Type:**
   - Free tier: For testing only
   - Starter ($7/mo): For light production
   - Standard ($25/mo): Recommended for production

8. **Click:** Create Web Service

9. **Wait:** 3-5 minutes for deployment

10. **Copy URL:** `https://voice-agent-webhook-xxxx.onrender.com`

---

### Step 3: Deploy Agent Worker

#### On Render.com:

1. **Go to:** Dashboard → New + → Background Worker

2. **Connect:** Same repository as webhook

3. **Configure Service:**
   ```
   Name: voice-agent-worker
   Runtime: Python 3
   Region: Same as webhook
   Branch: main
   ```

4. **Build Settings:**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: python agent.py
   ```

5. **Environment Variables:**
   - Add ALL same variables as webhook
   - Must be identical!

6. **Instance Type:**
   - Starter: For testing
   - Standard: For production (recommended)

7. **Click:** Create Background Worker

8. **Wait:** 3-5 minutes for deployment

---

### Step 4: Verify Deployments

#### Check Webhook:

Visit: `https://your-webhook-url.onrender.com/health`

**Expected response:**
```json
{"status":"ok","active_calls":0}
```

**If error:** Check logs in Render dashboard

#### Check Agent Logs:

1. Render dashboard → voice-agent-worker → Logs
2. Look for:
   ```
   ✅ Realtime agent ready - LOW LATENCY optimized!
   ✅ VAD threshold: 0.75
   ```

**If errors:** Check environment variables match

---

### Step 5: Configure Twilio

1. **Go to:** https://console.twilio.com/us1/develop/phone-numbers/manage/incoming

2. **Click:** Your phone number

3. **Voice Configuration:**
   - A Call Comes In: **Webhook**
   - URL: `https://your-webhook-url.onrender.com/incoming-call`
   - HTTP Method: **POST**

4. **Save Configuration**

---

### Step 6: Test the Integration

#### Make Test Call:

1. **Call your Twilio number**
2. **Wait 1-2 seconds** for connection
3. **Say:** "Hello!"
4. **Listen:** Agent should respond in ~500-700ms

#### Check Logs:

**Webhook logs should show:**
```
📞 Incoming call: CA... from +353877069402
🔗 SIP URI: sip:call-CA...@sip.livekit.cloud
✓ TwiML response created
```

**Agent logs should show:**
```
👤 Participant joined: [sip-participant]
✅ Realtime agent ready
```

**If successful:** 🎉 Deployment complete!

---

## 🔍 Verification Checklist

### Before Testing:

- [ ] Webhook deployed and "Live" status
- [ ] Agent worker deployed and "Live" status
- [ ] Both services show no errors in logs
- [ ] Webhook health check returns OK
- [ ] Twilio webhook configured correctly
- [ ] All environment variables set in both services

### During Test Call:

- [ ] Call connects (doesn't hang up)
- [ ] You can speak clearly
- [ ] Agent responds
- [ ] Response time feels fast (<1 second)
- [ ] Audio quality is good
- [ ] Conversation flows naturally

### In Logs:

- [ ] Webhook shows SIP URI (not WebSocket)
- [ ] Agent shows participant joined
- [ ] No error messages
- [ ] Call cleanup happens on hangup

---

## 🔧 Troubleshooting Deployment

### Webhook Won't Start:

**Check:**
1. Build logs for errors
2. All environment variables set
3. Python version (should use 3.11+)
4. requirements.txt is correct

**Fix:**
- Manual Deploy → Clear build cache
- Redeploy

### Agent Won't Start:

**Check:**
1. Same environment variables as webhook
2. LIVEKIT_URL is accessible
3. API credentials are valid

**Fix:**
- Check agent logs for specific error
- Verify LiveKit credentials
- Restart service

### Webhook Returns 500 Error:

**Check:**
1. Logs for Python errors
2. Missing environment variables
3. Invalid credentials

**Fix:**
- Fix errors in code
- Add missing variables
- Redeploy

### Twilio Can't Reach Webhook:

**Check:**
1. Webhook URL is HTTPS
2. URL ends with `/incoming-call`
3. Service is "Live" not "Deploying"

**Fix:**
- Wait for deployment to complete
- Use correct URL
- Check Render service status

### Call Connects but No Audio:

**Check:**
1. Agent worker is running
2. LiveKit SIP is enabled
3. SIP domain is correct
4. You spoke first

**Fix:**
- Restart agent worker
- Verify LiveKit SIP config
- Say "Hello!" clearly

---

## 🔄 Update Deployment

### Code Changes:

```bash
# Make changes to code
git add .
git commit -m "Description of changes"
git push origin main
```

Render auto-deploys on push.

### Environment Variable Changes:

1. Render dashboard → Service → Environment
2. Edit variable
3. Save (triggers automatic redeploy)

### Manual Redeploy:

1. Render dashboard → Service
2. Manual Deploy → Deploy latest commit

---

## 📊 Monitoring Production

### Check Service Health:

```bash
# Webhook health
curl https://your-webhook.onrender.com/health

# Metrics
curl https://your-webhook.onrender.com/metrics
```

### Monitor Logs:

**Real-time:**
- Render dashboard → Logs tab
- Auto-updates

**Historical:**
- Download logs from Render
- Set up log aggregation (optional)

### Set Up Alerts:

**In Render:**
1. Service settings → Alerts
2. Configure:
   - Service down
   - High error rate
   - High memory/CPU

**In Twilio:**
1. Monitor → Alerts
2. Configure:
   - Webhook failures
   - High latency
   - Error rates

---

## 💰 Cost Management

### Render.com Pricing:

| Plan | Cost | Calls |
|------|------|-------|
| **Free** | $0 | ~5-10 concurrent (testing) |
| **Starter** | $7/mo each | ~25 concurrent |
| **Standard** | $25/mo each | ~100 concurrent |

**Total for webhook + agent:**
- Testing: $0 (free tier)
- Production: $50-100/mo (2x Standard)

### LiveKit Pricing:

Check: https://livekit.io/pricing

Estimate: $50-150/mo for moderate usage

### OpenAI Pricing:

Realtime API: ~$0.06/minute input, ~$0.24/minute output

100 hours/month ≈ $200-400

### Twilio Pricing:

- Phone number: $1-2/mo
- Inbound minutes: $0.0085/min
- SIP: No extra charge

100 hours/month ≈ $50

### Total Estimate:

**Monthly costs:** $300-600 for moderate usage

---

## 🚀 Production Checklist

Before going live:

### Configuration:
- [ ] All services deployed and running
- [ ] Environment variables secure (not in code)
- [ ] SIP domain verified
- [ ] Twilio webhook configured

### Testing:
- [ ] Multiple test calls successful
- [ ] Latency acceptable (<1s)
- [ ] Audio quality good
- [ ] No errors in logs
- [ ] Load test completed (if high volume)

### Monitoring:
- [ ] Health checks working
- [ ] Alerts configured
- [ ] Log monitoring set up
- [ ] Metrics tracking enabled

### Documentation:
- [ ] Team knows how to check logs
- [ ] Escalation process defined
- [ ] Backup contact methods ready

### Security:
- [ ] API keys not exposed
- [ ] Webhook validation (optional but recommended)
- [ ] Rate limiting considered
- [ ] Access controls in place

---

## 🎯 Next Steps After Deployment

1. **Monitor first 24 hours** - Check for any issues
2. **Gather feedback** - Test call quality from different phones
3. **Optimize settings** - Adjust VAD if needed
4. **Scale if needed** - Upgrade instances for more calls
5. **Add features** - Custom prompts, call recording, etc.

---

## 🆘 Getting Help

### Render Support:
- Dashboard → Help icon
- community.render.com

### LiveKit Support:
- support@livekit.io
- livekit.io/community

### Twilio Support:
- www.twilio.com/help
- Twilio debugger for webhook issues

---

## ✅ Deployment Complete!

If you've completed all steps:

**You now have:**
- ✅ Production-ready voice agent
- ✅ Ultra-low latency (<700ms)
- ✅ Scalable architecture
- ✅ Monitoring and alerts

**Test it:** Call your number and talk to your AI! 🎉

---

**Need help?** Check `LIVEKIT_SIP_SETUP.md` for detailed troubleshooting.

