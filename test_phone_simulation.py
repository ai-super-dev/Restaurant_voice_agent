"""
Test Phone Call Simulation
Simulates a Twilio phone call without needing a real phone or Twilio account
Tests the webhook server's phone call handling
"""

import asyncio
import json
import base64
import aiohttp
import numpy as np

# Try to import audioop with compatibility
try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop


# Configuration
WEBHOOK_URL = "https://restaurant-voice-agent-ofma.onrender.com"
TEST_CALL_SID = "CA_TEST_123456789"
TEST_FROM_NUMBER = "+15551234567"
TEST_TO_NUMBER = "+16266813821"
TEST_STREAM_SID = "MZ_TEST_987654321"


async def test_health_check():
    """Test 1: Health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{WEBHOOK_URL}/health") as response:
                data = await response.json()
                print(f"✅ Status: {response.status}")
                print(f"✅ Response: {data}")
                return response.status == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_incoming_call():
    """Test 2: Incoming call webhook"""
    print("\n" + "="*60)
    print("TEST 2: Incoming Call Webhook")
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
                print(f"✅ TwiML Response:")
                print(twiml[:200] + "..." if len(twiml) > 200 else twiml)
                
                # Check if TwiML contains Stream element
                if "<Stream url=" in twiml:
                    print("✅ TwiML contains Stream element - Ready for WebSocket!")
                    return True
                else:
                    print("❌ TwiML missing Stream element")
                    return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def generate_test_audio(duration_seconds=1, sample_rate=8000):
    """Generate test audio (simple sine wave)"""
    # Generate a 440Hz tone (A note)
    samples = int(duration_seconds * sample_rate)
    t = np.linspace(0, duration_seconds, samples)
    frequency = 440  # Hz
    audio = np.sin(2 * np.pi * frequency * t)
    
    # Convert to int16 PCM
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Convert to mulaw (Twilio's format)
    pcm_bytes = audio_int16.tobytes()
    mulaw_bytes = audioop.lin2ulaw(pcm_bytes, 2)
    
    # Base64 encode
    encoded = base64.b64encode(mulaw_bytes).decode('utf-8')
    
    return encoded


async def test_websocket_connection():
    """Test 3: WebSocket connection (simulates Twilio Media Streams)"""
    print("\n" + "="*60)
    print("TEST 3: WebSocket Media Stream")
    print("="*60)
    print("This simulates a real phone call's audio stream...")
    
    ws_url = f"{WEBHOOK_URL.replace('http', 'ws')}/media-stream"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                print("✅ WebSocket connected!")
                
                # Step 1: Send "start" event (Twilio sends this when call starts)
                start_message = {
                    "event": "start",
                    "streamSid": TEST_STREAM_SID,
                    "start": {
                        "callSid": TEST_CALL_SID,
                        "customParameters": {
                            "callSid": TEST_CALL_SID,
                            "roomName": f"call-{TEST_CALL_SID}",
                            "fromNumber": TEST_FROM_NUMBER
                        }
                    },
                    "sequenceNumber": "1"
                }
                
                print("\n📤 Sending START event...")
                await ws.send_str(json.dumps(start_message))
                print("✅ Start event sent")
                
                # Give the server time to connect to LiveKit
                await asyncio.sleep(2)
                
                # Step 2: Send test audio data (simulate speaking)
                print("\n📤 Sending simulated audio (440Hz tone for 3 seconds)...")
                
                # Send audio in small chunks (Twilio sends 20ms chunks)
                chunk_duration = 0.02  # 20ms
                total_duration = 3  # 3 seconds of audio
                chunks = int(total_duration / chunk_duration)
                
                for i in range(chunks):
                    audio_payload = await generate_test_audio(chunk_duration)
                    
                    media_message = {
                        "event": "media",
                        "sequenceNumber": str(i + 2),
                        "media": {
                            "track": "inbound",
                            "chunk": str(i + 1),
                            "timestamp": str(i * 20),  # 20ms per chunk
                            "payload": audio_payload
                        },
                        "streamSid": TEST_STREAM_SID
                    }
                    
                    await ws.send_str(json.dumps(media_message))
                    
                    # Show progress every 10 chunks (200ms)
                    if (i + 1) % 10 == 0:
                        print(f"   ... sent {i+1}/{chunks} chunks ({(i+1)*20}ms)")
                    
                    # Small delay to simulate real-time
                    await asyncio.sleep(0.02)
                
                print("✅ Audio sent successfully!")
                
                # Step 3: Listen for responses from agent
                print("\n📥 Listening for agent responses...")
                print("   (Note: Agent will only respond if agent.py is running)")
                
                try:
                    # Wait for up to 5 seconds for responses
                    async with asyncio.timeout(5):
                        response_count = 0
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                if data.get("event") == "media":
                                    response_count += 1
                                    if response_count == 1:
                                        print("✅ Received first audio response from agent!")
                                    if response_count % 50 == 0:
                                        print(f"   ... received {response_count} audio chunks")
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                print(f"❌ WebSocket error: {ws.exception()}")
                                break
                        
                        if response_count > 0:
                            print(f"✅ Total audio chunks received: {response_count}")
                        else:
                            print("⚠️  No audio response received")
                            print("   (This is normal if agent.py is not running)")
                
                except asyncio.TimeoutError:
                    print("⏱️  Timeout waiting for response (this is normal for testing)")
                
                # Step 4: Send "stop" event
                print("\n📤 Sending STOP event...")
                stop_message = {
                    "event": "stop",
                    "streamSid": TEST_STREAM_SID,
                    "sequenceNumber": str(chunks + 2)
                }
                await ws.send_str(json.dumps(stop_message))
                print("✅ Stop event sent")
                
                await asyncio.sleep(1)
                
                print("\n✅ WebSocket test completed!")
                return True
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_call_status():
    """Test 4: Call status callback"""
    print("\n" + "="*60)
    print("TEST 4: Call Status Callback")
    print("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field('CallSid', TEST_CALL_SID)
            form_data.add_field('CallStatus', 'completed')
            
            async with session.post(f"{WEBHOOK_URL}/call-status", data=form_data) as response:
                text = await response.text()
                print(f"✅ Status: {response.status}")
                print(f"✅ Response: {text}")
                return response.status == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def run_all_tests():
    """Run all tests in sequence"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "PHONE CALL SIMULATION TEST SUITE" + " "*16 + "║")
    print("╚" + "="*58 + "╝")
    print(f"\nTesting webhook at: {WEBHOOK_URL}")
    print("Make sure webhook_server.py is running!")
    print("\nPress Ctrl+C to abort at any time")
    
    await asyncio.sleep(2)
    
    results = {}
    
    # Test 1: Health Check
    results['health'] = await test_health_check()
    
    if not results['health']:
        print("\n❌ Health check failed! Make sure webhook_server.py is running.")
        print("   Run: python webhook_server.py")
        return
    
    await asyncio.sleep(1)
    
    # Test 2: Incoming Call
    results['incoming_call'] = await test_incoming_call()
    await asyncio.sleep(1)
    
    # Test 3: WebSocket (Full simulation)
    print("\n⚠️  NOTE: The next test simulates a full phone call.")
    print("   - If agent.py is running, it will connect to LiveKit and interact")
    print("   - If agent.py is NOT running, the test will still work but won't get responses")
    await asyncio.sleep(2)
    
    results['websocket'] = await test_websocket_connection()
    await asyncio.sleep(1)
    
    # Test 4: Call Status
    results['call_status'] = await test_call_status()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Your webhook is working perfectly!")
        print("\nNext steps:")
        print("1. If you haven't already, start agent.py for full functionality")
        print("2. Test with a real phone call using ngrok")
        print("3. Deploy to production!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print("\n" + "="*60)


async def run_quick_test():
    """Quick test - just health check and incoming call"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "QUICK WEBHOOK TEST" + " "*25 + "║")
    print("╚" + "="*58 + "╝")
    
    # Health check
    health_ok = await test_health_check()
    if not health_ok:
        print("\n❌ Webhook is not running or not accessible.")
        return
    
    # Incoming call
    await asyncio.sleep(1)
    incoming_ok = await test_incoming_call()
    
    print("\n" + "="*60)
    if health_ok and incoming_ok:
        print("✅ QUICK TEST PASSED!")
        print("\nYour webhook is responding correctly.")
        print("Run with --full flag for complete test including WebSocket.")
    else:
        print("⚠️  Some issues detected. Check output above.")
    print("="*60)


def print_help():
    """Print usage help"""
    print("""
Phone Call Simulation Test

This script simulates a Twilio phone call to test your webhook server
without needing a real phone or Twilio account.

Usage:
    python test_phone_simulation.py [options]

Options:
    --quick     Quick test (health check + incoming call only)
    --full      Full test including WebSocket simulation (default)
    --help      Show this help message

Examples:
    python test_phone_simulation.py              # Full test
    python test_phone_simulation.py --quick      # Quick test
    python test_phone_simulation.py --full       # Full test (explicit)

Requirements:
    1. webhook_server.py must be running (python webhook_server.py)
    2. For full functionality test, also run agent.py
    3. Install dependencies: pip install -r requirements.txt

What gets tested:
    ✓ Health endpoints
    ✓ Incoming call webhook (TwiML response)
    ✓ WebSocket connection
    ✓ Audio streaming simulation
    ✓ Call status callback

This simulates the entire phone call flow that Twilio would perform!
""")


async def main():
    """Main entry point"""
    import sys
    
    # Check command line arguments
    if '--help' in sys.argv or '-h' in sys.argv:
        print_help()
        return
    
    if '--quick' in sys.argv:
        await run_quick_test()
    else:
        await run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

