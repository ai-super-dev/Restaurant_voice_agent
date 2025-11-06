"""
Test LiveKit SIP Integration
Tests the webhook server's SIP configuration without needing a real phone
Validates that webhook returns correct SIP TwiML for LiveKit integration
"""

import asyncio
import aiohttp
from xml.etree import ElementTree as ET


# Configuration
WEBHOOK_URL = "http://localhost:8000"  # Change to your deployed URL for remote testing
TEST_CALL_SID = "CA_TEST_123456789"
TEST_FROM_NUMBER = "+15551234567"
TEST_TO_NUMBER = "+15559876543"


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
    """Test 2: Incoming call webhook - Check SIP TwiML"""
    print("\n" + "="*60)
    print("TEST 2: Incoming Call Webhook (SIP)")
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
                print(twiml)
                print()
                
                # Parse and validate SIP TwiML
                try:
                    root = ET.fromstring(twiml)
                    dial = root.find('Dial')
                    if dial is not None:
                        sip = dial.find('Sip')
                        if sip is not None and sip.text:
                            sip_uri = sip.text
                            print(f"✅ TwiML contains SIP dial!")
                            print(f"✅ SIP URI: {sip_uri}")
                            
                            # Validate SIP URI format
                            if sip_uri.startswith('sip:') and 'livekit.cloud' in sip_uri:
                                print(f"✅ SIP URI format is correct!")
                                print(f"✅ Room name: {sip_uri.split('@')[0].replace('sip:', '')}")
                                return True
                            else:
                                print(f"❌ SIP URI format invalid")
                                return False
                        else:
                            print("❌ TwiML missing <Sip> element")
                            return False
                    else:
                        print("❌ TwiML missing <Dial> element")
                        return False
                except ET.ParseError as e:
                    print(f"❌ Failed to parse TwiML: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_sip_configuration():
    """Test 3: Verify SIP Configuration"""
    print("\n" + "="*60)
    print("TEST 3: SIP Configuration Verification")
    print("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test multiple calls to ensure consistent SIP URIs
            print("Testing multiple calls to verify SIP configuration...")
            
            for i in range(3):
                call_sid = f"CA_TEST_{i+1}"
                form_data = aiohttp.FormData()
                form_data.add_field('CallSid', call_sid)
                form_data.add_field('From', TEST_FROM_NUMBER)
                form_data.add_field('To', TEST_TO_NUMBER)
                
                async with session.post(f"{WEBHOOK_URL}/incoming-call", data=form_data) as response:
                    twiml = await response.text()
                    
                    # Extract SIP URI
                    try:
                        root = ET.fromstring(twiml)
                        sip_uri = root.find('.//Sip').text
                        room_name = sip_uri.split('@')[0].replace('sip:', '')
                        domain = sip_uri.split('@')[1]
                        
                        print(f"\nCall {i+1}:")
                        print(f"  Room: {room_name}")
                        print(f"  Domain: {domain}")
                        
                        # Verify room name matches call SID
                        if call_sid in room_name:
                            print(f"  ✅ Room name correctly includes CallSid")
                        else:
                            print(f"  ❌ Room name doesn't match CallSid")
                            return False
                            
                    except Exception as e:
                        print(f"  ❌ Failed to parse: {e}")
                        return False
            
            print("\n✅ SIP configuration is consistent and correct!")
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
                print(f"   Utilization: {data.get('utilization_percent')}%")
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


async def run_all_tests():
    """Run all tests in sequence"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*12 + "LIVEKIT SIP INTEGRATION TEST" + " "*19 + "║")
    print("╚" + "="*58 + "╝")
    print(f"\nTesting webhook at: {WEBHOOK_URL}")
    print("Make sure webhook_server.py is running!")
    print("\n⚠️  NOTE: This tests SIP configuration, not full phone calls")
    print("   For full end-to-end testing, make a real phone call.")
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
    
    # Test 2: Incoming Call (SIP TwiML)
    results['sip_twiml'] = await test_incoming_call()
    await asyncio.sleep(1)
    
    # Test 3: SIP Configuration
    results['sip_config'] = await test_sip_configuration()
    await asyncio.sleep(1)
    
    # Test 4: Metrics
    results['metrics'] = await test_metrics()
    await asyncio.sleep(1)
    
    # Test 5: Call Status
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
        print("\n🎉 ALL TESTS PASSED! Your SIP webhook is configured correctly!")
        print("\nWhat was tested:")
        print("  ✅ Webhook server is running")
        print("  ✅ Returns correct SIP TwiML")
        print("  ✅ SIP URIs are properly formatted")
        print("  ✅ Room names include CallSid")
        print("  ✅ Metrics endpoint working")
        print("\nNext steps:")
        print("  1. Deploy webhook to Render.com")
        print("  2. Deploy agent.py as background worker")
        print("  3. Configure Twilio webhook URL")
        print("  4. Test with a REAL phone call! 📞")
        print("\n⚠️  Note: This test validates configuration only.")
        print("   Real phone testing is required for full validation.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print("\n" + "="*60)


async def run_quick_test():
    """Quick test - just health check and SIP TwiML"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "QUICK SIP TEST" + " "*29 + "║")
    print("╚" + "="*58 + "╝")
    
    # Health check
    health_ok = await test_health_check()
    if not health_ok:
        print("\n❌ Webhook is not running or not accessible.")
        print("   Run: python webhook_server.py")
        return
    
    # Incoming call (SIP TwiML)
    await asyncio.sleep(1)
    sip_ok = await test_incoming_call()
    
    print("\n" + "="*60)
    if health_ok and sip_ok:
        print("✅ QUICK TEST PASSED!")
        print("\nYour SIP webhook is configured correctly.")
        print("  ✅ Webhook responding")
        print("  ✅ Returns valid SIP TwiML")
        print("\nRun without --quick flag for complete test suite.")
    else:
        print("⚠️  Some issues detected. Check output above.")
    print("="*60)


def print_help():
    """Print usage help"""
    print("""
LiveKit SIP Integration Test

This script tests your LiveKit SIP webhook configuration without needing
a real phone. It validates that your webhook returns correct SIP TwiML.

Usage:
    python test_phone_simulation.py [options]

Options:
    --quick     Quick test (health check + SIP TwiML validation)
    --full      Full test suite (default)
    --help      Show this help message

Examples:
    python test_phone_simulation.py              # Full test suite
    python test_phone_simulation.py --quick      # Quick test
    python test_phone_simulation.py --full       # Full test (explicit)

Requirements:
    1. webhook_server.py must be running (python webhook_server.py)
    2. LIVEKIT_SIP_DOMAIN configured in .env or config
    3. Install dependencies: pip install -r requirements.txt

What gets tested:
    ✓ Health endpoints
    ✓ SIP TwiML generation
    ✓ SIP URI format validation
    ✓ Room name generation
    ✓ Metrics endpoint
    ✓ Call status callback

⚠️  Important: This validates webhook configuration only.
    For full end-to-end testing, make a real phone call!

Note: This does NOT simulate actual SIP calls (requires real phone).
      It verifies your webhook is configured correctly for LiveKit SIP.
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

