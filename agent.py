"""
Main AI Voice Agent with LiveKit Integration
Handles voice conversations with low latency and high concurrency
Uses OpenAI Realtime API for <1s latency
"""

import asyncio
import logging
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    voice,
)
from livekit.plugins import openai, silero
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """
    Main entry point for each voice agent session
    Called automatically by LiveKit when a participant joins a room
    Uses OpenAI Realtime API for ultra-low latency (<1s)
    """
    try:
        logger.info(f"🎯 New agent session started")
        logger.info(f"Room: {ctx.room.name}")
        
        # Connect to the room with audio only for lower latency
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info(f"✓ Connected to room: {ctx.room.name}")
        
        # Wait for participant to join
        participant = await ctx.wait_for_participant()
        logger.info(f"👤 Participant joined: {participant.identity}")
        
        # Create OpenAI Realtime Multimodal Agent (STT + LLM + TTS in one)
        # This provides the lowest latency possible
        logger.info(f"🚀 Creating OpenAI Realtime agent (ultra-low latency mode)")
        
        # Import TurnDetection for proper VAD configuration
        from livekit.plugins.openai.realtime.realtime_model import TurnDetection
        
        # Create RealtimeModel with production-optimized settings
        # CRITICAL: Use ONLY OpenAI's Server VAD - NO local VAD
        # Phone call settings: Balanced for speed + stability
        realtime_model = openai.realtime.RealtimeModel(
            voice=Config.VOICE_MODEL,
            temperature=0.8,
            modalities=["text", "audio"],
            turn_detection=TurnDetection(
                type="server_vad",
                threshold=0.75,  # Balanced: not too sensitive, not too slow
                prefix_padding_ms=200,  # Reduced for faster response
                silence_duration_ms=500,  # Balanced: 500ms for <1s total latency
            ),
        )
        
        # Create voice agent using Realtime API
        # CRITICAL: NO local VAD! Only use OpenAI's Server VAD to avoid conflicts
        # Add TTS fallback to handle text responses (prevents cancellations)
        agent = voice.Agent(
            instructions=Config.SYSTEM_PROMPT,
            llm=realtime_model,
            tts=openai.TTS(voice=Config.VOICE_MODEL),  # Fallback for text responses
            # vad=None - deliberately omitted to use only Server VAD
        )
        
        # Create and start session
        session = voice.AgentSession()
        logger.info(f"🎤 Starting Realtime agent session")
        logger.info(f"💡 Speak first to start - say 'Hello'")
        await session.start(agent, room=ctx.room)
        
        logger.info(f"✅ Realtime agent ready - LOW LATENCY optimized!")
        logger.info(f"✅ VAD threshold: 0.75 (balanced: speed + stability)")
        logger.info(f"✅ Silence duration: 500ms (fast response)")
        logger.info(f"✅ Prefix padding: 200ms (reduced for speed)")
        logger.info(f"✅ Expected latency: 600-900ms target (phone optimized)")
        logger.info(f"✅ Deployment: Cloud-ready (Render.com, etc.)")
        
        # Keep the session running until disconnect
        while ctx.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
            await asyncio.sleep(0.5)
        
        logger.info(f"📞 Session ended")
        
    except Exception as e:
        logger.error(f"❌ Error in agent session: {e}", exc_info=True)
        raise


def main():
    """
    Main function to start the voice agent worker
    """
    logger.info("=" * 80)
    logger.info("🎙️  AI VOICE AGENT WITH LIVEKIT (REALTIME API)")
    logger.info("=" * 80)
    logger.info(f"Agent Name: {Config.AGENT_NAME}")
    logger.info(f"Voice Model: {Config.VOICE_MODEL}")
    logger.info(f"Max Concurrent Calls: {Config.MAX_CONCURRENT_CALLS}")
    logger.info(f"LiveKit URL: {Config.LIVEKIT_URL}")
    logger.info("=" * 80)
    logger.info("")
    logger.info("🔧 Configuration:")
    logger.info(f"   - Ultra-low latency mode: ENABLED (<1s target)")
    logger.info(f"   - OpenAI Realtime API: ENABLED (STT+LLM+TTS unified)")
    logger.info(f"   - Voice Activity Detection: OpenAI Server VAD ONLY")
    logger.info(f"   - TTS Fallback: ENABLED (prevents cancelled responses)")
    logger.info(f"   - Voice Model: {Config.VOICE_MODEL}")
    logger.info("")
    logger.info("📊 Performance settings (LOW LATENCY optimized):")
    logger.info(f"   - Server VAD threshold: 0.75 (balanced)")
    logger.info(f"   - Prefix padding: 200ms (fast response)")
    logger.info(f"   - Silence duration: 500ms (target <1s latency)")
    logger.info(f"   - Expected latency: 600-900ms (phone network included)")
    logger.info(f"   - NO local VAD (avoids conflicts)")
    logger.info(f"   - Auto-subscribe: Audio only")
    logger.info(f"   - Full-duplex streaming: Enabled")
    logger.info(f"   - Cloud deployment: Ready (Render.com compatible)")
    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ Agent is ready with <1s latency optimization!")
    logger.info("=" * 80)
    logger.info("")
    
    # Run the worker with optimized settings
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=Config.LIVEKIT_API_KEY,
            api_secret=Config.LIVEKIT_API_SECRET,
            ws_url=Config.LIVEKIT_URL,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down agent...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)

