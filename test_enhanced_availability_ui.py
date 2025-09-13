"""
Test the Enhanced Availability Query Processor in UI Integration Context
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_availability_query_processor import get_availability_query_processor
from healthcare_chatbot_service import HealthcareResponseGenerator
from healthcare_database_manager_sqlserver import HealthcareDatabaseManager

def test_enhanced_availability_ui():
    """Test the enhanced availability processor as it would work in the UI"""
    
    print("🧪 Testing Enhanced Availability Query Processor for UI Integration")
    print("=" * 70)
    
    # Initialize components (simulating UI initialization)
    try:
        print("🔧 Initializing database manager...")
        db_manager = HealthcareDatabaseManager()
        
        print("🔧 Initializing response generator...")
        response_generator = HealthcareResponseGenerator(db_manager)
        
        print("✅ UI components initialized successfully\n")
        
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return
    
    # Test queries that would come from the UI
    test_queries = [
        "get me the availability of jon snow",
        "check availability of jane smith on wednesday", 
        "who is available on monday",
        "show me all available employees"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test Query {i}: '{query}'")
        print("-" * 50)
        
        try:
            # Simulate UI calling the response generator
            response = response_generator._handle_availability_check(
                message=query,
                entities={},  # UI would parse entities
                websocket_session_id=f"test_session_{i}",
                chain_of_thoughts=[]
            )
            
            print(f"✅ Status: {response.status}")
            print(f"🎯 Intent: {response.intent}")
            print(f"📊 Confidence: {response.confidence}")
            print(f"⏱️ Execution Time: {response.execution_time:.3f}s")
            
            print(f"\n📝 Response Message:")
            print(response.message)
            
            if response.suggested_actions:
                print(f"\n💡 Suggestions: {', '.join(response.suggested_actions)}")
            
            if response.chain_of_thoughts:
                print(f"\n🧠 Chain of Thoughts ({len(response.chain_of_thoughts)} steps):")
                for j, thought in enumerate(response.chain_of_thoughts[-5:], 1):  # Show last 5
                    print(f"   {j}. {thought}")
            
            if response.data and 'sql_query' in response.data:
                print(f"\n🗄️ SQL Query Generated:")
                query_lines = response.data['sql_query'].split('\n')
                for line in query_lines:
                    if line.strip():
                        print(f"   {line}")
                        
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("🎉 Enhanced Availability Query Processor UI Integration Test Complete")

if __name__ == "__main__":
    test_enhanced_availability_ui()
