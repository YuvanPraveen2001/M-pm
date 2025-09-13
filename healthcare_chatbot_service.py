"""
Healthcare Chatbot Service
Contains the main conversation management and response generation classes
"""

import json
import re
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from ai_chatbot_tools import HealthcareToolsRegistry, ToolType
from natural_language_processor import HealthcareQueryProcessor
from healthcare_database_manager_sqlserver import HealthcareDatabaseManager
from healthcare_schema_rag import get_healthcare_schema_rag
from enhanced_schema_rag import get_enhanced_schema_rag
from dynamic_schema_manager import get_dynamic_schema_manager
from availability_query_generator import get_availability_query_generator
from enhanced_availability_query_processor import get_availability_query_processor
# Import working availability query function
from generate_availability_query import get_availability_query_for_employee, generate_employee_availability_sql

# WebSocket for real-time chain of thoughts
try:
    from websocket_chain_of_thoughts import get_chain_of_thoughts_ws
    WEBSOCKET_AVAILABLE = True
except ImportError:
    print("⚠️ WebSocket chain of thoughts not available")
    get_chain_of_thoughts_ws = None
    WEBSOCKET_AVAILABLE = False


class BookingStep(Enum):
    """Enumeration of booking steps"""
    INITIAL = "initial"
    PATIENT_SEARCH = "patient_search"
    PATIENT_CONFIRMATION = "patient_confirmation"
    EMPLOYEE_SEARCH = "employee_search"
    EMPLOYEE_SELECTION = "employee_selection"
    AUTH_VERIFICATION = "auth_verification"
    AUTH_DETAIL_SELECTION = "auth_detail_selection"
    LOCATION_SELECTION = "location_selection"
    DATETIME_SELECTION = "datetime_selection"
    FINAL_CONFIRMATION = "final_confirmation"
    COMPLETED = "completed"


@dataclass
class ChatResponse:
    """Response from the healthcare chatbot"""
    message: str
    status: str = "success"
    intent: str = "general"
    confidence: float = 0.5
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    entities: Optional[Dict[str, Any]] = None
    suggested_actions: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)  # Alias for suggested_actions
    booking_step: Optional[BookingStep] = None
    chain_of_thoughts: List[str] = field(default_factory=list)
    websocket_session_id: Optional[str] = None  # For real-time chain of thoughts
    processing_time_ms: Optional[int] = None
    confidence_score: Optional[float] = None
    query_executed: Optional[str] = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        """Ensure suggested_actions and suggestions are synchronized"""
        if self.suggested_actions and not self.suggestions:
            self.suggestions = self.suggested_actions
        elif self.suggestions and not self.suggested_actions:
            self.suggested_actions = self.suggestions


@dataclass
class BookingContext:
    """Context for booking flow management"""
    step: BookingStep = BookingStep.INITIAL
    selected_patient: Optional[Dict] = None
    selected_employee: Optional[Dict] = None
    final_employee: Optional[Dict] = None
    selected_auth: Optional[Dict] = None
    selected_auth_detail: Optional[Dict] = None
    selected_location: Optional[Dict] = None
    appointment_datetime: Optional[str] = None
    duration_minutes: int = 60
    notes: str = ""
    search_criteria: Dict[str, Any] = field(default_factory=dict)


