#!/usr/bin/env python3
"""
Test script to verify availability query integration with UI
"""

import requests
import json

def test_availability_api():
    """Test the availability API endpoint"""
    
    print("=== Testing Availability Query through API ===\n")
    
    # Test cases
    test_queries = [
        "get me the availability of jon snow",
        "show availability for Dr. Smith", 
        "when is John available",
        "availability of Mary Johnson"
    ]
    
    base_url = "http://localhost:5001"
    
    for query in test_queries:
        print(f"Testing query: '{query}'")
        print("-" * 50)
        
        try:
            # Test direct query endpoint
            response = requests.post(f"{base_url}/api/query-direct", 
                                   json={"query": query},
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Query successful!")
                print(f"   Success: {result.get('success', False)}")
                print(f"   Message: {result.get('message', 'No message')}")
                print(f"   Results: {len(result.get('results', []))} records")
                if result.get('sql_query'):
                    print(f"   SQL: {result['sql_query'][:100]}...")
            else:
                print(f"❌ Query failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
        
        print("\n")

def test_chat_endpoint():
    """Test the chat endpoint with availability queries"""
    
    print("=== Testing Chat Endpoint with Availability Queries ===\n")
    
    base_url = "http://localhost:5001"
    
    # Test availability query through chat endpoint
    query = "get me the availability of jon snow"
    
    try:
        response = requests.post(f"{base_url}/api/chat", 
                               json={"message": query},
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat query successful!")
            print(f"   Session ID: {result.get('session_id', 'N/A')}")
            print(f"   Response: {result.get('response', 'No response')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Intent: {result.get('data', {}).get('intent', 'N/A')}")
            print(f"   Chain of thoughts: {len(result.get('chain_of_thoughts', []))} thoughts")
        else:
            print(f"❌ Chat query failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Chat request failed: {str(e)}")

def check_server_status():
    """Check if the server is running"""
    
    print("=== Checking Server Status ===\n")
    
    base_url = "http://localhost:5001"
    
    try:
        response = requests.get(f"{base_url}/api/test-db", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Server is running!")
            print(f"   Database connection: {'✅' if result.get('success') else '❌'}")
            print(f"   Server: {result.get('server', 'N/A')}")
            print(f"   Database: {result.get('database', 'N/A')}")
        else:
            print(f"❌ Server check failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not responding: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Availability Query UI Integration\n")
    
    # First check if server is running
    if not check_server_status():
        print("⚠️ Server is not running. Please start the app first with:")
        print("   python3 app/healthcare_chatbot_app.py")
        exit(1)
    
    print("\n")
    
    # Test direct query endpoint
    test_availability_api()
    
    # Test chat endpoint
    test_chat_endpoint()
    
    print("🧪 Testing complete!")
    print("\n💡 You can also test manually by:")
    print("   1. Open http://localhost:5001 in your browser")
    print("   2. Type: 'get me the availability of jon snow'")
    print("   3. Check if the query works correctly")
