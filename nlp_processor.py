"""
Natural Language Processing and Tool Selection System
Implements Steps 2-3 of the healthcare chatbot roadmap:
- Prompting for Tool Selection & Parameter Gathering
- Validation Layer with retry mechanisms
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum

from ai_chatbot_tools import (
    HealthcareToolsRegistry, ParameterValidator, ToolDefinition, 
    ParameterDefinition, ToolType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Intent(Enum):
    """User intent classification"""
    BOOK_APPOINTMENT = "book_appointment"
    CHECK_AVAILABILITY = "check_availability"
    FIND_THERAPIST = "find_therapist"
    SUGGEST_THERAPIST = "suggest_therapist"
    VIEW_APPOINTMENTS = "view_appointments"
    CANCEL_APPOINTMENT = "cancel_appointment"
    MODIFY_APPOINTMENT = "modify_appointment"
    GENERAL_INQUIRY = "general_inquiry"
    UNKNOWN = "unknown"


@dataclass
class ConversationContext:
    """Maintains conversation state and context"""
    session_id: str
    current_intent: Optional[Intent] = None
    selected_tool: Optional[str] = None
    collected_parameters: Dict[str, Any] = None
    missing_parameters: List[str] = None
    retry_count: int = 0
    conversation_history: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.collected_parameters is None:
            self.collected_parameters = {}
        if self.missing_parameters is None:
            self.missing_parameters = []
        if self.conversation_history is None:
            self.conversation_history = []


class HealthcareNLPProcessor:
    """
    Natural Language Processing system for healthcare chatbot
    Handles intent detection, entity extraction, and tool selection
    """
    
    def __init__(self, tools_registry: HealthcareToolsRegistry):
        self.tools_registry = tools_registry
        self.intent_patterns = self._build_intent_patterns()
        self.entity_patterns = self._build_entity_patterns()
    
    def _build_intent_patterns(self) -> Dict[Intent, List[str]]:
        """Build regex patterns for intent detection"""
        return {
            Intent.BOOK_APPOINTMENT: [
                r'book.*appointment',
                r'schedule.*appointment',
                r'make.*appointment',
                r'set.*up.*meeting',
                r'i.*need.*to.*see',
                r'want.*to.*book',
                r'can.*i.*schedule'
            ],
            Intent.CHECK_AVAILABILITY: [
                r'check.*availability',
                r'when.*is.*available',
                r'what.*times.*available',
                r'free.*slots',
                r'available.*times',
                r'when.*can.*i.*see',
                r'availability.*of'
            ],
            Intent.FIND_THERAPIST: [
                r'find.*therapist',
                r'search.*for.*therapist',
                r'looking.*for.*therapist',
                r'need.*therapist',
                r'find.*employee',
                r'search.*employee',
                r'therapist.*in.*area',
                r'therapist.*near.*me'
            ],
            Intent.SUGGEST_THERAPIST: [
                r'suggest.*therapist',
                r'recommend.*therapist',
                r'best.*therapist',
                r'suitable.*therapist',
                r'who.*should.*i.*see',
                r'which.*therapist'
            ],
            Intent.VIEW_APPOINTMENTS: [
                r'my.*appointments',
                r'view.*appointments',
                r'show.*appointments',
                r'list.*appointments',
                r'appointment.*history',
                r'upcoming.*appointments'
            ]
        }
    
    def _build_entity_patterns(self) -> Dict[str, str]:
        """Build regex patterns for entity extraction"""
        return {
            'date': r'(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|tomorrow|today|next week|this week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            'time': r'(\d{1,2}:\d{2}(?:\s*(?:am|pm))?|\d{1,2}\s*(?:am|pm))',
            'name': r'(?:therapist|doctor|dr\.?)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',
            'gender': r'\b(male|female|man|woman|guy|lady)\b',
            'language': r'\b(english|spanish|french|mandarin|cantonese|hindi|arabic)\b',
            'zone': r'\b(zone\s*\d+|area\s*\d+|district\s*\d+)\b',
            'zip_code': r'\b(\d{5}(?:-\d{4})?)\b',
            'specialty': r'\b(anxiety|depression|trauma|ptsd|addiction|family|couples?|child|cognitive|behavioral|cbt)\b',
            'patient_id': r'\bpatient\s*(?:id|#)?\s*(\d+)\b',
            'employee_id': r'\b(?:therapist|employee|doctor)\s*(?:id|#)?\s*(\d+)\b'
        }
    
    def detect_intent(self, user_input: str) -> Intent:
        """Detect user intent from natural language input"""
        user_input_lower = user_input.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input_lower, re.IGNORECASE):
                    logger.info(f"Detected intent: {intent.value} for input: {user_input}")
                    return intent
        
        logger.info(f"Could not detect intent for input: {user_input}")
        return Intent.UNKNOWN
    
    def extract_entities(self, user_input: str) -> Dict[str, Any]:
        """Extract entities from user input"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            if matches:
                if entity_type in ['date', 'time', 'name']:
                    entities[entity_type] = matches[0] if isinstance(matches[0], str) else matches[0]
                else:
                    entities[entity_type] = matches
        
        # Process and normalize entities
        entities = self._normalize_entities(entities)
        
        logger.info(f"Extracted entities: {entities}")
        return entities
    
    def _normalize_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize extracted entities to standard formats"""
        normalized = {}
        
        for key, value in entities.items():
            if key == 'date':
                normalized[key] = self._normalize_date(value)
            elif key == 'time':
                normalized[key] = self._normalize_time(value)
            elif key == 'gender':
                normalized[key] = self._normalize_gender(value)
            elif key == 'language':
                normalized[key] = self._normalize_language(value)
            else:
                normalized[key] = value
        
        return normalized
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format"""
        date_str = date_str.lower().strip()
        today = date.today()
        
        if date_str == 'today':
            return today.isoformat()
        elif date_str == 'tomorrow':
            return (today + timedelta(days=1)).isoformat()
        elif date_str == 'next week':
            return (today + timedelta(days=7)).isoformat()
        elif date_str in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            return self._get_next_weekday(date_str)
        else:
            # Try to parse various date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date()
                    return parsed_date.isoformat()
                except ValueError:
                    continue
        
        return date_str  # Return original if can't parse
    
    def _normalize_time(self, time_str: str) -> str:
        """Normalize time to HH:MM format"""
        time_str = time_str.lower().strip()
        
        # Handle AM/PM format
        if 'am' in time_str or 'pm' in time_str:
            try:
                if ':' in time_str:
                    parsed_time = datetime.strptime(time_str, '%I:%M %p').time()
                else:
                    parsed_time = datetime.strptime(time_str, '%I %p').time()
                return parsed_time.strftime('%H:%M')
            except ValueError:
                pass
        
        # Handle 24-hour format
        if ':' in time_str:
            return time_str
        
        return time_str  # Return original if can't parse
    
    def _normalize_gender(self, gender_value: Any) -> str:
        """Normalize gender to standard values"""
        if isinstance(gender_value, list):
            gender_str = gender_value[0].lower()
        else:
            gender_str = str(gender_value).lower()
        
        if gender_str in ['male', 'man', 'guy']:
            return 'Male'
        elif gender_str in ['female', 'woman', 'lady']:
            return 'Female'
        return gender_str.title()
    
    def _normalize_language(self, language_value: Any) -> str:
        """Normalize language to standard values"""
        if isinstance(language_value, list):
            return language_value[0].title()
        return str(language_value).title()
    
    def _get_next_weekday(self, weekday_name: str) -> str:
        """Get the date of the next occurrence of a weekday"""
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        today = date.today()
        target_weekday = weekdays[weekday_name.lower()]
        days_ahead = target_weekday - today.weekday()
        
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        target_date = today + timedelta(days=days_ahead)
        return target_date.isoformat()


