"""
Twilio Webhook Server
Handles incoming phone calls and connects them to LiveKit rooms

IMPORTANT: This implementation uses Twilio Media Streams to bridge phone audio to LiveKit.
For production use, LiveKit SIP Trunk integration is recommended as it's more reliable
and handles all audio conversion automatically.
"""

import logging
import json
import base64
import asyncio
import numpy as np

# Use audioop-lts for Python 3.13+ compatibility
try:
    import audioop
except ModuleNotFoundError:
    # Python 3.13+ removed audioop, use audioop-lts instead
    import audioop_lts as audioop
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from livekit import api, rtc
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
    Uses Twilio Media Streams to connect phone audio to LiveKit room
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
        
        logger.info(f"✓ Created room '{room_name}' for call {call_sid}")
        
        # Get the public URL for the WebSocket endpoint
        # In production, this should be your deployed URL
        # For local testing with ngrok, this will be your ngrok URL
        webhook_base_url = request.url.scheme + "://" + request.url.netloc
        stream_url = f"{webhook_base_url.replace('http', 'ws')}/media-stream"
        
        logger.info(f"🔗 Stream URL: {stream_url}")
        
        # Create TwiML response with Media Streams
        # This streams bidirectional audio between Twilio and our WebSocket handler
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{stream_url}">
            <Parameter name="callSid" value="{call_sid}"/>
            <Parameter name="roomName" value="{room_name}"/>
            <Parameter name="fromNumber" value="{from_number}"/>
        </Stream>
    </Connect>
