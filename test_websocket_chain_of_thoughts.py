#!/usr/bin/env python3
"""
Test script for WebSocket chain of thoughts functionality
"""

import sys
import os
import time

# Add the current directory to Python path
sys.path.append('/Users/xyloite/workspace/M-pm')

def test_websocket_import():
    """Test WebSocket import"""
    print("🧪 Testing WebSocket import...")
    try:
        from websocket_chain_of_thoughts import ChainOfThoughtsWebSocket, get_chain_of_thoughts_ws
        print("✅ WebSocket module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ WebSocket import failed: {e}")
        return False

def test_websocket_creation():
    """Test WebSocket creation"""
    print("\n🧪 Testing WebSocket creation...")
    try:
        from websocket_chain_of_thoughts import ChainOfThoughtsWebSocket
        
        # Create WebSocket instance
        ws = ChainOfThoughtsWebSocket()
        print("✅ WebSocket instance created successfully")
        
        # Test session creation
        session_id = ws.create_session()
        print(f"✅ Session created: {session_id}")
        
        # Test thought emission (without Flask app)
        ws.emit_thought_step(session_id, "Test Step", "Testing thought emission", "completed")
        print("✅ Thought emission test passed")
        
        return True
    except Exception as e:
        print(f"❌ WebSocket creation failed: {e}")
        return False

def test_chatbot_integration():
    """Test chatbot integration with WebSocket"""
    print("\n🧪 Testing chatbot integration...")
    try:
        from healthcare_database_manager_sqlserver import HealthcareDatabaseManager
        from healthcare_chatbot_service import HealthcareResponseGenerator, HealthcareConversationManager
        
        # Initialize components
        db_manager = HealthcareDatabaseManager()
        chatbot = HealthcareResponseGenerator(db_manager)
        conversation_manager = HealthcareConversationManager()
        
        print("✅ Chatbot components initialized")
        
        # Test response generation (this should include WebSocket session creation)
        response = chatbot.generate_response("Hi, can you help me book an appointment?", conversation_manager)
        
        print(f"✅ Response generated: {response.message[:50]}...")
        print(f"✅ Chain of thoughts: {len(response.chain_of_thoughts)} steps")
        print(f"✅ WebSocket session: {response.websocket_session_id}")
        print(f"✅ Processing time: {response.processing_time_ms}ms")
        
        return True
    except Exception as e:
        print(f"❌ Chatbot integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all WebSocket tests"""
    print("🧪 WEBSOCKET CHAIN OF THOUGHTS TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("WebSocket Import", test_websocket_import),
        ("WebSocket Creation", test_websocket_creation),
        ("Chatbot Integration", test_chatbot_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 WEBSOCKET TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All WebSocket tests passed! Real-time chain of thoughts ready.")
    else:
        print("⚠️  Some tests failed. Check WebSocket dependencies.")

if __name__ == "__main__":
    main()
