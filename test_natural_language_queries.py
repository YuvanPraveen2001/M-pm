"""
Natural Language Query Test Script
Test the chatbot's ability to process queries like "Check availability of John this Wednesday"
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from healthcare_database_manager_sqlserver import HealthcareDatabaseManager
from natural_language_processor import HealthcareQueryProcessor

def test_natural_language_queries():
    """Test various natural language queries"""
    
    print("🤖 Healthcare Natural Language Query Processor Test")
    print("=" * 60)
    
    try:
        # Initialize the database manager and query processor
        db_manager = HealthcareDatabaseManager()
        query_processor = HealthcareQueryProcessor(db_manager)
        
        # Test queries
        test_queries = [
            "Check me the availability of John this Wednesday",
            "Show me Sarah's appointments today",
            "What's Dr. Smith's schedule tomorrow?",
            "Find appointments for Jennifer next Monday",
            "Is Michael available this Friday?",
            "Check availability of Lisa",
            "Show schedule for Dr. Johnson this week",
            "What appointments does Mary have on 9/15/2025?",
            "Find free time for Dr. Brown tomorrow"
        ]
        
        print("🔍 Testing Natural Language Queries:")
        print("-" * 40)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: '{query}'")
            print("-" * 30)
            
            try:
                result = query_processor.process_query(query)
                
                if result['success']:
                    print("✅ Success!")
                    print(f"📊 Analysis: {result['analysis']}")
                    print(f"💬 Response: {result['message'][:200]}...")
                    print(f"📈 Records found: {len(result.get('results', []))}")
                    
                    if result.get('sql_query'):
                        sql = result['sql_query'].replace('\n', ' ').strip()
                        print(f"🔍 SQL: {sql[:100]}...")
                else:
                    print("❌ Failed!")
                    print(f"💬 Message: {result['message']}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print("\n" + "=" * 60)
        print("✅ Natural Language Query Testing Complete!")
        
        # Interactive mode
        print("\n🎯 Interactive Mode - Try your own queries!")
        print("Type 'quit' to exit")
        print("-" * 40)
        
        while True:
            try:
                user_query = input("\n📝 Enter your query: ").strip()
                
                if user_query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_query:
                    continue
                
                print(f"🔍 Processing: '{user_query}'")
                result = query_processor.process_query(user_query)
                
                print(f"✅ Success: {result['success']}")
                print(f"💬 Response:\n{result['message']}")
                
                if result.get('sql_query'):
                    print(f"\n🔍 Generated SQL:\n{result['sql_query']}")
                
                if result.get('results'):
                    print(f"\n📊 Found {len(result['results'])} records")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print("\n👋 Goodbye!")
        
    except Exception as e:
        print(f"❌ Failed to initialize query processor: {str(e)}")
        print("\n💡 Make sure your SQL Server is running and .env is configured properly.")
        return False
    
    return True

if __name__ == "__main__":
    test_natural_language_queries()