</Response>"""
        
        logger.info(f"✓ TwiML response created for {call_sid}")
        logger.info(f"Active calls: {len(active_calls)}")
        
        return Response(
            content=twiml_response,
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"❌ Error handling incoming call: {e}", exc_info=True)
        
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


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams
    Bridges audio between Twilio phone call and LiveKit room
    """
    await websocket.accept()
    logger.info("📡 Media stream WebSocket connected")
    
    call_sid = None
    room_name = None
    room = None
    audio_source = None
    
    try:
        # Wait for start message from Twilio
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                event_type = data.get("event")
                
                if event_type == "start":
                    # Extract call parameters
                    stream_sid = data.get("streamSid")
                    call_sid = data.get("start", {}).get("callSid")
                    custom_params = data.get("start", {}).get("customParameters", {})
                    room_name = custom_params.get("roomName")
                    from_number = custom_params.get("fromNumber")
                    
                    logger.info(f"🎬 Stream started: {stream_sid} for call {call_sid}")
                    logger.info(f"🎯 Connecting to LiveKit room: {room_name}")
                    
                    # Connect to LiveKit room
                    room = rtc.Room()
                    
                    # Generate token for this phone caller
                    token = api.AccessToken(
                        Config.LIVEKIT_API_KEY,
                        Config.LIVEKIT_API_SECRET
                    )
                    token.with_identity(f"phone-{from_number}")
                    token.with_name(f"Phone Caller")
                    token.with_grants(api.VideoGrants(
                        room_join=True,
                        room=room_name,
                        can_publish=True,
                        can_subscribe=True,
                    ))
                    
                    # Connect to the room
                    await room.connect(Config.LIVEKIT_URL, token.to_jwt())
                    logger.info(f"✓ Connected to LiveKit room: {room_name}")
                    
                    # Create audio source for phone audio
                    audio_source = rtc.AudioSource(8000, 1)  # 8kHz mono (Twilio's format)
                    track = rtc.LocalAudioTrack.create_audio_track("phone-audio", audio_source)
                    options = rtc.TrackPublishOptions()
                    options.source = rtc.TrackSource.SOURCE_MICROPHONE
                    
                    # Publish the audio track to LiveKit
                    await room.local_participant.publish_track(track, options)
                    logger.info(f"✓ Published phone audio track to room")
                    
                    # Set up event handler for remote tracks (agent's audio)
                    @room.on("track_subscribed")
                    def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
                        """Handle when we receive audio from the agent"""
                        if track.kind == rtc.TrackKind.KIND_AUDIO:
                            logger.info(f"🎧 Subscribed to agent audio track from {participant.identity}")
                            asyncio.create_task(stream_agent_audio_to_twilio(track, stream_sid, websocket))
                    
                    async def stream_agent_audio_to_twilio(track, stream_sid, ws):
                        """Stream agent's audio back to Twilio phone call"""
                        try:
                            audio_stream = rtc.AudioStream(track)
                            logger.info("📤 Starting to stream agent audio to Twilio")
                            
                            async for audio_frame_event in audio_stream:
                                try:
                                    # Get the actual AudioFrame from the event
                                    frame = audio_frame_event.frame
                                    
                                    # Get PCM audio data from LiveKit
                                    # AudioFrame provides data as int16 PCM
                                    pcm_data = frame.data.tobytes()
                                    
                                    # Resample from 48kHz (LiveKit) to 8kHz (Twilio) if needed
                                    if frame.sample_rate != 8000:
                                        pcm_data, _ = audioop.ratecv(
                                            pcm_data,
                                            2,  # 2 bytes per sample (int16)
                                            frame.num_channels,
                                            frame.sample_rate,
                                            8000,  # Target: 8kHz for Twilio
                                            None
                                        )
                                    
                                    # Convert stereo to mono if needed
                                    if frame.num_channels == 2:
                                        pcm_data = audioop.tomono(pcm_data, 2, 1, 1)
                                    
                                    # Convert PCM to mulaw (Twilio's format)
                                    mulaw_data = audioop.lin2ulaw(pcm_data, 2)
                                    
                                    # Base64 encode for Twilio
                                    encoded_audio = base64.b64encode(mulaw_data).decode('utf-8')
                                    
                                    # Send to Twilio
                                    media_msg = {
                                        "event": "media",
                                        "streamSid": stream_sid,
                                        "media": {
                                            "payload": encoded_audio
                                        }
                                    }
                                    await ws.send_text(json.dumps(media_msg))
                                    
                                except Exception as e:
                                    logger.error(f"Error processing audio frame: {e}")
                                    
                        except Exception as e:
                            logger.error(f"Error streaming agent audio to Twilio: {e}", exc_info=True)
                    
                elif event_type == "media":
                    # Receive audio from phone and send to LiveKit
                    if audio_source:
                        media_payload = data.get("media", {}).get("payload")
                        if media_payload:
                            try:
                                # Decode mulaw audio from Twilio (base64 encoded)
                                mulaw_data = base64.b64decode(media_payload)
                                
                                # Convert mulaw to PCM int16
                                pcm_data = audioop.ulaw2lin(mulaw_data, 2)
                                
                                # Convert to numpy array for LiveKit
                                # Twilio sends 8kHz mono, 20ms chunks (160 samples)
                                audio_array = np.frombuffer(pcm_data, dtype=np.int16)
                                
                                # Create AudioFrame for LiveKit
                                audio_frame = rtc.AudioFrame(
                                    data=audio_array,
                                    sample_rate=8000,
                                    num_channels=1,
                                    samples_per_channel=len(audio_array)
                                )
                                
                                # Send to LiveKit room
                                await audio_source.capture_frame(audio_frame)
                                
                            except Exception as e:
                                logger.error(f"Error processing incoming audio: {e}")
                
                elif event_type == "stop":
                    logger.info(f"🛑 Stream stopped for call {call_sid}")
                    break
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from Twilio: {e}")
                continue
            except WebSocketDisconnect:
                logger.info(f"📞 WebSocket disconnected for call {call_sid}")
                break
            except Exception as e:
                logger.error(f"Error in media stream: {e}", exc_info=True)
                break
    
    finally:
        # Cleanup
        if room:
            await room.disconnect()
            logger.info(f"✓ Disconnected from LiveKit room")
        
        if call_sid:
            active_calls.discard(call_sid)
            logger.info(f"✓ Cleaned up call {call_sid}")


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

