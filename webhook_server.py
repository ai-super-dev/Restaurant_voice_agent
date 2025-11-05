"""
Twilio Webhook Server
Handles incoming phone calls and connects them to LiveKit rooms
"""

import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from livekit import api
import uvicorn
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Voice Agent Webhook Server")

# Track active calls for metrics
active_calls = set()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Voice Agent Webhook Server",
        "active_calls": len(active_calls)
    }


@app.get("/health")
async def health():
    """Health check for load balancers"""
    return {"status": "ok", "active_calls": len(active_calls)}


@app.post("/incoming-call")
async def incoming_call(request: Request):
    """
    Handle incoming Twilio calls
    This endpoint receives webhook from Twilio when a call comes in
    """
    try:
        # Get call details from Twilio
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        from_number = form_data.get("From")
        to_number = form_data.get("To")
        
        logger.info(f"📞 Incoming call: {call_sid} from {from_number} to {to_number}")
        
        # Track active call
        active_calls.add(call_sid)
        
        # Create a unique room name for this call
        room_name = f"call-{call_sid}"
        
        # Generate LiveKit token for the participant
        token = api.AccessToken(
            Config.LIVEKIT_API_KEY,
            Config.LIVEKIT_API_SECRET
        )
        token.with_identity(f"caller-{from_number}")
        token.with_name(f"Caller {from_number}")
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))
        
        jwt_token = token.to_jwt()
        
        # Create TwiML response
        # IMPORTANT: Choose ONE of the following approaches:
        
        # APPROACH 1: LiveKit SIP Integration (if you have SIP enabled)
        # Requires: LiveKit Cloud account with SIP enabled
        USE_LIVEKIT_SIP = False  # Change to True if you have LiveKit SIP enabled
        
        if USE_LIVEKIT_SIP:
            # Connect via LiveKit SIP
            sip_uri = f"sip:{room_name}@sip.livekit.cloud"
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Connecting you to the AI assistant.</Say>
    <Dial>
        <Sip>{sip_uri}</Sip>
    </Dial>
</Response>"""
        else:
            # APPROACH 2: Simple Test Response (for testing webhook only)
            # This confirms your webhook is working but doesn't connect to agent yet
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        Hello! Your webhook is working correctly. 
        Call ID is {call_sid[:8]}.
        To connect with the AI agent, you need to enable LiveKit SIP integration.
        Check the setup guide for details.
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Joanna">Goodbye!</Say>
    <Hangup/>
</Response>"""
        
        logger.info(f"✓ Created room '{room_name}' for call {call_sid}")
        logger.info(f"Active calls: {len(active_calls)}")
        
        return Response(
            content=twiml_response,
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}", exc_info=True)
        
        # Return error TwiML
        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Sorry, there was an error connecting your call. Please try again later.</Say>
    <Hangup/>
</Response>"""
        
        return Response(
            content=error_twiml,
            media_type="application/xml"
        )


@app.post("/call-status")
async def call_status(request: Request):
    """
    Handle call status updates from Twilio
    This receives updates when call state changes (completed, failed, etc.)
    """
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        
        logger.info(f"📊 Call status update: {call_sid} - {call_status}")
        
        # Remove from active calls when completed
        if call_status in ["completed", "failed", "busy", "no-answer", "canceled"]:
            active_calls.discard(call_sid)
            logger.info(f"Call ended: {call_sid}. Active calls: {len(active_calls)}")
        
        return PlainTextResponse("OK")
        
    except Exception as e:
        logger.error(f"Error handling call status: {e}", exc_info=True)
        return PlainTextResponse("OK")


@app.get("/metrics")
async def metrics():
    """
    Metrics endpoint for monitoring
    """
    return {
        "active_calls": len(active_calls),
        "max_concurrent_calls": Config.MAX_CONCURRENT_CALLS,
        "utilization_percent": (len(active_calls) / Config.MAX_CONCURRENT_CALLS) * 100
    }


def main():
    """Start the webhook server"""
    logger.info("=" * 60)
    logger.info("🚀 Starting Voice Agent Webhook Server")
    logger.info("=" * 60)
    logger.info(f"Host: {Config.WEBHOOK_HOST}")
    logger.info(f"Port: {Config.WEBHOOK_PORT}")
    logger.info(f"Max concurrent calls: {Config.MAX_CONCURRENT_CALLS}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📝 Configure your Twilio phone number webhook to:")
    logger.info(f"   https://your-domain.com/incoming-call")
    logger.info("")
    logger.info("💡 For local testing with ngrok:")
    logger.info(f"   1. Run: ngrok http {Config.WEBHOOK_PORT}")
    logger.info("   2. Copy the HTTPS URL from ngrok")
    logger.info("   3. Set Twilio webhook to: https://YOUR-NGROK-URL/incoming-call")
    logger.info("=" * 60)
    
    # Start the server
    uvicorn.run(
        app,
        host=Config.WEBHOOK_HOST,
        port=Config.WEBHOOK_PORT,
        log_level=Config.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()

