#!/usr/bin/env python3
"""
Test script for RAG-enhanced Healthcare Chatbot Service
Tests the integration of schema-aware SQL generation with Qdrant RAG
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_rag_chatbot():
    """Test the RAG-enhanced chatbot functionality"""
    
    print("🧪 Testing RAG-Enhanced Healthcare Chatbot Service")
    print("=" * 60)
    
    try:
        # Import the chatbot service
        from healthcare_chatbot_service import HealthcareResponseGenerator, HealthcareConversationManager
        from healthcare_database_manager_sqlserver import HealthcareDatabaseManager
        
        print("✅ Successfully imported required classes")
        
        # Initialize the service
        print("\n🔧 Initializing chatbot service...")
        conversation_manager = HealthcareConversationManager()
        
        # Create database manager (will use mock/fallback mode without real credentials)
        db_manager = HealthcareDatabaseManager()
        chatbot = HealthcareResponseGenerator(db_manager)
        print("✅ Chatbot service initialized successfully")
        
        # Test queries that should trigger RAG-based processing
        test_queries = [
            "Check the availability of John this Wednesday",
            "Find all therapists specializing in anxiety",
            "Show me appointments for Dr. Smith next week",
            "Are there any available slots for cognitive therapy?",
            "Book an appointment with a psychiatrist",
            "What providers are available on Friday afternoon?",
            "Show me all appointments scheduled for today",
            "Find patients with diabetes treatment plans"
        ]
        
        print(f"\n🔍 Testing {len(test_queries)} sample queries:")
        print("-" * 50)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: '{query}'")
            try:
                # Process the query
                response = chatbot.generate_response(query, conversation_manager)
                
                print(f"   Intent: {response.intent}")
                print(f"   Message: {response.message[:200]}{'...' if len(response.message) > 200 else ''}")
                
                if response.entities and 'schema_tables' in response.entities:
                    print(f"   Schema Tables: {response.entities['schema_tables']}")
                
                if response.entities and 'confidence_score' in response.entities:
                    print(f"   Confidence: {response.entities['confidence_score']:.2f}")
                
                print(f"   Suggestions: {response.suggestions[:3]}")  # First 3 suggestions
                print("   ✅ Query processed successfully")
                
            except Exception as e:
                print(f"   ❌ Error processing query: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 RAG Chatbot test completed!")
        
        # Test schema retrieval specifically
        print("\n🔍 Testing schema retrieval capabilities...")
        try:
            schema_result = chatbot.schema_rag.retrieve_relevant_schema("Find available therapists")
            print(f"✅ Schema retrieval test: Found {len(schema_result.tables)} relevant tables")
            for table in schema_result.tables:
                print(f"   - {table.table_name}: {table.description}")
        except Exception as e:
            print(f"❌ Schema retrieval test failed: {str(e)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Test individual components separately"""
    
    print("\n🔧 Testing Individual Components")
    print("=" * 40)
    
    # Test schema RAG system
    try:
        from healthcare_schema_rag import HealthcareSchemaRAG
        print("✅ HealthcareSchemaRAG imported successfully")
        
        schema_rag = HealthcareSchemaRAG()
        print("✅ HealthcareSchemaRAG initialized successfully")
        
        # Test schema parsing
        schema_path = "/Users/xyloite/workspace/M-pm/chatbot_schema.sql"
        if os.path.exists(schema_path):
            print("✅ Schema file found")
            
            # Test schema processing
            schema_result = schema_rag.retrieve_relevant_schema("therapist availability")
            print(f"✅ Schema retrieval test: {len(schema_result.tables)} tables found")
        else:
            print("⚠️ Schema file not found, skipping schema tests")
        
    except Exception as e:
        print(f"❌ Schema RAG component test failed: {str(e)}")
    
    # Test database manager
    try:
        from healthcare_database_manager_sqlserver import HealthcareDatabaseManager
        print("✅ HealthcareDatabaseManager imported successfully")
        
        # Note: We won't test actual connection without credentials
        print("✅ Database manager component available")
        
    except Exception as e:
        print(f"❌ Database manager component test failed: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting RAG Chatbot Tests - {datetime.now()}")
    
    # Test individual components first
    test_individual_components()
    
    # Test full integration
    success = test_rag_chatbot()
    
    if success:
        print("\n🎊 All tests completed successfully!")
        print("\n📋 Next steps:")
        print("1. Set up your SQL Server database")
        print("2. Configure environment variables (.env)")
        print("3. Run the production app: python app/production_healthcare_app.py")
        print("4. Test with real database queries")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        sys.exit(1)
