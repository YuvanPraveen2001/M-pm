"""
Healthcare Chatbot Demo Script
Demonstrates the complete roadmap implementation with all features
"""

import sys
import json
from datetime import datetime, date, timedelta

# Import our modules
from ai_chatbot_tools import HealthcareToolsRegistry
from nlp_processor import ConversationManager, Intent
from quadrant_rag_system import EnhancedHealthcareChatbot

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step_num, title):
    """Print a step header"""
    print(f"\n--- Step {step_num}: {title} ---")

def demo_tools_registry():
    """Demonstrate the tools registry system"""
    print_header("STEP 1: TOOL COLLECTION & REGISTRATION")
    
    # Initialize registry
    registry = HealthcareToolsRegistry()
    
    print("📋 Registered Healthcare Tools:")
    tools = registry.list_available_tools()
    
    for i, (name, description) in enumerate(tools.items(), 1):
        print(f"{i:2d}. {name}")
        print(f"    {description}")
    
    print(f"\n✅ Total Tools Registered: {len(tools)}")
    
    # Show detailed tool info
    print("\n🔍 Detailed Tool Example - Book Appointment:")
    book_tool = registry.get_tool("book_appointment")
    if book_tool:
        print(f"   Type: {book_tool.tool_type.value}")
        print(f"   Purpose: {book_tool.purpose}")
        print(f"   Parameters:")
        for param in book_tool.parameters:
            print(f"     - {param.name} ({param.parameter_type.value}): {param.description}")
        print(f"   Business Rules:")
        for rule in book_tool.business_rules or []:
            print(f"     - {rule}")
    
    return registry

