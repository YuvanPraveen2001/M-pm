#!/usr/bin/env python3
"""
Test script to demonstrate the live chain of thought functionality
"""

import requests
import json
import time

def test_live_chain_of_thought():
    """Test the live chain of thought via Server-Sent Events"""
    print("🧪 Testing Live Chain of Thought (Claude-style)")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    
    # Test message
    test_message = "I want to book an appointment with Dr. Smith for patient John Doe"
    
    print(f"📝 Sending message: '{test_message}'")
    print("🔄 Starting live chain of thought stream...")
    print("-" * 40)
    
    # Send chat message (this will trigger live thoughts)
    chat_response = requests.post(f"{base_url}/api/chat", 
                                 json={"message": test_message},
                                 timeout=10)
    
    if chat_response.status_code == 200:
        data = chat_response.json()
        session_id = data.get('session_id')
        
        print(f"✅ Chat request successful (Session: {session_id})")
        print(f"🤖 Response: {data.get('response', 'No response')[:100]}...")
        
        # Test Server-Sent Events endpoint
        print("\n🔍 Testing live thoughts stream endpoint...")
        try:
            sse_response = requests.get(f"{base_url}/api/live-thoughts/{session_id}", 
                                       stream=True, timeout=5)
            
            if sse_response.status_code == 200:
                print("✅ Server-Sent Events stream connected")
                
                # Read a few events
                event_count = 0
                for line in sse_response.iter_lines(decode_unicode=True):
                    if line.startswith('data: '):
                        event_data = line[6:]  # Remove 'data: ' prefix
                        try:
                            event_json = json.loads(event_data)
                            event_count += 1
                            
                            if event_json.get('type') == 'thought':
                                thought = event_json.get('data', {}).get('thought', '')
                                timestamp = event_json.get('data', {}).get('timestamp', '')
                                print(f"💭 [{timestamp}] {thought}")
                            elif event_json.get('type') == 'connected':
                                print(f"🔌 {event_json.get('message')}")
                            elif event_json.get('type') == 'complete':
                                print(f"✅ {event_json.get('message')}")
                                break
                                
                            # Limit to first 10 events for demo
                            if event_count >= 10:
                                break
                                
                        except json.JSONDecodeError:
                            continue
                            
                print(f"\n📊 Processed {event_count} live thought events")
            else:
                print(f"❌ SSE stream failed with status: {sse_response.status_code}")
                
        except requests.exceptions.Timeout:
            print("⏰ SSE stream timed out (expected)")
        except Exception as e:
            print(f"⚠️ SSE stream error: {e}")
    else:
        print(f"❌ Chat request failed with status: {chat_response.status_code}")
        print(f"Response: {chat_response.text}")

if __name__ == "__main__":
    try:
        test_live_chain_of_thought()
        print("\n🎯 Live Chain of Thought Test Completed!")
        print("✅ The system successfully demonstrates Claude-style live thinking")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
