"""
Test Webhook Server - Media Streams Implementation
Tests the webhook server without needing a real phone
Validates that webhook returns correct TwiML with Media Streams
"""

import asyncio
import aiohttp
from xml.etree import ElementTree as ET


# Configuration - UPDATE THIS for your deployment
WEBHOOK_URL = "http://localhost:8000"  # Change to your Render URL: https://your-app.onrender.com
TEST_CALL_SID = "CA_TEST_123456789"
TEST_FROM_NUMBER = "+15551234567"
TEST_TO_NUMBER = "+16266813821"


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
                
                if data.get('status') == 'ok':
                    print(f"[OK] Webhook server is healthy!")
                    return True
                else:
                    print(f"[FAIL] Unexpected health status")
                    return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        print(f"   Make sure webhook server is running at {WEBHOOK_URL}")
        return False


async def test_incoming_call():
    """Test 2: Incoming call webhook - Check Media Streams TwiML"""
    print("\n" + "="*60)
    print("TEST 2: Incoming Call Webhook (Media Streams)")
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
                print(f"[OK] Status: {response.status}")
                print(f"[OK] TwiML Response:")
                print(twiml)
                print()
                
                # Parse and validate Media Streams TwiML
                try:
                    root = ET.fromstring(twiml)
                    connect = root.find('Connect')
                    
                    if connect is None:
                        print("❌ TwiML missing <Connect> element")
                        return False
                    
                    stream = connect.find('Stream')
                    if stream is None:
                        print("❌ TwiML missing <Stream> element")
                        return False
                    
                    stream_url = stream.get('url')
                    if not stream_url:
                        print("❌ Stream missing 'url' attribute")
                        return False
                    
                    print(f"✅ TwiML contains Media Streams!")
                    print(f"✅ Stream URL: {stream_url}")
                    
                    # Validate stream URL format
                    if stream_url.startswith('wss://') or stream_url.startswith('ws://'):
                        print(f"✅ Stream URL format is correct (WebSocket)")
                        
                        # Check for custom parameters
                        params = stream.findall('Parameter')
                        param_dict = {p.get('name'): p.get('value') for p in params}
                        
                        print(f"✅ Custom Parameters:")
                        for name, value in param_dict.items():
                            print(f"   - {name}: {value}")
                        
                        if 'callSid' in param_dict and 'roomName' in param_dict:
                            print(f"✅ Required parameters present!")
                            return True
                        else:
                            print(f"❌ Missing required parameters")
                            return False
                    else:
                        print(f"❌ Stream URL format invalid (not WebSocket)")
                        return False
                        
                except ET.ParseError as e:
                    print(f"❌ Failed to parse TwiML: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_media_streams_configuration():
    """Test 3: Verify Media Streams Configuration"""
    print("\n" + "="*60)
    print("TEST 3: Media Streams Configuration Verification")
    print("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test multiple calls to ensure consistent configuration
            print("Testing multiple calls to verify Media Streams configuration...")
            
            for i in range(3):
                call_sid = f"CA_TEST_{i+1}"
                form_data = aiohttp.FormData()
                form_data.add_field('CallSid', call_sid)
                form_data.add_field('From', TEST_FROM_NUMBER)
                form_data.add_field('To', TEST_TO_NUMBER)
                
                async with session.post(f"{WEBHOOK_URL}/incoming-call", data=form_data) as response:
                    twiml = await response.text()
                    
                    # Extract Stream configuration
                    try:
                        root = ET.fromstring(twiml)
                        stream = root.find('.//Stream')
                        stream_url = stream.get('url')
                        
                        params = stream.findall('Parameter')
                        param_dict = {p.get('name'): p.get('value') for p in params}
                        
                        print(f"\nCall {i+1}:")
                        print(f"  Stream URL: {stream_url}")
                        print(f"  Room Name: {param_dict.get('roomName')}")
                        print(f"  Call SID: {param_dict.get('callSid')}")
                        
                        # Verify room name matches call SID
                        if call_sid in param_dict.get('roomName', ''):
                            print(f"  ✅ Room name correctly includes CallSid")
                        else:
                            print(f"  ❌ Room name doesn't match CallSid")
                            return False
                            
                    except Exception as e:
                        print(f"  ❌ Failed to parse: {e}")
                        return False
            
            print("\n✅ Media Streams configuration is consistent and correct!")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_metrics():
    """Test 4: Check metrics endpoint"""
    print("\n" + "="*60)
    print("TEST 4: Metrics Endpoint")
    print("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{WEBHOOK_URL}/metrics") as response:
                data = await response.json()
                print(f"✅ Status: {response.status}")
                print(f"✅ Metrics:")
                print(f"   Active calls: {data.get('active_calls')}")
                print(f"   Max concurrent: {data.get('max_concurrent_calls')}")
                print(f"   Utilization: {data.get('utilization_percent'):.1f}%")
                return response.status == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_call_status():
    """Test 5: Call status callback"""
    print("\n" + "="*60)
    print("TEST 5: Call Status Callback")
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


async def test_root_endpoint():
    """Test 6: Root endpoint"""
    print("\n" + "="*60)
    print("TEST 6: Root Endpoint")
    print("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{WEBHOOK_URL}/") as response:
                data = await response.json()
                print(f"✅ Status: {response.status}")
                print(f"✅ Response: {data}")
                
                if data.get('status') == 'healthy':
                    print(f"✅ Root endpoint responding correctly!")
                    return True
                else:
                    print(f"❌ Unexpected response from root endpoint")
                    return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def run_all_tests():
    """Run all tests in sequence"""
    print("\n")
    print("=" * 60)
    print(" " * 10 + "MEDIA STREAMS WEBHOOK TEST SUITE")
    print("=" * 60)
    print(f"\nTesting webhook at: {WEBHOOK_URL}")
    print("\n📋 Requirements:")
    print("   ✓ webhook_server.py running (or deployed to Render)")
    print("   ✓ Environment variables configured")
    print("\n⚠️  NOTE: This tests webhook configuration, not full phone calls")
    print("   For full end-to-end testing, make a real phone call.")
    print("\nPress Ctrl+C to abort at any time")
    
    await asyncio.sleep(2)
    
    results = {}
    
    # Test 1: Health Check
    results['health'] = await test_health_check()
    
    if not results['health']:
        print("\n❌ Health check failed! Make sure webhook server is accessible.")
        if WEBHOOK_URL == "http://localhost:8000":
            print("   Local: python webhook_server.py")
        else:
            print(f"   Remote: Check that {WEBHOOK_URL} is deployed and running")
        return
    
    await asyncio.sleep(1)
    
    # Test 2: Root endpoint
    results['root'] = await test_root_endpoint()
    await asyncio.sleep(1)
    
    # Test 3: Incoming Call (Media Streams TwiML)
    results['media_streams_twiml'] = await test_incoming_call()
    await asyncio.sleep(1)
    
    # Test 4: Media Streams Configuration
    results['media_streams_config'] = await test_media_streams_configuration()
    await asyncio.sleep(1)
    
    # Test 5: Metrics
    results['metrics'] = await test_metrics()
    await asyncio.sleep(1)
    
    # Test 6: Call Status
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
        print("\n🎉 ALL TESTS PASSED! Your Media Streams webhook is configured correctly!")
        print("\nWhat was tested:")
        print("  ✅ Webhook server is running and healthy")
        print("  ✅ Returns correct Media Streams TwiML")
        print("  ✅ WebSocket URLs are properly formatted")
        print("  ✅ Room names include CallSid")
        print("  ✅ Metrics endpoint working")
        print("  ✅ Call status callback working")
        print("\nNext steps:")
        if WEBHOOK_URL == "http://localhost:8000":
            print("  1. Deploy webhook to Render.com (see RENDER_DEPLOYMENT.md)")
            print("  2. Deploy agent.py as background worker")
            print("  3. Update WEBHOOK_URL in this test script")
            print("  4. Re-run tests against deployed URL")
            print("  5. Configure Twilio webhook URL")
            print("  6. Test with a REAL phone call! 📞")
        else:
            print("  1. Make sure agent.py is also deployed/running")
            print("  2. Configure Twilio webhook URL:")
            print(f"     {WEBHOOK_URL}/incoming-call")
            print("  3. Test with a REAL phone call! 📞")
        print("\n⚠️  Note: This test validates configuration only.")
        print("   Real phone testing is required for full validation.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print("\n" + "="*60)


async def run_quick_test():
    """Quick test - just health check and Media Streams TwiML"""
    print("\n")
    print("=" * 60)
    print(" " * 18 + "QUICK WEBHOOK TEST")
    print("=" * 60)
    
    # Health check
    health_ok = await test_health_check()
    if not health_ok:
        print("\n❌ Webhook is not running or not accessible.")
        if WEBHOOK_URL == "http://localhost:8000":
            print("   Run: python webhook_server.py")
        else:
            print(f"   Check: {WEBHOOK_URL}")
        return
    
    # Incoming call (Media Streams TwiML)
    await asyncio.sleep(1)
    twiml_ok = await test_incoming_call()
    
    print("\n" + "="*60)
    if health_ok and twiml_ok:
        print("✅ QUICK TEST PASSED!")
        print("\nYour Media Streams webhook is configured correctly.")
        print("  ✅ Webhook responding")
        print("  ✅ Returns valid Media Streams TwiML")
        print("\nRun without --quick flag for complete test suite.")
    else:
        print("⚠️  Some issues detected. Check output above.")
    print("="*60)


def print_help():
    """Print usage help"""
    print("""
Media Streams Webhook Test

This script tests your Twilio Media Streams webhook configuration without
needing a real phone. It validates that your webhook returns correct TwiML.

Usage:
    python test_webhook_deployment.py [options]

Options:
    --quick     Quick test (health check + TwiML validation)
    --full      Full test suite (default)
    --help      Show this help message

Examples:
    python test_webhook_deployment.py              # Full test suite
    python test_webhook_deployment.py --quick      # Quick test
    python test_webhook_deployment.py --full       # Full test (explicit)

Configuration:
    Edit WEBHOOK_URL at the top of this file:
    - Local testing:  http://localhost:8000
    - Render deploy:  https://your-app.onrender.com

Requirements:
    1. Webhook server running (locally or deployed)
    2. Environment variables configured
    3. Dependencies: pip install aiohttp

What gets tested:
    ✓ Health endpoints
    ✓ Media Streams TwiML generation
    ✓ WebSocket URL format validation
    ✓ Room name generation
    ✓ Metrics endpoint
    ✓ Call status callback

⚠️  Important: This validates webhook configuration only.
    For full end-to-end testing, make a real phone call!

Testing Deployed Version:
    1. Update WEBHOOK_URL to your Render URL
    2. Run this script
    3. If tests pass, configure Twilio webhook
    4. Make a test phone call

Note: This does NOT simulate actual phone calls.
      It verifies your webhook is configured correctly.
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