class ToolSelector:
    """
    Selects appropriate tools based on user intent and context
    Implements Step 2: Tool Selection & Parameter Gathering
    """
    
    def __init__(self, tools_registry: HealthcareToolsRegistry):
        self.tools_registry = tools_registry
        self.intent_to_tool_mapping = {
            Intent.BOOK_APPOINTMENT: ["book_appointment", "validate_patient", "validate_therapist", "check_availability"],
            Intent.CHECK_AVAILABILITY: ["check_availability"],
            Intent.FIND_THERAPIST: ["find_employees_by_criteria"],
            Intent.SUGGEST_THERAPIST: ["suggest_suitable_therapists"],
            Intent.VIEW_APPOINTMENTS: ["get_patient_appointments", "validate_patient"]
        }
    
    def select_tool(self, intent: Intent, context: ConversationContext) -> Optional[str]:
        """Select the primary tool based on intent"""
        if intent in self.intent_to_tool_mapping:
            primary_tools = self.intent_to_tool_mapping[intent]
            if primary_tools:
                selected_tool = primary_tools[0]  # Select the primary tool
                logger.info(f"Selected tool '{selected_tool}' for intent '{intent.value}'")
                return selected_tool
        
        logger.warning(f"No tool found for intent: {intent.value}")
        return None
    
    def get_required_dependencies(self, tool_name: str) -> List[str]:
        """Get required dependencies for a tool"""
        tool = self.tools_registry.get_tool(tool_name)
        if tool and tool.dependencies:
            return tool.dependencies
        return []