class HealthcareConversationManager:
    """Manages conversation state and booking context"""
    
    def __init__(self):
        self.context = {}
        self.booking_context = BookingContext()
        self.conversation_history = []
        
    def update_context(self, key: str, value: Any):
        """Update conversation context"""
        self.context[key] = value
        
    def get_context(self, key: str, default=None):
        """Get value from conversation context"""
        return self.context.get(key, default)
    
    def get_booking_context(self) -> BookingContext:
        """Get current booking context"""
        return self.booking_context
    
    def add_to_history(self, role: str, message: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            'role': role,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def reset_booking_context(self):
        """Reset booking context for new booking"""
        self.booking_context = BookingContext()


class HealthcareResponseGenerator:
    """Generates intelligent responses for healthcare conversations"""
    
    def __init__(self, db_manager: HealthcareDatabaseManager):
        self.db_manager = db_manager
        self.query_processor = HealthcareQueryProcessor(db_manager)
        self.tool_registry = HealthcareToolsRegistry()
        
        # Initialize Dynamic Schema Manager (primary system)
        print("🔄 DEBUG: Initializing dynamic schema management system...")
        self.dynamic_schema = get_dynamic_schema_manager(db_manager)
        print("✅ DEBUG: Dynamic schema management system ready")
        
        # Initialize Enhanced RAG system as backup
        print("🔍 DEBUG: Initializing enhanced healthcare schema RAG system...")
        self.schema_rag = get_enhanced_schema_rag(db_manager)
        print("✅ DEBUG: Enhanced healthcare schema RAG system ready")
        
        # Keep the old schema RAG as fallback
        self.fallback_schema_rag = get_healthcare_schema_rag()
        
        # WebSocket for real-time chain of thoughts
        self.websocket_cot = get_chain_of_thoughts_ws() if WEBSOCKET_AVAILABLE else None
        if self.websocket_cot:
            print("✅ Real-time chain of thoughts WebSocket ready")
        else:
            print("⚠️ Chain of thoughts will be provided in response only")
        
        # Setup enhanced logging
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('healthcare_chatbot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('HealthcareChatbot')
        
        # Intent patterns
        self.intent_patterns = {
            'check_availability': [
                r'check.*availabilit',
                r'is.*available',
                r'free.*time',
                r'when.*available',
                r'schedule.*for',
                r'get.*availability',
                r'show.*availability',
                r'availability.*of',
                r'find.*availability'
            ],
            'book_appointment': [
                r'book.*appointment',
                r'schedule.*appointment',
                r'make.*appointment',
                r'reserve.*time',
                r'set.*appointment'
            ],
            'find_provider': [
                r'find.*therapist',
                r'find.*doctor',
                r'show.*therapist',
                r'list.*provider',
                r'who.*specializes'
            ],
            'get_appointments': [
                r'my.*appointment',
                r'show.*appointment',
                r'list.*appointment',
                r'upcoming.*appointment'
            ],
            'cancel_appointment': [
                r'cancel.*appointment',
                r'remove.*appointment',
                r'delete.*appointment'
            ]
        }
    
    def emit_thought(self, thought: str, session_id: str = None):
        """Emit a chain of thought with detailed logging"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_thought = f"[{timestamp}] {thought}"
        
        # Log to console for debugging
        print(f"💭 {formatted_thought}")
        
        # Log to file for persistence
        self.logger.info(f"[ChainOfThought] {formatted_thought}")
        
        # Emit to WebSocket if available
        if self.websocket_cot and session_id:
            try:
                self.websocket_cot.emit_thought(session_id, formatted_thought)
            except Exception as e:
                print(f"⚠️ WebSocket emit failed: {e}")
        
        return formatted_thought
    
    def log_query(self, query: str, query_type: str = "SQL", session_id: str = None, metadata: dict = None):
        """Log generated queries for debugging and monitoring"""
        # Create a detailed log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "query_type": query_type,
            "query": query,
            "query_length": len(query),
            "complexity": "complex" if len(query.split()) > 20 else "simple",
            "metadata": metadata or {}
        }
        
        # Log to console with formatting
        print(f"\n🔍 GENERATED QUERY [{query_type}]:")
        print(f"📅 Time: {log_entry['timestamp']}")
        print(f"🆔 Session: {session_id or 'N/A'}")
        print(f"📊 Complexity: {log_entry['complexity']}")
        print(f"📝 Query:\n{query}")
        print("─" * 80)
        
        # Log to file for persistence
        self.logger.info(f"[GeneratedQuery] {json.dumps(log_entry, indent=2)}")
        
        # Emit to WebSocket for live monitoring
        if self.websocket_cot and session_id:
            try:
                self.websocket_cot.emit_query_generated(session_id, query, query_type)
            except Exception as e:
                print(f"⚠️ WebSocket query log failed: {e}")
        
        return log_entry

    def generate_response(self, user_message: str, conversation_manager: HealthcareConversationManager) -> ChatResponse:
        """Generate intelligent response to user message"""
        start_time = time.time()
        chain_of_thoughts = []
        websocket_session_id = None
        
        try:
            self.emit_thought(f"🔍 Processing user message: '{user_message[:50]}...'", websocket_session_id)
            
            # Create WebSocket session for real-time chain of thoughts
            if self.websocket_cot and not websocket_session_id:
                websocket_session_id = self.websocket_cot.create_session()
                self.emit_thought(f"💭 Created WebSocket session: {websocket_session_id}", websocket_session_id)
            
            # Add user message to history
            self.emit_thought("� Adding message to conversation history", websocket_session_id)
            conversation_manager.add_to_history('user', user_message)
            
            # Step 1: Analyze intent
            self.emit_thought("🤖 Analyzing user intent and extracting entities", websocket_session_id)
            if self.websocket_cot and websocket_session_id:
                self.websocket_cot.emit_query_analysis(websocket_session_id, user_message, "analyzing", [])
            
            intent = self._analyze_intent(user_message)
            self.emit_thought(f"� Detected intent: '{intent}'", websocket_session_id)
            chain_of_thoughts.append(f"Analyzed user query and detected intent: {intent}")
            
            # Step 2: Extract entities
            self.emit_thought("🔍 Extracting entities from user message", websocket_session_id)
            entities = self._extract_entities(user_message)
            self.emit_thought(f"� Extracted entities: {entities}", websocket_session_id)
            chain_of_thoughts.append(f"Extracted entities from query: {entities}")
            
            if self.websocket_cot and websocket_session_id:
                self.websocket_cot.emit_query_analysis(websocket_session_id, user_message, intent, entities)
            
            # Step 3: Get booking context
            self.emit_thought("� Retrieving current booking context", websocket_session_id)
            booking_context = conversation_manager.get_booking_context()
            self.emit_thought(f"� Current booking step: {booking_context.step.value}", websocket_session_id)
            chain_of_thoughts.append(f"Retrieved booking context, current step: {booking_context.step.value}")
            
            # Generate response based on intent and context
            if intent == 'book_appointment':
                self.emit_thought("� Processing appointment booking request", websocket_session_id)
                if self.websocket_cot and websocket_session_id:
                    self.websocket_cot.emit_tool_selection(websocket_session_id, "booking_workflow", "User wants to book an appointment")
                response = self._handle_booking_flow(user_message, entities, booking_context, chain_of_thoughts, websocket_session_id)
            elif intent == 'check_availability':
                self.emit_thought("🔍 Processing availability check request", websocket_session_id)
                if self.websocket_cot and websocket_session_id:
                    self.websocket_cot.emit_tool_selection(websocket_session_id, "availability_check", "User wants to check provider availability")
                response = self._handle_availability_check(user_message, entities, websocket_session_id, chain_of_thoughts)
            elif intent == 'find_provider':
                self.emit_thought("�‍⚕️ Processing provider search request", websocket_session_id)
                if self.websocket_cot and websocket_session_id:
                    self.websocket_cot.emit_tool_selection(websocket_session_id, "provider_search", "User wants to find healthcare providers")
                response = self._handle_provider_search(user_message, entities, chain_of_thoughts, websocket_session_id)
            elif intent == 'get_appointments':
                self.emit_thought("� Processing appointment query request", websocket_session_id)
                if self.websocket_cot and websocket_session_id:
                    self.websocket_cot.emit_tool_selection(websocket_session_id, "appointment_query", "User wants to retrieve appointment information")
                response = self._handle_appointment_query(user_message, entities, chain_of_thoughts, websocket_session_id)
            else:
                self.emit_thought("� Processing as general healthcare query", websocket_session_id)
                if self.websocket_cot and websocket_session_id:
                    self.websocket_cot.emit_tool_selection(websocket_session_id, "natural_language_processing", "Processing general query with NLP")
                # Try natural language query processing
                response = self._handle_general_query(user_message, websocket_session_id)
            
            print(f"🔍 DEBUG: Generated response intent: {response.intent}")
            print(f"🔍 DEBUG: Response message length: {len(response.message)} chars")
            
            # Add response to history
            print("🔍 DEBUG: Adding response to conversation history...")
            conversation_manager.add_to_history('assistant', response.message)
            
            print("🔍 DEBUG: Response generation completed successfully")
            
            # Calculate processing time and emit completion
            processing_time_ms = int((time.time() - start_time) * 1000)
            chain_of_thoughts.append(f"Response generated successfully in {processing_time_ms}ms")
            
            if self.websocket_cot and websocket_session_id:
                self.websocket_cot.emit_completion(websocket_session_id, len(chain_of_thoughts), processing_time_ms)
            
            # Add WebSocket information to response
            response.chain_of_thoughts = chain_of_thoughts
            response.websocket_session_id = websocket_session_id
            response.processing_time_ms = processing_time_ms
            
            return response
            
        except Exception as e:
            print(f"❌ ERROR in generate_response: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Emit error to WebSocket
            if self.websocket_cot and websocket_session_id:
                self.websocket_cot.emit_error(websocket_session_id, type(e).__name__, str(e), "Response Generation")
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            chain_of_thoughts.append(f"Error occurred: {str(e)}")
            
            return ChatResponse(
                message=f"I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.",
                status="error",
                chain_of_thoughts=chain_of_thoughts,
                websocket_session_id=websocket_session_id,
                processing_time_ms=processing_time_ms
            )
    
    def _analyze_intent(self, message: str) -> str:
        """Analyze message intent"""
        message_lower = message.lower()
        
        # Debug output
        print(f"🔍 DEBUG: Analyzing intent for: '{message}'")
        print(f"🔍 DEBUG: Lowercase: '{message_lower}'")
        
        for intent, patterns in self.intent_patterns.items():
            print(f"🔍 DEBUG: Checking {intent}:")
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    print(f"🔍 DEBUG: ✅ MATCHED {intent} with pattern: {pattern}")
                    return intent
                else:
                    print(f"🔍 DEBUG: ❌ No match: {pattern}")
        
        print(f"🔍 DEBUG: No patterns matched, returning 'general_query'")
        return 'general_query'
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from message"""
        entities = {}
        
        # Extract names (simple pattern)
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        names = re.findall(name_pattern, message)
        if names:
            entities['names'] = names
        
        # Extract dates
        date_patterns = [
            r'\b(today|tomorrow|yesterday)\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b',
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, message.lower())
            if matches:
                entities['date_references'] = matches
        
        # Extract times
        time_pattern = r'\b(\d{1,2}:\d{2}(?:\s*[ap]m)?|\d{1,2}\s*[ap]m)\b'
        times = re.findall(time_pattern, message.lower())
        if times:
            entities['times'] = times
        
        return entities
    
    def _handle_booking_flow(self, message: str, entities: Dict, booking_context: BookingContext) -> ChatResponse:
        """Handle multi-step booking flow"""
        
        if booking_context.step == BookingStep.INITIAL:
            # Start patient search
            self.emit_thought("🔍 Starting patient search for booking flow", booking_context.websocket_session_id)
            if 'names' in entities and entities['names']:
                patient_name = entities['names'][0]
                self.emit_thought(f"🏥 Searching for patient: {patient_name}", booking_context.websocket_session_id)
                patients = self.db_manager.search_patient_by_name(patient_name)
                
                # Log the patient search query
                self.log_query(f"Patient search for: {patient_name}", "PATIENT_SEARCH", booking_context.websocket_session_id, {"patient_name": patient_name})
                
                if patients:
                    if len(patients) == 1:
                        booking_context.selected_patient = patients[0]
                        booking_context.step = BookingStep.EMPLOYEE_SEARCH
                        self.emit_thought(f"✅ Found unique patient: {patients[0]['PatientName']}", booking_context.websocket_session_id)
                        return ChatResponse(
                            message=f"Great! I found patient {patients[0]['PatientName']}. Who would you like to book an appointment with?",
                            intent="book_appointment",
                            booking_step=BookingStep.EMPLOYEE_SEARCH,
                            suggestions=["Search for a therapist", "Find available providers"]
                        )
                    else:
                        booking_context.step = BookingStep.PATIENT_CONFIRMATION
                        self.emit_thought(f"👥 Found {len(patients)} patients with similar names", booking_context.websocket_session_id)
                        return ChatResponse(
                            message=f"I found {len(patients)} patients with that name. Please select one:",
                            intent="book_appointment",
                            booking_step=BookingStep.PATIENT_CONFIRMATION,
                            data={'patients': patients[:5]},  # Limit to 5 for UI
                            metadata={'requires_action': True, 'action_type': "select_patient"}
                        )
                else:
                    self.emit_thought(f"❌ No patients found for: {patient_name}", booking_context.websocket_session_id)
                    return ChatResponse(
                        message=f"I couldn't find any patients named '{patient_name}'. Please check the spelling or try a different name.",
                        intent="book_appointment",
                        suggestions=["Try a different name", "Search by last name only"]
                    )
            else:
                self.emit_thought("📝 Requesting patient name for booking", booking_context.websocket_session_id)
                return ChatResponse(
                    message="To book an appointment, I'll need the patient's name. What's the patient's name?",
                    intent="book_appointment",
                    booking_step=BookingStep.PATIENT_SEARCH,
                    suggestions=["John Smith", "Sarah Johnson"]
                )
        
        elif booking_context.step == BookingStep.EMPLOYEE_SEARCH:
            # Handle employee search
            self.emit_thought("👨‍⚕️ Starting employee/provider search", booking_context.websocket_session_id)
            if 'names' in entities and entities['names']:
                employee_name = entities['names'][0]
                self.emit_thought(f"🔍 Searching for employee: {employee_name}", booking_context.websocket_session_id)
                employees = self.db_manager.search_employee_by_name(employee_name)
                
                # Log the employee search query
                self.log_query(f"Employee search for: {employee_name}", "EMPLOYEE_SEARCH", booking_context.websocket_session_id, {"employee_name": employee_name})
                
                if employees:
                    booking_context.selected_employee = employees[0]
                    booking_context.step = BookingStep.AUTH_VERIFICATION
                    self.emit_thought(f"✅ Found employee: {employees[0]['EmployeeName']}", booking_context.websocket_session_id)
                    return ChatResponse(
                        message=f"Found {employees[0]['EmployeeName']}. Let me check the patient's authorizations...",
                        intent="book_appointment",
                        booking_step=BookingStep.AUTH_VERIFICATION
                    )
                else:
                    self.emit_thought(f"❌ No employees found for: {employee_name}", booking_context.websocket_session_id)
                    return ChatResponse(
                        message=f"I couldn't find any employees named '{employee_name}'. Would you like me to suggest available providers?",
                        intent="book_appointment",
                        suggestions=["Show available therapists", "Find providers by specialty"]
                    )
            else:
                self.emit_thought("📝 Requesting provider name for booking", booking_context.websocket_session_id)
                return ChatResponse(
                    message="Which provider would you like to book with? You can give me their name.",
                    intent="book_appointment",
                    booking_step=BookingStep.EMPLOYEE_SEARCH,
                    suggestions=["Dr. Smith", "Sarah Thompson"]
                )
        
        # Continue with other booking steps...
        self.emit_thought(f"🔄 Continuing booking flow for step: {booking_context.step}", booking_context.websocket_session_id)
        return ChatResponse(
            message="Booking flow continues... (this would be implemented for all steps)",
            intent="book_appointment",
            booking_step=booking_context.step
        )
    
    def _extract_employee_name_from_query(self, message: str, entities: Dict) -> Optional[str]:
        """Extract employee name from user query"""
        import re
        
        # First check if entities contain employee name
        if entities and 'employee_name' in entities:
            return entities['employee_name']
        
        # Look for common patterns in the message
        message_lower = message.lower()
        
        # Pattern 1: "availability of [name]"
        pattern1 = re.search(r'availability\s+of\s+([a-zA-Z\s]+)', message_lower)
        if pattern1:
            return pattern1.group(1).strip()
        
        # Pattern 2: "get me the availability of [name]"
        pattern2 = re.search(r'get.*availability.*of\s+([a-zA-Z\s]+)', message_lower)
        if pattern2:
            return pattern2.group(1).strip()
        
        # Pattern 3: "show [name] availability"
        pattern3 = re.search(r'show\s+([a-zA-Z\s]+)\s+availability', message_lower)
        if pattern3:
            return pattern3.group(1).strip()
        
        # Pattern 4: "when is [name] available"
        pattern4 = re.search(r'when\s+is\s+([a-zA-Z\s]+)\s+available', message_lower)
        if pattern4:
            return pattern4.group(1).strip()
        
        # Pattern 5: "[name] schedule"
        pattern5 = re.search(r'([a-zA-Z\s]+)\s+schedule', message_lower)
        if pattern5:
            name = pattern5.group(1).strip()
            # Avoid common words
            if name not in ['work', 'my', 'the', 'employee', 'staff', 'doctor']:
                return name
        
        # Pattern 6: Look for names after common keywords
        keywords = ['for', 'of', 'with']
        for keyword in keywords:
            pattern = rf'{keyword}\s+([a-zA-Z\s]+)'
            match = re.search(pattern, message_lower)
            if match:
                potential_name = match.group(1).strip()
                # Check if it looks like a name (2-3 words, proper case)
                words = potential_name.split()
                if 1 <= len(words) <= 3 and all(word.isalpha() for word in words):
                    return potential_name
        
        return None
    
    def _handle_availability_check(self, message: str, entities: Dict, websocket_session_id: Optional[str] = None, chain_of_thoughts: Optional[List[str]] = None) -> ChatResponse:
        """Handle availability checking with enhanced query generation and full chain of thoughts"""
        if chain_of_thoughts is None:
            chain_of_thoughts = []
            
        try:
            # Extract employee name from message or entities
            self.emit_thought("🧠 Extracting employee name from query", websocket_session_id)
            employee_name = self._extract_employee_name_from_query(message, entities)
            
            if not employee_name:
                return ChatResponse(
                    message="I'd be happy to help you check employee availability! Could you please specify which employee you're looking for? For example: 'get me the availability of Jon Snow' or 'show availability for Dr. Smith'",
                    status="need_employee_name",
                    intent="availability_clarification",
                    entities={'query': message},
                    suggested_actions=["Try: 'availability of [employee name]'", "Try: 'show schedule for [employee name]'"],
                    chain_of_thoughts=chain_of_thoughts,
                    websocket_session_id=websocket_session_id
                )
            
            self.emit_thought(f"🔍 Looking up availability for: {employee_name}", websocket_session_id)
            chain_of_thoughts.append(f"Searching for employee: {employee_name}")
            
            if self.websocket_cot and websocket_session_id:
                self.websocket_cot.emit_tool_selection(websocket_session_id, "availability_query_generator", f"Generating availability query for {employee_name}")
            
            # Use the working availability query function
            self.emit_thought("🔍 Generating SQL query for availability check", websocket_session_id)
            sql_query, table_info = get_availability_query_for_employee(employee_name)
            chain_of_thoughts.append(f"Generated SQL query for {employee_name}")
            
            # Execute the query
            self.emit_thought("⚡ Executing availability query against database", websocket_session_id)
            start_time = time.time()
            
            try:
                results = self.db_manager.execute_query(sql_query)
                execution_time = time.time() - start_time
                
                # Create result object similar to enhanced processor
                class QueryResult:
                    def __init__(self, success, results, sql_query, execution_time, chain_of_thoughts):
                        self.success = success
                        self.results = results
                        self.sql_query = sql_query
                        self.execution_time = execution_time
                        self.chain_of_thoughts = chain_of_thoughts
                        self.confidence_score = 0.9 if results else 0.7
                        self.error_message = None
                        self.schema_analysis = table_info
                
                result = QueryResult(True, results, sql_query, execution_time, chain_of_thoughts)
                
            except Exception as query_error:
                execution_time = time.time() - start_time
                error_msg = str(query_error)
                self.emit_thought(f"❌ Query execution failed: {error_msg}", websocket_session_id)
                
                class QueryResult:
                    def __init__(self, success, error_message, sql_query, execution_time, chain_of_thoughts):
                        self.success = success
                        self.results = []
                        self.sql_query = sql_query
                        self.execution_time = execution_time
                        self.chain_of_thoughts = chain_of_thoughts
                        self.confidence_score = 0.0
                        self.error_message = error_message
                        self.schema_analysis = {}
                
                result = QueryResult(False, error_msg, sql_query, execution_time, chain_of_thoughts)
            
            # Merge chain of thoughts
            chain_of_thoughts.extend(result.chain_of_thoughts)
            
            # Emit thoughts to WebSocket if available
            if self.websocket_cot and websocket_session_id:
                for thought in result.chain_of_thoughts:
                    self.websocket_cot.emit_thought(websocket_session_id, thought)
            
            if result.success:
                self.emit_thought(f"✅ Query executed successfully. Found {len(result.results)} results.", websocket_session_id)
                
                # Format the results for display
                if result.results:
                    formatted_message = self._format_availability_results(message, result.results, result.sql_query)
                    suggestions = self._generate_availability_suggestions(result.results)
                    
                    return ChatResponse(
                        message=formatted_message,
                        status="success",
                        intent="availability_results",
                        confidence=result.confidence_score,
                        entities={'employee_name': employee_name, 'results_count': len(result.results)},
                        data={
                            'query_results': result.results,
                            'sql_query': result.sql_query,
                            'schema_analysis': result.schema_analysis,
                            'execution_time': result.execution_time
                        },
                        suggested_actions=suggestions,
                        chain_of_thoughts=chain_of_thoughts,
                        websocket_session_id=websocket_session_id,
                        query_executed=result.sql_query,
                        execution_time=result.execution_time
                    )
                else:
                    return ChatResponse(
                        message=f"I found the relevant information in our database, but no availability matches your query. The query was executed successfully against the employee schedules.",
                        status="no_results",
                        intent="no_availability_results",
                        entities={'employee_name': employee_name, 'results_count': 0},
                        data={'sql_query': result.sql_query, 'execution_time': result.execution_time},
                        suggested_actions=["Try a different name", "Check different day", "Show all available staff"],
                        chain_of_thoughts=chain_of_thoughts,
                        websocket_session_id=websocket_session_id
                    )
            else:
                self.emit_thought(f"❌ Query processing failed: {result.error_message}", websocket_session_id)
                
                return ChatResponse(
                    message=f"I understand you're looking for availability information. I've analyzed the request and generated the appropriate query, but encountered an issue during execution: {result.error_message}. Please try rephrasing your request or contact support.",
                    status="error",
                    intent="availability_error",
                    entities={'employee_name': employee_name, 'error': result.error_message},
                    data={'error': result.error_message, 'execution_time': result.execution_time},
                    suggested_actions=["Try different wording", "Check database connection", "Contact support"],
                    chain_of_thoughts=chain_of_thoughts,
                    websocket_session_id=websocket_session_id
                )
                
        except Exception as e:
            error_msg = str(e)
            self.emit_thought(f"❌ Error in enhanced availability processing: {error_msg}", websocket_session_id)
            chain_of_thoughts.append(f"Error in enhanced availability processing: {error_msg}")
            
            # Fallback to advanced availability query if enhanced fails
            self.emit_thought("🔄 Falling back to advanced availability query processor", websocket_session_id)
            return self._handle_advanced_availability_query(message, entities, websocket_session_id, chain_of_thoughts)
    
    def _handle_advanced_availability_query(self, message: str, entities: Dict, websocket_session_id: Optional[str] = None, chain_of_thoughts: Optional[List[str]] = None) -> ChatResponse:
        """Handle advanced availability queries like 'list of available employees' with metadata filters"""
        if chain_of_thoughts is None:
            chain_of_thoughts = []
            
        try:
            # Initialize availability query generator
            self.emit_thought("🛠️ Initializing specialized availability query generator", websocket_session_id)
            availability_generator = get_availability_query_generator()
            chain_of_thoughts.append("Initialized specialized availability query generator")
            
            if self.websocket_cot and websocket_session_id:
                self.websocket_cot.emit_tool_selection(websocket_session_id, "advanced_sql_generation", "Generating advanced SQL for employee availability")
            
            # Parse metadata from the message (this would be enhanced with better NLP)
            self.emit_thought("🔍 Extracting metadata filters from user request", websocket_session_id)
            metadata = self._extract_availability_metadata(message, entities)
            self.emit_thought(f"📊 Extracted metadata: {metadata}", websocket_session_id)
            chain_of_thoughts.append(f"Extracted metadata: {metadata}")
            
            # Generate specialized query
            self.emit_thought("⚙️ Generating specialized SQL query for availability", websocket_session_id)
            sql_query = availability_generator.generate_availability_query(
                query_text=message,
                metadata=metadata
            )
            
            # Log the generated query
            self.log_query(sql_query, "AVAILABILITY_SQL", websocket_session_id, metadata)
            self.emit_thought("✅ Successfully generated specialized SQL query", websocket_session_id)
            chain_of_thoughts.append(f"Generated specialized SQL query")
            
            if self.websocket_cot and websocket_session_id:
                self.websocket_cot.emit_database_query(websocket_session_id, "executing")
            
            # Execute the query
            self.emit_thought("🗄️ Executing query against database", websocket_session_id)
            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(sql_query)
                    results = []
                    
                    # Get column names
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Fetch results
                    for row in cursor.fetchall():
                        row_dict = {}
                        for i, value in enumerate(row):
                            row_dict[columns[i]] = value
                        results.append(row_dict)
                    
                    self.emit_thought(f"✅ Query executed successfully, found {len(results)} results", websocket_session_id)
                    chain_of_thoughts.append(f"Query executed successfully, found {len(results)} results")
                    
                    if self.websocket_cot and websocket_session_id:
                        self.websocket_cot.emit_database_query(websocket_session_id, "completed", len(results))
                    
                    if results:
                        # Format results for availability display
                        self.emit_thought("📋 Formatting results for display", websocket_session_id)
                        formatted_message = self._format_availability_list_results(results, metadata)
                        
                        if self.websocket_cot and websocket_session_id:
                            self.websocket_cot.emit_response_generation(websocket_session_id, "availability_list_response", 0.95)
                        
                        return ChatResponse(
                            message=formatted_message,
                            status="success",
                            data={
                                'employees': results,
                                'metadata': metadata,
                                'sql_query': sql_query
                            },
                            suggested_actions=[
                                "Book with available employee",
                                "Check specific availability",
                                "Filter by different criteria"
                            ],
                            chain_of_thoughts=chain_of_thoughts,
                            query_executed=sql_query
                        )
                    else:
                        self.emit_thought("⚠️ No results found for the specified criteria", websocket_session_id)
                        return ChatResponse(
                            message=f"I couldn't find any employees available with the specified criteria. Please try different filters or check a different date.",
                            status="no_results",
                            data={'metadata': metadata, 'sql_query': sql_query},
                            suggested_actions=[
                                "Try different date",
                                "Remove some filters",
                                "Check all employees"
                            ],
                            chain_of_thoughts=chain_of_thoughts,
                            query_executed=sql_query
                        )
                        
            except Exception as db_error:
                chain_of_thoughts.append(f"Database error: {str(db_error)}")
                
                if self.websocket_cot and websocket_session_id:
                    self.websocket_cot.emit_error(websocket_session_id, "DatabaseError", str(db_error), "Query Execution")
                
                return ChatResponse(
                    message=f"I encountered a database error while searching for available employees. Please try again or contact support. Error: {str(db_error)}",
                    status="database_error",
                    data={'error': str(db_error), 'sql_query': sql_query},
                    suggested_actions=[
                        "Try again",
                        "Contact support",
                        "Use simpler query"
                    ],
                    chain_of_thoughts=chain_of_thoughts
                )
                
        except Exception as e:
            chain_of_thoughts.append(f"Error in advanced availability query: {str(e)}")
            
            if self.websocket_cot and websocket_session_id:
                self.websocket_cot.emit_error(websocket_session_id, type(e).__name__, str(e), "Advanced Query Processing")
            
            return ChatResponse(
                message=f"I encountered an error while processing your availability request. Please try a simpler query or contact support.",
                status="error",
                data={'error': str(e)},
                suggested_actions=[
                    "Try simpler query",
                    "Contact support",
                    "Check individual availability"
                ],
                chain_of_thoughts=chain_of_thoughts
            )
    
    def _handle_provider_search(self, message: str, entities: Dict) -> ChatResponse:
        """Handle provider search requests"""
        # Extract specialties or other criteria from the message
        specialties = self._extract_specialties(message)
        
        if specialties:
            # Search for providers with those specialties
            results = []  # This would be implemented with actual database search
            
            return ChatResponse(
                message=f"Here are therapists specializing in {', '.join(specialties)}:\n\n• Dr. Sarah Johnson - Anxiety & Depression Specialist\n• Mark Wilson, LCSW - Trauma Therapy\n• Lisa Chen, PhD - Cognitive Behavioral Therapy",
                intent="find_provider",
                entities={'specialties': specialties},
                suggestions=["Book with Dr. Johnson", "See more specialists", "Check availability"]
            )
        
        return ChatResponse(
            message="I can help you find therapists. What type of therapy or specialty are you looking for?",
            intent="find_provider",
            suggestions=["Anxiety therapy", "Depression counseling", "Family therapy"]
        )
    
    def _handle_appointment_query(self, message: str, entities: Dict) -> ChatResponse:
        """Handle appointment queries"""
        # This would implement actual appointment retrieval
        return ChatResponse(
            message="Here are your upcoming appointments:\n\n• Tomorrow, 2:00 PM - Dr. Sarah Johnson (Therapy)\n• Friday, 10:00 AM - Mark Wilson (Follow-up)",
            intent="get_appointments",
            suggestions=["Reschedule appointment", "Cancel appointment", "Book new appointment"]
        )
    
    def _handle_general_query(self, message: str, websocket_session_id: Optional[str] = None) -> ChatResponse:
        """Handle general queries using RAG-enhanced schema retrieval and SQL generation"""
        try:
            print(f"🔍 DEBUG: Processing general query with Dynamic Schema Manager: '{message}'")
            
            # Step 1: Check for schema changes and update if needed
            print("🔄 DEBUG: Checking for database schema changes...")
            self.emit_thought("🔄 Checking for database schema updates", websocket_session_id)
            
            update_info = self.dynamic_schema.check_for_schema_changes()
            if update_info.tables_updated:
                print(f"🔄 Schema changes detected: {len(update_info.tables_updated)} tables updated")
                self.emit_thought(f"📊 Schema updated: {len(update_info.tables_updated)} tables refreshed", websocket_session_id)
            
            # Step 2: Get relevant schema using dynamic manager
            print("🔍 DEBUG: Retrieving relevant schema using Dynamic Schema Manager...")
            self.emit_thought("🗄️ Retrieving current database schema with exact column names", websocket_session_id)
            
            schema_result = self.dynamic_schema.get_schema_for_query(message)
            
            print(f"🔍 DEBUG: Found {len(schema_result['tables'])} relevant tables:")
            for table in schema_result['tables']:
                print(f"  - {table['table_name']}: {len(table['columns'])} columns")
                column_names = [col['name'] for col in table['columns'][:5]]
                print(f"    Columns: {', '.join(column_names)}{'...' if len(table['columns']) > 5 else ''}")
            print(f"🔍 DEBUG: Schema confidence: {schema_result['confidence_score']:.2f} ({schema_result['search_method']})")
            
            # Step 3: Generate SQL using dynamic schema manager
            print("🔍 DEBUG: Generating SQL with current schema...")
            self.emit_thought("⚙️ Generating SQL query with real-time schema validation", websocket_session_id)
            
            sql_query = self.dynamic_schema.generate_sql_with_current_schema(message, schema_result['tables'])
            print(f"🔍 DEBUG: Generated SQL with dynamic schema:\n{sql_query}")
            
            # Log the generated query
            self.log_query(sql_query, "Dynamic_Schema_SQL", websocket_session_id, {
                "user_query": message,
                "tables_used": [t['table_name'] for t in schema_result['tables']],
                "confidence": schema_result['confidence_score'],
                "search_method": schema_result['search_method'],
                "schema_updated": len(update_info.tables_updated) > 0
            })
            
            # Step 4: Execute the SQL query
            try:
                print("🔍 DEBUG: Executing SQL query with validated schema...")
                self.emit_thought("🔄 Executing database query with verified column names", websocket_session_id)
                
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(sql_query)
                    results = []
                    
                    # Get column names
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Fetch results
                    for row in cursor.fetchall():
                        row_dict = {}
                        for i, value in enumerate(row):
                            row_dict[columns[i]] = value
                        results.append(row_dict)
                    
                    print(f"✅ DEBUG: Query executed successfully, {len(results)} results found")
                    
                    if results:
                        # Format results for display
                        formatted_message = self._format_rag_query_results(message, results, schema_result)
                        
                        return ChatResponse(
                            message=formatted_message,
                            intent="rag_query_results",
                            entities={
                                'query_results': results,
                                'sql_query': sql_query,
                                'schema_tables': [t["table_name"] for t in schema_result["tables"]],
                                'confidence_score': schema_result["confidence_score"]
                            },
                            suggestions=self._generate_contextual_suggestions(message, results)
                        )
                    else:
                        return ChatResponse(
                            message=f"I found the relevant information in our database, but no results matched your query. The query searched through {', '.join([t['table_name'] for t in schema_result['tables']])} tables.",
                            intent="no_results",
                            entities={'sql_query': sql_query, 'schema_tables': [t["table_name"] for t in schema_result["tables"]]},
                            suggestions=["Try a different search", "Check spelling", "Use different keywords"]
                        )
                        
            except Exception as db_error:
                print(f"⚠️ DEBUG: Database execution failed: {str(db_error)}")
                
                # Provide helpful response even without database execution
                return ChatResponse(
                    message=f"I understand you're looking for information about {self._extract_query_intent(message)}. I've identified the relevant database tables ({', '.join([t['table_name'] for t in schema_result['tables']])}) and generated the appropriate query, but I'm currently unable to connect to the database to get the results. Please check your database connection.",
                    intent="database_unavailable",
                    entities={
                        'sql_query': sql_query,
                        'schema_tables': [t["table_name"] for t in schema_result["tables"]],
                        'confidence_score': schema_result["confidence_score"],
                        'error': str(db_error)
                    },
                    suggestions=["Check database connection", "Try again later", "Contact system administrator"]
                )
                
        except Exception as e:
            print(f"❌ DEBUG: Error in RAG general query processing: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback to original query processor
            try:
                print("🔍 DEBUG: Falling back to original query processor...")
                result = self.query_processor.process_query(message)
                
                if result['success']:
                    formatted_message = self._format_query_results(result)
                    
                    return ChatResponse(
                        message=formatted_message,
                        intent="fallback_query_results",
                        entities={'query_results': result['results']},
                        suggestions=["Book an appointment", "Check availability", "Find more providers"]
                    )
                else:
                    return ChatResponse(
                        message=result.get('message', 'I couldn\'t process that query. Could you please rephrase?'),
                        intent="general",
                        suggestions=result.get('suggestions', [
                            "Check availability",
                            "Book an appointment", 
                            "Find a therapist"
                        ])
                    )
                    
            except:
                return ChatResponse(
                    message="I'm having trouble processing that request. Could you please try asking in a different way?",
                    intent="error",
                    suggestions=["Check availability", "Book appointment", "Find therapist"]
                )
    
    def _extract_availability_metadata(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Extract metadata for availability queries"""
        metadata = {}
        message_lower = message.lower()
        
        # Extract gender filter
        if 'male' in message_lower and 'female' not in message_lower:
            metadata['gender'] = 'Male'
        elif 'female' in message_lower and 'male' not in message_lower:
            metadata['gender'] = 'Female'
        
        # Extract site/location filter
        site_patterns = [r'site\s*(\d+)', r'location\s*(\d+)', r'siteid\s*(\d+)']
        for pattern in site_patterns:
            match = re.search(pattern, message_lower)
            if match:
                metadata['site_id'] = int(match.group(1))
                break
        
        # Extract date filter (look for Wednesday, specific dates, etc.)
        date_patterns = [
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message_lower)
            if match:
                metadata['target_date'] = match.group(1)
                break
        
        # Extract role/position filter
        role_keywords = ['therapist', 'doctor', 'nurse', 'specialist', 'counselor']
        for keyword in role_keywords:
            if keyword in message_lower:
                metadata['role'] = keyword.title()
                break
        
        # Extract specialty filter
        specialty_keywords = ['physical therapy', 'mental health', 'occupational therapy', 'speech therapy']
        for specialty in specialty_keywords:
            if specialty in message_lower:
                metadata['specialty'] = specialty
                break
        
        return metadata
    
    def _format_availability_list_results(self, results: List[Dict], metadata: Dict) -> str:
        """Format availability list results for display"""
        if not results:
            return "No employees found matching your criteria."
        
        # Build header based on metadata
        filter_desc = []
        if metadata.get('gender'):
            filter_desc.append(f"Gender: {metadata['gender']}")
        if metadata.get('site_id'):
            filter_desc.append(f"Site: {metadata['site_id']}")
        if metadata.get('target_date'):
            filter_desc.append(f"Date: {metadata['target_date']}")
        if metadata.get('role'):
            filter_desc.append(f"Role: {metadata['role']}")
        if metadata.get('specialty'):
            filter_desc.append(f"Specialty: {metadata['specialty']}")
        
        header = "Available Employees"
        if filter_desc:
            header += f" ({', '.join(filter_desc)})"
        header += f" - {len(results)} found:\n\n"
        
        formatted = header
        
        for i, employee in enumerate(results[:10], 1):  # Limit to 10 results
            name = employee.get('EmployeeName') or f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
            title = employee.get('Title') or employee.get('job_title', 'Employee')
            site = employee.get('SiteId') or employee.get('site_id', 'N/A')
            gender = employee.get('Gender') or 'N/A'
            
            formatted += f"{i}. {name}\n"
            formatted += f"   Title: {title}\n"
            formatted += f"   Site: {site}\n"
            formatted += f"   Gender: {gender}\n"
            
            # Add availability info if present
            if 'available_slots' in employee:
                formatted += f"   Available Slots: {employee['available_slots']}\n"
            elif 'next_available' in employee:
                formatted += f"   Next Available: {employee['next_available']}\n"
            
            formatted += "\n"
        
        if len(results) > 10:
            formatted += f"... and {len(results) - 10} more employees. Use filters to narrow down the results.\n"
        
        return formatted

    def _parse_date_reference(self, date_refs: List[str]) -> Optional[str]:
        """Parse date references into actual dates"""
        if not date_refs:
            return None
        
        today = datetime.now().date()
        
        for ref in date_refs:
            ref_lower = ref.lower()
            if 'today' in ref_lower:
                return today.strftime('%Y-%m-%d')
            elif 'tomorrow' in ref_lower:
                return (today + timedelta(days=1)).strftime('%Y-%m-%d')
            elif 'wednesday' in ref_lower:
                # Find next Wednesday
                days_ahead = 2 - today.weekday()  # Wednesday is 2
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            # Add more date parsing logic as needed
        
        return None
    
    def _extract_specialties(self, message: str) -> List[str]:
        """Extract therapy specialties from message"""
        specialties = []
        specialty_keywords = {
            'anxiety': ['anxiety', 'anxious', 'worry', 'panic'],
            'depression': ['depression', 'depressed', 'sad', 'mood'],
            'trauma': ['trauma', 'ptsd', 'abuse'],
            'family': ['family', 'couples', 'marriage', 'relationship'],
            'addiction': ['addiction', 'substance', 'alcohol', 'drug']
        }
        
        message_lower = message.lower()
        for specialty, keywords in specialty_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                specialties.append(specialty)
        
        return specialties
    
    def _format_query_results(self, result: Dict) -> str:
        """Format query results for chat display"""
        if not result.get('results'):
            return result.get('message', 'No results found.')
        
        results = result['results']
        
        if len(results) == 1:
            # Single result
            item = results[0]
            if 'EmployeeName' in item:
                return f"I found: {item['EmployeeName']}"
            elif 'PatientName' in item:
                return f"Patient: {item['PatientName']}"
            else:
                return f"Found: {str(item)}"
        else:
            # Multiple results - format as list
            formatted = "Here's what I found:\n\n"
            for i, item in enumerate(results[:5], 1):  # Limit to 5 results
                if 'EmployeeName' in item:
                    formatted += f"{i}. {item['EmployeeName']}\n"
                elif 'PatientName' in item:
                    formatted += f"{i}. {item['PatientName']}\n"
                else:
                    formatted += f"{i}. {str(item)}\n"
            
            if len(results) > 5:
                formatted += f"\n... and {len(results) - 5} more results"
            
            return formatted

    def _format_rag_query_results(self, original_query: str, results: list, schema_result) -> str:
        """Format RAG query results with context"""
        try:
            intent = self._extract_query_intent(original_query)
            result_count = len(results)
            
            if "availability" in intent.lower() or "available" in original_query.lower():
                return self._format_availability_results(results, original_query)
            elif "appointment" in intent.lower() or "book" in original_query.lower():
                return self._format_appointment_results(results, original_query)
            elif "therapist" in intent.lower() or "provider" in original_query.lower():
                return self._format_provider_results(results, original_query)
            else:
                # Generic formatting with schema context
                table_names = [t["name"] for t in schema_result["tables"]]
                
                if result_count == 0:
                    return f"I searched through {', '.join(table_names)} but couldn't find any results for '{original_query}'."
                elif result_count == 1:
                    return f"I found 1 result for '{original_query}' in our {', '.join(table_names)} database:\n\n{self._format_single_result(results[0])}"
                else:
                    return f"I found {result_count} results for '{original_query}' in our {', '.join(table_names)} database:\n\n{self._format_multiple_results(results[:5])}"  # Limit to 5 results
                    
        except Exception as e:
            print(f"⚠️ DEBUG: Error formatting RAG results: {str(e)}")
            return f"I found {len(results)} results for your query."

    def _format_availability_results(self, query: str, results: list, sql_query: str = None) -> str:
        """Format availability-specific results with enhanced schema-aware formatting"""
        if not results:
            return f"I analyzed your query '{query}' and searched the employee schedules, but couldn't find any matching availability information. Please try specifying a different date, time, or provider name."
        
        # Determine the day mapping for display
        day_mapping = {
            1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday',
            5: 'Thursday', 6: 'Friday', 7: 'Saturday'
        }
        
        formatted = f"Here's the availability information for your query '{query}':\n\n"
        
        for i, result in enumerate(results[:5]):  # Limit to 5 results
            try:
                # Extract employee information
                employee_name = result.get('EmployeeName', 'Unknown Employee')
                employee_id = result.get('EmployeeID', 'N/A')
                
                # Extract schedule information
                week_day = result.get('WeekDay')  # Updated column name
                day_name = day_mapping.get(week_day, f'Day {week_day}') if week_day else 'Unknown Day'
                
                available_from = result.get('AvailableFrom', 'N/A')  # Updated column name
                available_to = result.get('AvailableTo', 'N/A')  # Updated column name
                availability_status_id = result.get('AvailabilityStatusId', 0)  # Updated column name
                
                # Format the time display
                time_display = f"{available_from} - {available_to}" if available_from != 'N/A' and available_to != 'N/A' else 'Time not specified'
                
                # Create the formatted entry
                formatted += f"🩺 **{employee_name}** (ID: {employee_id})\n"
                formatted += f"   📅 {day_name}: {time_display}\n"
                formatted += f"   ✅ Status: {'Available' if availability_status_id == 1 else 'Not Available'}\n"
                
                if i < len(results) - 1 and i < 4:  # Add separator if not last item
                    formatted += "\n"
                    
            except Exception as e:
                # Fallback for unexpected result structure
                formatted += f"• {str(result)}\n"
        
        # Add summary information
        if len(results) > 5:
            formatted += f"\n... and {len(results) - 5} more results available.\n"
        
        formatted += f"\n📊 Total matches found: {len(results)}"
        
        if sql_query:
            formatted += f"\n\n🔍 Query executed successfully against the employee schedules database."
        
        return formatted

    def _format_appointment_results(self, results: list, query: str) -> str:
        """Format appointment-specific results"""
        if not results:
            return "I couldn't find any appointment information. Would you like to book a new appointment?"
        
        formatted = "Here are the appointment details I found:\n\n"
        for result in results[:3]:
            appointment_id = result.get('appointment_id', 'N/A')
            provider = result.get('provider_name') or f"{result.get('first_name', '')} {result.get('last_name', '')}".strip()
            date = result.get('appointment_date', 'Date not specified')
            time = result.get('appointment_time', 'Time not specified')
            status = result.get('status', 'Status unknown')
            
            formatted += f"• Appointment #{appointment_id}\n"
            formatted += f"  Provider: {provider}\n"
            formatted += f"  Date/Time: {date} at {time}\n"
            formatted += f"  Status: {status}\n\n"
        
        return formatted

    def _format_provider_results(self, results: list, query: str) -> str:
        """Format provider-specific results"""
        if not results:
            return "I couldn't find any providers matching your criteria. Please try different search terms."
        
        formatted = "Here are the providers I found:\n\n"
        for result in results[:5]:
            name = result.get('provider_name') or f"{result.get('first_name', '')} {result.get('last_name', '')}".strip()
            specialty = result.get('specialty') or result.get('specialization', 'General')
            phone = result.get('phone') or result.get('contact_phone', 'Phone not available')
            email = result.get('email') or result.get('contact_email', 'Email not available')
            
            formatted += f"• {name}\n"
            formatted += f"  Specialty: {specialty}\n"
            formatted += f"  Phone: {phone}\n"
            formatted += f"  Email: {email}\n\n"
        
        return formatted

    def _format_single_result(self, result: dict) -> str:
        """Format a single result nicely"""
        formatted = ""
        for key, value in result.items():
            if value is not None:
                key_display = key.replace('_', ' ').title()
                formatted += f"{key_display}: {value}\n"
        return formatted

    def _format_multiple_results(self, results: list) -> str:
        """Format multiple results in a compact way"""
        formatted = ""
        for i, result in enumerate(results, 1):
            formatted += f"{i}. "
            # Show most relevant fields first
            if 'provider_name' in result or 'first_name' in result:
                name = result.get('provider_name') or f"{result.get('first_name', '')} {result.get('last_name', '')}".strip()
                formatted += name
            
            if 'appointment_date' in result:
                formatted += f" - {result['appointment_date']}"
            if 'appointment_time' in result:
                formatted += f" at {result['appointment_time']}"
            if 'specialty' in result:
                formatted += f" ({result['specialty']})"
            
            formatted += "\n"
        
        return formatted

    def _extract_query_intent(self, query: str) -> str:
        """Extract the main intent from a query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['available', 'availability', 'free', 'open']):
            return "availability check"
        elif any(word in query_lower for word in ['book', 'schedule', 'appointment']):
            return "appointment booking"
        elif any(word in query_lower for word in ['therapist', 'provider', 'doctor', 'specialist']):
            return "provider search"
        elif any(word in query_lower for word in ['cancel', 'reschedule', 'change']):
            return "appointment modification"
        else:
            return "general information"

    def _generate_availability_suggestions(self, results: list) -> list:
        """Generate contextual suggestions based on availability results"""
        suggestions = []
        
        if not results:
            suggestions = [
                "Try a different name",
                "Check another day", 
                "Show all available staff",
                "Search by specialty"
            ]
        else:
            # Extract unique employee names for suggestions
            employee_names = set()
            days_mentioned = set()
            
            for result in results[:3]:  # Check first few results
                if 'EmployeeName' in result:
                    employee_names.add(result['EmployeeName'])
                if 'WeekDay' in result:  # Updated column name
                    day_mapping = {
                        1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday',
                        5: 'Thursday', 6: 'Friday', 7: 'Saturday'
                    }
                    day_name = day_mapping.get(result['WeekDay'])  # Updated column name
                    if day_name:
                        days_mentioned.add(day_name)
            
            # Generate suggestions based on available employees
            if employee_names:
                first_employee = list(employee_names)[0]
                suggestions.append(f"Book with {first_employee}")
                if len(employee_names) > 1:
                    suggestions.append("Compare all providers")
            
            # Generate suggestions based on days
            if days_mentioned:
                suggestions.append("Check other days")
            
            # General availability suggestions
            suggestions.extend([
                "Show full schedules",
                "Filter by time",
                "Find specialists"
            ])
        
        return suggestions[:4]  # Limit to 4 suggestions

    def _generate_contextual_suggestions(self, query: str, results: list) -> list:
        """Generate contextual suggestions based on query and results"""
        intent = self._extract_query_intent(query)
        suggestions = []
        
        if intent == "availability check":
            suggestions = ["Book this appointment", "Check other times", "Find different provider"]
        elif intent == "appointment booking":
            suggestions = ["Confirm appointment", "Check availability", "Find provider info"]
        elif intent == "provider search":
            suggestions = ["Check availability", "Book appointment", "Get contact info"]
        elif intent == "appointment modification":
            suggestions = ["Reschedule appointment", "Cancel appointment", "Contact provider"]
        else:
            suggestions = ["Book appointment", "Check availability", "Find provider"]
        
        # Add result-specific suggestions
        if results and len(results) > 5:
            suggestions.insert(0, "Show more results")
        
        return suggestions

    def _create_fallback_response(self, error_msg: str) -> ChatResponse:
        """Create a fallback response when all retries fail"""
        if "42S02" in error_msg or "Invalid object name" in error_msg:
            return ChatResponse(
                message="I'm having trouble accessing some database tables. This might be a temporary issue. Please try again in a moment, or I can help you with general information about our services.",
                intent="database_error",
                suggestions=[
                    "Try again later", 
                    "Ask about our services", 
                    "Contact support",
                    "Book appointment manually"
                ]
            )
        elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            return ChatResponse(
                message="I'm experiencing connection issues with our database. Please try your request again, or I can provide general assistance.",
                intent="connection_error", 
                suggestions=[
                    "Try again", 
                    "Check your connection", 
                    "Contact support",
                    "Ask general questions"
                ]
            )
        else:
            return ChatResponse(
                message="I encountered an unexpected issue while processing your request. Our technical team has been notified. Please try again or contact support.",
                intent="general_error",
                suggestions=[
                    "Try rephrasing", 
                    "Contact support", 
                    "Try again later",
                    "Ask different question"
                ]
            )