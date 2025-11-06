"""
Full System Test - Simulates Complete Phone Call Flow
Tests webhook_server.py + agent.py + LiveKit + OpenAI integration
WITHOUT needing a real phone call

This test simulates what Twilio does:
1. POST to /incoming-call (get TwiML)
2. Connect WebSocket to /media-stream
3. Send audio frames (simulated speech)
4. Receive audio responses from agent

Modes:
  - Local: Tests with agent.py running locally (default)
  - Deployed: Tests with agent deployed on LiveKit Cloud (--deployed flag)
"""

import asyncio
import websockets
import aiohttp
import json
import base64
import wave
import numpy as np
from xml.etree import ElementTree as ET

# Try to import audioop, fall back to audioop_lts if needed
try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop


# Configuration
WEBHOOK_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
TEST_CALL_SID = "CA_TEST_FULL_SYSTEM"
TEST_STREAM_SID = "MZ_TEST_STREAM"
TEST_FROM_NUMBER = "+15551234567"
TEST_TO_NUMBER = "+16266813821"

# Test mode: 'local' or 'deployed'
TEST_MODE = 'local'  # Will be set by command line argument


def generate_test_audio(duration_seconds=2, sample_rate=8000):
    """
    Generate test audio signal (sine wave)
    This simulates someone speaking into the phone
    """
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    
    # Generate a mix of frequencies to simulate voice
    freq1 = 300  # Lower frequency
    freq2 = 800  # Higher frequency
    signal = (np.sin(2 * np.pi * freq1 * t) + np.sin(2 * np.pi * freq2 * t)) / 2
    
    # Convert to 16-bit PCM
    audio_data = (signal * 32767 * 0.5).astype(np.int16)
    
    return audio_data.tobytes()


def pcm_to_mulaw(pcm_data):
    """Convert PCM audio to mulaw (as Twilio sends it)"""
    return audioop.lin2ulaw(pcm_data, 2)


def mulaw_to_pcm(mulaw_data):
    """Convert mulaw audio to PCM (as we receive from Twilio)"""
    return audioop.ulaw2lin(mulaw_data, 2)