class ConversationManager:
    """
    Manages conversation flow, parameter gathering, and validation
    Implements Steps 2-3: Parameter Gathering and Validation Layer
    """
    
    def __init__(self, tools_registry: HealthcareToolsRegistry):
        self.tools_registry = tools_registry
        self.nlp_processor = HealthcareNLPProcessor(tools_registry)
        self.tool_selector = ToolSelector(tools_registry)
        self.parameter_validator = ParameterValidator()
        self.active_contexts: Dict[str, ConversationContext] = {}
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Main method to process user input and manage conversation flow"""
        # Get or create conversation context
        context = self.active_contexts.get(session_id)
        if not context:
            context = ConversationContext(session_id=session_id)
            self.active_contexts[session_id] = context
        
        # Add user input to conversation history
        context.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        response = self._process_conversation_step(context, user_input)
        
        # Add assistant response to conversation history
        context.conversation_history.append({
            "role": "assistant",
            "content": response.get("message", ""),
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def _process_conversation_step(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        """Process a single conversation step"""
        
        # If we're in the middle of collecting parameters, continue with that
        if context.selected_tool and context.missing_parameters:
            return self._collect_missing_parameters(context, user_input)
        
        # Detect intent and extract entities
        intent = self.nlp_processor.detect_intent(user_input)
        entities = self.nlp_processor.extract_entities(user_input)
        
        # Update context with new intent
        context.current_intent = intent
        
        # Select appropriate tool
        selected_tool = self.tool_selector.select_tool(intent, context)
        if not selected_tool:
            return {
                "status": "error",
                "message": "I'm sorry, I couldn't understand what you're trying to do. Could you please rephrase your request?",
                "suggestions": [
                    "Book an appointment",
                    "Check therapist availability", 
                    "Find a therapist",
                    "View my appointments"
                ]
            }
        
        context.selected_tool = selected_tool
        
        # Get tool definition and map entities to parameters
        tool_def = self.tools_registry.get_tool(selected_tool)
        if not tool_def:
            return {"status": "error", "message": "Selected tool not found in registry"}
        
        # Map extracted entities to tool parameters
        mapped_parameters = self._map_entities_to_parameters(entities, tool_def)
        context.collected_parameters.update(mapped_parameters)
        
        # Check if we have all required parameters
        missing_params = self._get_missing_parameters(context.collected_parameters, tool_def)
        context.missing_parameters = missing_params
        
        if missing_params:
            return self._request_missing_parameters(context, tool_def, missing_params)
        else:
            # All parameters collected, validate and execute
            return self._validate_and_execute_tool(context, tool_def)
    
    def _collect_missing_parameters(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        """Collect missing parameters from user input"""
        entities = self.nlp_processor.extract_entities(user_input)
        tool_def = self.tools_registry.get_tool(context.selected_tool)
        
        if not tool_def:
            return {"status": "error", "message": "Tool definition not found"}
        
        # Map entities to parameters
        mapped_parameters = self._map_entities_to_parameters(entities, tool_def)
        context.collected_parameters.update(mapped_parameters)
        
        # Check for missing parameters again
        missing_params = self._get_missing_parameters(context.collected_parameters, tool_def)
        context.missing_parameters = missing_params
        
        if missing_params:
            # Still missing parameters, ask for them
            return self._request_missing_parameters(context, tool_def, missing_params)
        else:
            # All parameters collected, validate and execute
            return self._validate_and_execute_tool(context, tool_def)
    
    def _map_entities_to_parameters(self, entities: Dict[str, Any], tool_def: ToolDefinition) -> Dict[str, Any]:
        """Map extracted entities to tool parameters"""
        mapped = {}
        
        # Create a mapping of entity types to parameter names
        entity_to_param_mapping = {
            'date': ['appointment_date', 'start_date', 'availability_date'],
            'time': ['appointment_time', 'time_from'],
            'gender': ['gender', 'preferred_gender'],
            'patient_id': ['patient_id'],
            'employee_id': ['employee_id'],
            'language': ['language_preference', 'language_id'],
            'zone': ['zone_id'],
            'zip_code': ['zip_code'],
            'specialty': ['specialization', 'treatment_type']
        }
        
        # Map entities to parameters
        for entity_type, entity_value in entities.items():
            if entity_type in entity_to_param_mapping:
                possible_params = entity_to_param_mapping[entity_type]
                for param_name in possible_params:
                    # Check if this parameter exists in the tool definition
                    param_exists = any(p.name == param_name for p in tool_def.parameters)
                    if param_exists and param_name not in mapped:
                        mapped[param_name] = entity_value
                        break
        
        logger.info(f"Mapped entities to parameters: {mapped}")
        return mapped
    
    def _get_missing_parameters(self, collected_params: Dict[str, Any], tool_def: ToolDefinition) -> List[str]:
        """Get list of missing required parameters"""
        missing = []
        
        for param_def in tool_def.parameters:
            if param_def.required and param_def.name not in collected_params:
                missing.append(param_def.name)
        
        return missing
    
    def _request_missing_parameters(self, context: ConversationContext, tool_def: ToolDefinition, missing_params: List[str]) -> Dict[str, Any]:
        """Request missing parameters from the user"""
        param_questions = {
            'patient_id': "What is your patient ID?",
            'employee_id': "Which therapist would you like to see? (Please provide the therapist ID or name)",
            'appointment_date': "What date would you prefer for your appointment? (Please use YYYY-MM-DD format)",
            'appointment_time': "What time would you prefer? (Please use HH:MM format)",
            'service_type_id': "What type of service do you need? (1: Individual Therapy, 2: Group Therapy, 3: Assessment)",
            'location_id': "Which location would you prefer? (Please provide location ID)",
            'zone_id': "Which zone/area are you looking for?",
            'gender': "Do you have a gender preference for your therapist?",
            'treatment_type_id': "What type of treatment are you looking for?",
            'start_date': "What is the start date for availability check?",
            'language_preference': "Do you have a language preference?"
        }
        
        # Ask for the first missing parameter
        first_missing = missing_params[0]
        question = param_questions.get(first_missing, f"Please provide {first_missing.replace('_', ' ')}")
        
        # Get parameter definition for additional context
        param_def = next((p for p in tool_def.parameters if p.name == first_missing), None)
        if param_def and param_def.description:
            question += f" ({param_def.description})"
        
        return {
            "status": "collecting_parameters",
            "message": question,
            "missing_parameters": missing_params,
            "tool": context.selected_tool,
            "collected_so_far": context.collected_parameters
        }
    
    def _validate_and_execute_tool(self, context: ConversationContext, tool_def: ToolDefinition) -> Dict[str, Any]:
        """Validate parameters and prepare for tool execution"""
        
        # Validate all parameters
        is_valid, validation_errors = self.parameter_validator.validate_parameters(
            context.collected_parameters, tool_def
        )
        
        if not is_valid:
            context.retry_count += 1
            if context.retry_count >= 3:
                # Reset context after too many retries
                self._reset_context(context)
                return {
                    "status": "error",
                    "message": "I'm having trouble understanding your request. Let's start over. How can I help you today?",
                    "errors": validation_errors
                }
            
            # Return validation errors and ask for correction
            error_message = "I found some issues with the information provided:\n"
            error_message += "\n".join(f"- {error}" for error in validation_errors)
            error_message += "\n\nPlease correct these issues."
            
            return {
                "status": "validation_error",
                "message": error_message,
                "errors": validation_errors,
                "retry_count": context.retry_count
            }
        
        # Validation passed, ready for execution
        return {
            "status": "ready_for_execution",
            "message": f"Great! I have all the information needed to {tool_def.description.lower()}. Let me process this for you.",
            "tool": context.selected_tool,
            "parameters": context.collected_parameters,
            "sql_template": tool_def.sql_template if tool_def.sql_template else None
        }
    
    def _reset_context(self, context: ConversationContext):
        """Reset conversation context"""
        context.current_intent = None
        context.selected_tool = None
        context.collected_parameters = {}
        context.missing_parameters = []
        context.retry_count = 0
    
    def get_conversation_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of the conversation"""
        context = self.active_contexts.get(session_id)
        if not context:
            return None
        
        return {
            "session_id": session_id,
            "current_intent": context.current_intent.value if context.current_intent else None,
            "selected_tool": context.selected_tool,
            "collected_parameters": context.collected_parameters,
            "missing_parameters": context.missing_parameters,
            "retry_count": context.retry_count,
            "conversation_length": len(context.conversation_history)
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize the system
    tools_registry = HealthcareToolsRegistry()
    conversation_manager = ConversationManager(tools_registry)
    
    # Test conversation flow
    session_id = "test_session_123"
    
    test_inputs = [
        "I want to book an appointment with Dr. Johnson next Wednesday at 2 PM",
        "My patient ID is 123",
        "I need service type 1",
        "Location ID 1 please"
    ]
    
    print("Testing conversation flow:")
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\nStep {i}: User: {user_input}")
        response = conversation_manager.process_user_input(session_id, user_input)
        print(f"Assistant: {response.get('message', 'No message')}")
        print(f"Status: {response.get('status', 'No status')}")
        
        if response.get('status') == 'ready_for_execution':
            print("Ready to execute tool with parameters:")
            print(json.dumps(response.get('parameters', {}), indent=2))
            break
