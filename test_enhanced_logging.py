#!/usr/bin/env python3
"""
Test script for enhanced chain of thought and query logging functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from healthcare_chatbot_service import HealthcareResponseGenerator, HealthcareConversationManager
from healthcare_database_manager_sqlserver import HealthcareDatabaseManager
import json

def test_enhanced_logging():
    """Test the enhanced logging functionality"""
    print("🧪 Testing Enhanced Chain of Thought and Query Logging")
    print("=" * 60)
    
    # Initialize the database manager first
    try:
        db_manager = HealthcareDatabaseManager()
        print("✅ Database manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database manager: {e}")
        return
    
    # Initialize the conversation manager
    try:
        conversation_manager = HealthcareConversationManager()
        print("✅ Conversation manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize conversation manager: {e}")
        return
    
    # Initialize the chatbot service
    try:
        chatbot = HealthcareResponseGenerator(db_manager)
        print("✅ Healthcare Response Generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return
    
    # Test scenarios with different types of queries
    test_scenarios = [
        {
            "name": "Patient Search Query",
            "message": "Find patients named John Smith",
            "expected_intent": "search"
        },
        {
            "name": "Availability Check Query", 
            "message": "Show me all available employees for today",
            "expected_intent": "availability"
        },
        {
            "name": "Appointment Booking Query",
            "message": "Book an appointment with Dr. Johnson for patient Mary Wilson tomorrow at 2pm",
            "expected_intent": "book_appointment"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔬 Test Scenario {i}: {scenario['name']}")
        print("-" * 40)
        print(f"Input: {scenario['message']}")
        
        try:
            # Generate response with enhanced logging
            response = chatbot.generate_response(
                scenario['message'], 
                conversation_manager
            )
            
            print(f"✅ Response generated successfully")
            print(f"📝 Intent: {response.intent}")
            print(f"📊 Status: {response.status}")
            print(f"💭 Chain of thoughts length: {len(response.chain_of_thoughts)}")
            
            # Print chain of thoughts
            if response.chain_of_thoughts:
                print("\n🧠 Chain of Thoughts:")
                for j, thought in enumerate(response.chain_of_thoughts, 1):
                    print(f"   {j}. {thought}")
            
            # Print query executed if available
            if response.query_executed:
                print(f"\n🗃️ SQL Query Executed: {response.query_executed[:100]}...")
            
            print(f"📝 Response: {response.message[:100]}...")
            
        except Exception as e:
            print(f"❌ Error in scenario {i}: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Enhanced Logging Test Completed")
    
    # Check if log file was created
    if os.path.exists("flask_server.log"):
        print("✅ Log file created successfully")
        with open("flask_server.log", "r") as f:
            lines = f.readlines()
            print(f"📊 Log file contains {len(lines)} lines")
            if lines:
                print("📝 Recent log entries:")
                for line in lines[-5:]:  # Show last 5 lines
                    print(f"   {line.strip()}")
    else:
        print("⚠️ Log file not created yet")

if __name__ == "__main__":
    test_enhanced_logging()