async def test_webhook_call_initiation():
    """
    Test 1: Simulate Twilio calling the webhook when a call comes in
    """
    print("\n" + "="*60)
    print("TEST 1: Call Initiation (HTTP → TwiML)")
    print("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field('CallSid', TEST_CALL_SID)
            form_data.add_field('From', TEST_FROM_NUMBER)
            form_data.add_field('To', TEST_TO_NUMBER)
            form_data.add_field('CallStatus', 'ringing')
            
            async with session.post(f"{WEBHOOK_URL}/incoming-call", data=form_data) as response:
                twiml = await response.text()
                print(f"✅ Status: {response.status}")
                
                # Parse TwiML to get WebSocket URL
                root = ET.fromstring(twiml)
                stream = root.find('.//Stream')
                stream_url = stream.get('url')
                
                print(f"✅ Got TwiML with WebSocket URL: {stream_url}")
                
                params = stream.findall('Parameter')
                param_dict = {p.get('name'): p.get('value') for p in params}
                room_name = param_dict.get('roomName')
                
                print(f"✅ Room Name: {room_name}")
                print(f"✅ Call SID: {param_dict.get('callSid')}")
                
                return stream_url, room_name
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def test_websocket_connection_and_audio():
    """
    Test 2: Simulate Twilio connecting via WebSocket and sending audio
    This is where the agent gets activated!
    """
    print("\n" + "="*60)
    print("TEST 2: WebSocket Connection + Audio Streaming")
    print("="*60)
    
    if TEST_MODE == 'deployed':
        print("🔷 Testing with DEPLOYED agent on LiveKit Cloud")
        print("   → Agent should auto-join room when created")
        print("   → No local agent.py needed")
    else:
        print("🔷 Testing with LOCAL agent (agent.py)")
        print("   → Make sure agent.py is running locally")
    
    print("\nThis test will:")
    print("  1. Connect WebSocket to /media-stream")
    print("  2. Send 'start' event (activates LiveKit room)")
    print("  3. Send audio frames (simulated speech)")
    print("  4. Receive audio responses from agent")
    print("  5. Monitor for 10 seconds")
    print("="*60)
    
    # First, initiate the call to get room info
    stream_url, room_name = await test_webhook_call_initiation()
    if not stream_url:
        print("❌ Failed to get stream URL")
        return False
    
    # Convert http to ws in the URL
    ws_url = stream_url.replace('http://', 'ws://').replace('https://', 'wss://')
    
    print(f"\n🔗 Connecting to WebSocket: {ws_url}")
    
    try:
        async with websockets.connect(ws_url, ping_interval=None) as websocket:
            print("✅ WebSocket connected!")
            
            # Step 1: Send START event (as Twilio does)
            start_event = {
                "event": "start",
                "sequenceNumber": "1",
                "start": {
                    "streamSid": TEST_STREAM_SID,
                    "accountSid": "AC_test",
                    "callSid": TEST_CALL_SID,
                    "tracks": ["inbound"],
                    "mediaFormat": {
                        "encoding": "audio/x-mulaw",
                        "sampleRate": 8000,
                        "channels": 1
                    },
                    "customParameters": {
                        "callSid": TEST_CALL_SID,
                        "roomName": room_name,
                        "fromNumber": TEST_FROM_NUMBER
                    }
                },
                "streamSid": TEST_STREAM_SID
            }
            
            await websocket.send(json.dumps(start_event))
            print("✅ Sent START event")
            print("   → This should activate the LiveKit room")
            
            if TEST_MODE == 'deployed':
                print("   → Deployed agent on LiveKit Cloud should auto-join")
                print("   → Check LiveKit Cloud dashboard for agent activity")
            else:
                print("   → Local agent.py should connect to the room")
                print("   → Check agent.py terminal for logs!")
            
            # Wait a bit for agent to connect (deployed agents may take slightly longer)
            wait_time = 3 if TEST_MODE == 'deployed' else 2
            print(f"   → Waiting {wait_time} seconds for agent to connect...")
            await asyncio.sleep(wait_time)
            
            # Step 2: Generate and send test audio (simulate speaking)
            print("\n📤 Generating test audio (simulated speech)...")
            test_audio_pcm = generate_test_audio(duration_seconds=2, sample_rate=8000)
            test_audio_mulaw = pcm_to_mulaw(test_audio_pcm)
            
            # Split audio into chunks (20ms chunks = 160 bytes for 8kHz)
            chunk_size = 160
            chunks = [test_audio_mulaw[i:i+chunk_size] for i in range(0, len(test_audio_mulaw), chunk_size)]
            
            print(f"📤 Sending {len(chunks)} audio chunks (simulating user speech)...")
            
            sequence = 2
            for chunk in chunks[:50]:  # Send first 50 chunks (1 second)
                media_event = {
                    "event": "media",
                    "sequenceNumber": str(sequence),
                    "media": {
                        "track": "inbound",
                        "chunk": str(sequence - 1),
                        "timestamp": str(sequence * 160),
                        "payload": base64.b64encode(chunk).decode('ascii')
                    },
                    "streamSid": TEST_STREAM_SID
                }
                await websocket.send(json.dumps(media_event))
                sequence += 1
                await asyncio.sleep(0.02)  # 20ms between chunks
            
            print("✅ Sent audio chunks to agent")
            print("   → Agent should process this audio")
            print("   → Agent should send response back")
            print("   → Check agent.py terminal for activity!")
            
            # Step 3: Listen for responses
            print("\n📥 Listening for agent responses...")
            print("   (Will listen for 10 seconds)")
            
            responses_received = 0
            media_responses = 0
            
            try:
                # Set a timeout for receiving messages
                async with asyncio.timeout(10):
                    while True:
                        try:
                            response = await websocket.recv()
                            responses_received += 1
                            
                            # Parse response
                            data = json.loads(response)
                            event_type = data.get('event')
                            
                            if event_type == 'media':
                                media_responses += 1
                                payload = data.get('media', {}).get('payload', '')
                                audio_size = len(base64.b64decode(payload)) if payload else 0
                                print(f"   📥 Received audio response #{media_responses} ({audio_size} bytes)")
                                print(f"      → Agent is speaking!")
                            elif event_type == 'mark':
                                print(f"   ✅ Received mark event")
                            else:
                                print(f"   📩 Received event: {event_type}")
                                
                        except websockets.exceptions.ConnectionClosed:
                            print("   ℹ️  WebSocket connection closed")
                            break
                            
            except TimeoutError:
                print("\n⏱️  10 second monitoring period complete")
            
            # Step 4: Send STOP event
            stop_event = {
                "event": "stop",
                "sequenceNumber": str(sequence),
                "stop": {
                    "accountSid": "AC_test",
                    "callSid": TEST_CALL_SID
                },
                "streamSid": TEST_STREAM_SID
            }
            await websocket.send(json.dumps(stop_event))
            print("\n✅ Sent STOP event")
            
            # Summary
            print("\n" + "="*60)
            print("TEST 2 SUMMARY")
            print("="*60)
            print(f"Total responses received: {responses_received}")
            print(f"Audio responses (agent speaking): {media_responses}")
            
            if media_responses > 0:
                print("\n🎉 SUCCESS! Agent responded with audio!")
                print("   ✅ WebSocket connection works")
                print("   ✅ LiveKit integration works")
                print("   ✅ Agent is processing audio")
                print("   ✅ Agent is generating responses")
                return True
            else:
                print("\n⚠️  No audio responses received from agent")
                print("   Possible reasons:")
                print("   1. Agent not running (check agent.py terminal)")
                print("   2. LiveKit connection issue (check API keys)")
                print("   3. OpenAI API issue (check OPENAI_API_KEY)")
                print("   4. Audio not triggering VAD (try real speech)")
                return False
                
    except Exception as e:
        print(f"\n❌ WebSocket test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_metrics_during_call():
    """
    Test 3: Check metrics while "call" is active
    """
    print("\n" + "="*60)
    print("TEST 3: Metrics During Call")
    print("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{WEBHOOK_URL}/metrics") as response:
                data = await response.json()
                print(f"✅ Status: {response.status}")
                print(f"📊 Active calls: {data.get('active_calls')}")
                print(f"📊 Max concurrent: {data.get('max_concurrent_calls')}")
                print(f"📊 Utilization: {data.get('utilization_percent'):.1f}%")
                return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def run_full_system_test():
    """
    Run complete system test
    """
    print("\n")
    print("=" * 60)
    print("        FULL SYSTEM TEST - SIMULATED PHONE CALL")
    print("=" * 60)
    print("\n⚠️  IMPORTANT REQUIREMENTS:")
    print("   1. agent.py MUST be running (Terminal 1)")
    print("   2. webhook_server.py MUST be running (Terminal 2)")
    print("   3. Both must have correct .env configuration")
    print("   4. LiveKit and OpenAI credentials must be valid")
    print("\n📋 This test simulates a complete phone call:")
    print("   → HTTP call initiation (like Twilio receiving call)")
    print("   → WebSocket connection (like Twilio streaming audio)")
    print("   → Audio transmission (simulated user speech)")
    print("   → Agent processing (real AI interaction)")
    print("   → Audio response (agent speaking back)")
    print("\n🎯 What to watch:")
    print("   • This terminal: Test progress and results")
    print("   • webhook_server.py terminal: WebSocket connections")
    print("   • agent.py terminal: Agent activation and processing")
    print("\nPress Ctrl+C to abort")
    print("=" * 60)
    
    await asyncio.sleep(3)
    
    # Run tests
    results = {}
    
    # Test WebSocket and audio
    print("\n🚀 Starting full system test...")
    results['full_system'] = await test_websocket_connection_and_audio()
    
    await asyncio.sleep(2)
    
    # Check metrics
    results['metrics'] = await test_metrics_during_call()
    
    # Final summary
    print("\n\n")
    print("=" * 60)
    print("           FULL SYSTEM TEST RESULTS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if results.get('full_system'):
        print("\n🎉🎉🎉 FULL SYSTEM TEST PASSED! 🎉🎉🎉")
        print("\n✅ Your complete voice agent system is working!")
        print("\nWhat was tested:")
        print("  ✅ Webhook server (HTTP endpoints)")
        print("  ✅ WebSocket streaming (Twilio Media Streams)")
        print("  ✅ LiveKit room creation and connection")
        print("  ✅ Agent activation and processing")
        print("  ✅ OpenAI Realtime API integration")
        print("  ✅ Audio transmission (both directions)")
        print("\n🎯 Next steps:")
        print("  1. Review agent.py logs to see AI processing")
        print("  2. Try with real phone call for final validation")
        print("  3. Deploy to production (Render.com)")
        print("\n✨ Your system is ready for real phone calls!")
    else:
        print("\n⚠️  FULL SYSTEM TEST DID NOT COMPLETE SUCCESSFULLY")
        print("\n🔍 Troubleshooting:")
        print("  1. Make sure agent.py is running:")
        print("     • Check for 'Agent ready' message")
        print("     • Look for room connection logs")
        print("     • Verify LiveKit credentials")
        print("\n  2. Check webhook_server.py logs:")
        print("     • Should show WebSocket connection")
        print("     • Should show audio streaming activity")
        print("\n  3. Verify environment variables:")
        print("     • LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET")
        print("     • OPENAI_API_KEY")
        print("\n  4. Check for errors in both terminals")
        print("\n  5. Try running test_webhook_deployment.py first:")
        print("     python test_webhook_deployment.py --quick")
    
    print("\n" + "=" * 60)


def print_help():
    """Print usage help"""
    print("""
Full System Test - Simulated Phone Call

This script tests your COMPLETE voice agent system including:
  • webhook_server.py (HTTP + WebSocket)
  • agent.py (LiveKit + OpenAI)
  • Audio streaming (bidirectional)
  • Real AI interaction

This is the most comprehensive test without making a real phone call.

Prerequisites:
    1. agent.py running in Terminal 1
       → Should show: "Agent ready - ULTRA-LOW LATENCY MODE ACTIVE!"
    
    2. webhook_server.py running in Terminal 2
       → Should show: "⚡ ULTRA-LOW LATENCY Webhook Server"
    
    3. .env file configured with:
       → LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
       → OPENAI_API_KEY
       → TWILIO credentials (optional for this test)
    
    4. Dependencies installed:
       → pip install websockets aiohttp numpy

Usage:
    python test_full_system.py

What gets tested:
    ✓ HTTP webhook endpoints
    ✓ WebSocket Media Streams connection
    ✓ LiveKit room creation
    ✓ Agent activation and connection
    ✓ Audio streaming (simulated speech)
    ✓ OpenAI Realtime API processing
    ✓ Agent audio responses
    ✓ Bidirectional audio flow

What to watch:
    • This terminal: Test progress and results
    • webhook_server.py terminal: Connection and streaming logs
    • agent.py terminal: Agent activation and AI processing logs

Expected flow:
    1. Test initiates "call" via HTTP
    2. Test connects WebSocket to /media-stream
    3. Agent receives room connection
    4. Test sends simulated audio
    5. Agent processes audio via OpenAI
    6. Agent sends audio response back
    7. Test receives and reports response

Success criteria:
    ✅ WebSocket connects successfully
    ✅ Agent logs show room connection
    ✅ Agent logs show participant joined
    ✅ Test receives audio responses
    ✅ No errors in any terminal

⚠️  Important notes:
    • Both agent.py AND webhook_server.py must be running
    • This test simulates audio but doesn't test actual voice quality
    • Final validation should still use a real phone call
    • Check all three terminals for complete picture

Troubleshooting:
    If test fails, check:
    1. Both services are running
    2. No errors in service logs
    3. Environment variables are correct
    4. LiveKit and OpenAI credentials are valid
    5. No firewall blocking WebSocket connections
""")


async def main():
    """Main entry point"""
    import sys
    
    # Check command line arguments
    if '--help' in sys.argv or '-h' in sys.argv:
        print_help()
        return
    
    # Run full system test
    await run_full_system_test()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Test interrupted by user")
        print("Cleaning up...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

