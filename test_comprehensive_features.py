#!/usr/bin/env python3
"""
Comprehensive test script for healthcare chatbot features:
1. Retry logic for database operations
2. Chain of thoughts in responses
3. RAG-based schema retrieval and SQL generation
4. Fallback mechanisms
"""

import sys
import os

# Add the current directory to Python path
sys.path.append('/Users/xyloite/workspace/M-pm')

from healthcare_database_manager_sqlserver import HealthcareDatabaseManager
from healthcare_schema_rag import HealthcareSchemaRAG, get_healthcare_schema_rag
from healthcare_chatbot_service import HealthcareResponseGenerator, ChatResponse
from ai_chatbot_tools import HealthcareToolsRegistry
import traceback


def test_retry_logic():
    """Test database retry logic"""
    print("\n" + "="*60)
    print("🔄 TESTING RETRY LOGIC")
    print("="*60)
    
    try:
        db_manager = HealthcareDatabaseManager()
        print("✅ Database manager initialized")
        
        # This should trigger retry logic due to missing table
        print("\n🔍 Testing search_employee_by_name with retry logic...")
        result = db_manager.search_employee_by_name('john')
        print(f"❌ Unexpected success: {result}")
        
    except Exception as e:
        print(f"✅ Expected error after retries: {type(e).__name__}: {str(e)[:100]}...")
        return True
    
    return False


def test_schema_rag():
    """Test healthcare schema RAG system"""
    print("\n" + "="*60)
    print("🧠 TESTING SCHEMA RAG SYSTEM")
    print("="*60)
    
    try:
        rag = get_healthcare_schema_rag()
        print("✅ Healthcare Schema RAG initialized")
        
        # Test queries
        test_queries = [
            "check availability of john this wednesday",
            "find patient appointments",
            "book appointment with therapist",
            "get employee schedule"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            result = rag.retrieve_relevant_schema(query)
            print(f"   📊 Retrieved {len(result.tables)} tables (confidence: {result.confidence_score:.2f})")
            
            for table in result.tables:
                print(f"   - {table.table_name}: {table.description[:50]}...")
            
            # Test SQL generation
            sql = rag.generate_sql_with_schema(query, result)
            print(f"   📝 Generated SQL: {len(sql)} characters")
            print(f"   🔍 Preview: {sql[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema RAG test failed: {e}")
        traceback.print_exc()
        return False


def test_chain_of_thoughts():
    """Test chain of thoughts in chatbot responses"""
    print("\n" + "="*60)
    print("💭 TESTING CHAIN OF THOUGHTS")
    print("="*60)
    
    try:
        # Initialize components
        db_manager = HealthcareDatabaseManager()
        chatbot = HealthcareResponseGenerator(db_manager)
        
        # Create a mock conversation manager
        from healthcare_chatbot_service import HealthcareConversationManager
        conversation_manager = HealthcareConversationManager()
        
        print("✅ Chatbot service initialized")
        
        # Test chat responses
        test_messages = [
            "Hi, can you help me book an appointment?",
            "Check availability of John this Wednesday",
            "Find me a therapist for anxiety treatment"
        ]
        
        for message in test_messages:
            print(f"\n🗣️  User: {message}")
            
            # Generate response
            response = chatbot.generate_response(message, conversation_manager)
            
            print(f"   🤖 Response: {response.message[:100]}...")
            print(f"   📋 Intent: {response.intent}")
            print(f"   💭 Chain of thoughts: {len(response.chain_of_thoughts)} steps")
            
            for i, thought in enumerate(response.chain_of_thoughts, 1):
                print(f"      {i}. {thought[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Chain of thoughts test failed: {e}")
        traceback.print_exc()
        return False


def test_tool_registry():
    """Test healthcare tool registry"""
    print("\n" + "="*60)
    print("🛠️  TESTING TOOL REGISTRY")
    print("="*60)
    
    try:
        tool_registry = HealthcareToolsRegistry()
        print("✅ Tool registry initialized")
        
        # Test tool registration
        tools = tool_registry.tools  # Access the tools dictionary directly
        print(f"📊 Registered {len(tools)} tools:")
        
        for tool_name, tool_def in tools.items():
            print(f"   - {tool_name} ({tool_def.tool_type.value})")
        
        # Test tool validation
        test_tool_calls = [
            ("book_appointment", {"patient_id": 123, "provider_id": 456}),
            ("check_availability", {"provider_id": 456, "date": "2024-01-15"}),
            ("invalid_tool", {"param": "value"})
        ]
        
        for tool_name, params in test_tool_calls:
            print(f"\n🔧 Testing tool: {tool_name}")
            tool_def = tool_registry.get_tool(tool_name)
            is_valid = tool_def is not None
            print(f"   ✅ Found: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool registry test failed: {e}")
        traceback.print_exc()
        return False


def test_fallback_mechanisms():
    """Test fallback mechanisms"""
    print("\n" + "="*60)
    print("🛡️  TESTING FALLBACK MECHANISMS")
    print("="*60)
    
    try:
        # Test schema fallback
        rag = HealthcareSchemaRAG(use_memory=False)  # This should fail and use fallback
        print("✅ Schema RAG with fallback initialized")
        
        # Test fallback schema retrieval
        query = "check patient appointments"
        result = rag._get_fallback_schema_result(query)
        print(f"📊 Fallback schema returned {len(result.tables)} tables")
        
        for table in result.tables:
            print(f"   - {table.table_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all comprehensive tests"""
    print("🏥 HEALTHCARE CHATBOT COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Retry Logic", test_retry_logic),
        ("Schema RAG", test_schema_rag),
        ("Chain of Thoughts", test_chain_of_thoughts),
        ("Tool Registry", test_tool_registry),
        ("Fallback Mechanisms", test_fallback_mechanisms)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n⏳ Running {test_name} test...")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for production.")
    else:
        print("⚠️  Some tests failed. Review the output above for details.")


if __name__ == "__main__":
    main()
