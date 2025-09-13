#!/usr/bin/env python3
"""
Test availability query with corrected JOIN and schema access
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_availability_with_live_server():
    """Test availability query by making HTTP request to live server"""
    import requests
    import json
    
    try:
        url = "http://localhost:5001/api/chat"
        
        test_queries = [
            "get me the availability of jon snow",
            "who is available on monday", 
            "show all available employees"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            
            payload = {
                "message": query,
                "session_id": "test_session_123"
            }
            
            try:
                response = requests.post(url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Status: {response.status_code}")
                    print(f"📝 Response: {result.get('message', 'No message')[:100]}...")
                    if 'chain_of_thoughts' in result:
                        print(f"🧠 Chain of thoughts: {len(result['chain_of_thoughts'])} steps")
                    if 'sql_query' in result:
                        print(f"🗄️ SQL generated: {result['sql_query'][:100]}...")
                else:
                    print(f"❌ Status: {response.status_code}")
                    print(f"📝 Error: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                print("❌ Server not running - start with: python3 healthcare_chatbot_app.py")
            except Exception as e:
                print(f"❌ Request failed: {e}")
        
    except ImportError:
        print("❌ requests library not available")

if __name__ == "__main__":
    print("🧪 Testing availability queries with corrected schema access...")
    test_availability_with_live_server()