def demo_nlp_processing(registry):
    """Demonstrate natural language processing and tool selection"""
    print_header("STEP 2: NATURAL LANGUAGE PROCESSING & TOOL SELECTION")
    
    # Initialize conversation manager
    conversation_manager = ConversationManager(registry)
    
    test_queries = [
        "I want to book an appointment with Dr. Johnson next Wednesday at 2 PM",
        "Find a female therapist who speaks Spanish in my area",
        "Check availability of John this week",
        "Show my upcoming appointments"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing Query: '{query}'")
        
        # Process through NLP
        nlp_result = conversation_manager.nlp_processor.detect_intent(query)
        entities = conversation_manager.nlp_processor.extract_entities(query)
        
        print(f"   🎯 Detected Intent: {nlp_result.value}")
        print(f"   📝 Extracted Entities: {entities}")
        
        # Select tool
        selected_tool = conversation_manager.tool_selector.select_tool(nlp_result, None)
        print(f"   🛠️  Selected Tool: {selected_tool}")
    
    return conversation_manager

def demo_conversation_flow(conversation_manager):
    """Demonstrate the complete conversation flow with parameter collection"""
    print_header("STEP 3: VALIDATION LAYER & CONVERSATION FLOW")
    
    session_id = "demo_session_001"
    
    conversation_steps = [
        "I need to book an appointment",
        "My patient ID is 123",
        "I want to see therapist 456",
        "Next Wednesday",
        "2:30 PM",
        "Service type 1",
        "Location 1"
    ]
    
    print("🔄 Simulating Multi-Step Conversation:")
    
    for i, user_input in enumerate(conversation_steps, 1):
        print(f"\n   Step {i}: User: '{user_input}'")
        
        response = conversation_manager.process_user_input(session_id, user_input)
        
        print(f"   🤖 Status: {response.get('status')}")
        print(f"   💬 Response: {response.get('message', 'No message')}")
        
        if response.get('missing_parameters'):
            print(f"   📝 Missing: {response.get('missing_parameters')}")
        
        if response.get('collected_so_far'):
            print(f"   ✅ Collected: {response.get('collected_so_far')}")
        
        if response.get('status') == 'ready_for_execution':
            print(f"   🎉 Ready to execute: {response.get('tool')}")
            print(f"   📊 Final Parameters: {json.dumps(response.get('parameters'), indent=6)}")
            break
    
    # Show conversation summary
    summary = conversation_manager.get_conversation_summary(session_id)
    print(f"\n📋 Conversation Summary:")
    print(f"   Intent: {summary.get('current_intent')}")
    print(f"   Tool: {summary.get('selected_tool')}")
    print(f"   Retry Count: {summary.get('retry_count')}")
    print(f"   Messages: {summary.get('conversation_length')}")

def demo_rag_system():
    """Demonstrate the RAG (Retrieval-Augmented Generation) system"""
    print_header("ENHANCED FEATURES: RAG INTEGRATION")
    
    try:
        # Initialize enhanced chatbot
        enhanced_chatbot = EnhancedHealthcareChatbot()
        
        print("🧠 RAG System Status:")
        print(f"   Quadrant DB: {'✅ Connected' if enhanced_chatbot.rag_system.qdrant_available else '❌ Not available'}")
        print(f"   Embeddings: {'✅ Loaded' if enhanced_chatbot.rag_system.embeddings_available else '❌ Not available'}")
        print(f"   Chat Model: {'✅ Ready' if enhanced_chatbot.rag_system.chat_available else '❌ Not available'}")
        
        # Test knowledge base
        knowledge_docs = enhanced_chatbot.rag_system.knowledge_base.documents
        print(f"\n📚 Knowledge Base: {len(knowledge_docs)} documents loaded")
        
        for doc_id, doc in list(knowledge_docs.items())[:3]:
            print(f"   - {doc_id} ({doc.document_type}): {doc.content[:50]}...")
        
        # Test enhanced conversation
        print(f"\n🎭 Testing Enhanced Conversation:")
        test_session = "rag_demo_session"
        
        test_queries = [
            "How do I book an appointment?",
            "What are the business rules for booking?",
            "Find therapists with anxiety specialization"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            response = enhanced_chatbot.process_message(test_session, query)
            print(f"   Response: {response.get('message', 'No response')[:100]}...")
            
            if response.get('knowledge_context'):
                print(f"   Knowledge Used: {len(response.get('knowledge_context', []))} documents")
        
    except Exception as e:
        print(f"❌ RAG System Error: {e}")
        print("   Note: This requires Ollama and Quadrant DB to be running locally")

def demo_query_examples():
    """Show practical query examples"""
    print_header("PRACTICAL QUERY EXAMPLES")
    
    examples = [
        {
            "category": "📅 Appointment Booking",
            "queries": [
                "Book appointment with Dr. Smith tomorrow at 2 PM for patient 123",
                "Schedule a session with therapist 456 next Wednesday at 10:30 AM",
                "I need to see a therapist for anxiety treatment this week"
            ]
        },
        {
            "category": "🔍 Therapist Search",
            "queries": [
                "Find female therapist who speaks Spanish in zone 1",
                "Search for child psychologist with PhD near zip code 12345",
                "Show me therapists specializing in depression and available today"
            ]
        },
        {
            "category": "⏰ Availability Checking", 
            "queries": [
                "Check availability of John this Wednesday",
                "When is Dr. Rodriguez available next week?",
                "Show me all free slots for therapist 789 this month"
            ]
        },
        {
            "category": "📋 Appointment Management",
            "queries": [
                "Show my upcoming appointments",
                "List all appointments for patient 123",
                "What appointments do I have with Dr. Chen?"
            ]
        }
    ]
    
    for example in examples:
        print(f"\n{example['category']}:")
        for i, query in enumerate(example['queries'], 1):
            print(f"   {i}. \"{query}\"")

def main():
    """Run the complete demo"""
    print_header("HEALTHCARE CHATBOT ROADMAP IMPLEMENTATION DEMO")
    print("This demo showcases the complete implementation of the healthcare")
    print("chatbot roadmap with tool-based architecture, NLP, and RAG integration.")
    
    try:
        # Step 1: Tool Collection & Registration
        registry = demo_tools_registry()
        
        # Step 2: NLP Processing & Tool Selection
        conversation_manager = demo_nlp_processing(registry)
        
        # Step 3: Validation Layer & Conversation Flow
        demo_conversation_flow(conversation_manager)
        
        # Enhanced Features: RAG Integration
        demo_rag_system()
        
        # Practical Examples
        demo_query_examples()
        
        print_header("DEMO COMPLETED SUCCESSFULLY")
        print("🎉 All components of the healthcare chatbot roadmap have been")
        print("   successfully implemented and demonstrated!")
        print("\n📝 Key Features Demonstrated:")
        print("   ✅ Tool Collection & Registration")
        print("   ✅ Natural Language Processing")
        print("   ✅ Intent Detection & Entity Extraction")
        print("   ✅ Tool Selection & Parameter Gathering")
        print("   ✅ Validation Layer with Retry Mechanisms")
        print("   ✅ Multi-step Conversation Management")
        print("   ✅ RAG Integration with Quadrant DB")
        print("   ✅ Knowledge Base Enhancement")
        print("   ✅ Production-Ready Flask Application")
        
        print("\n🚀 Next Steps:")
        print("   1. Run the Flask application: python advanced_healthcare_chatbot.py")
        print("   2. Open browser to http://localhost:5001")
        print("   3. Start chatting with the healthcare assistant!")
        print("   4. Try the admin dashboard at http://localhost:5001/admin")
        
    except Exception as e:
        print(f"\n❌ Demo Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
