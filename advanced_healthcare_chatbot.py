"""
Advanced Healthcare Chatbot Application
Implements the complete roadmap with tool-based architecture,
natural language processing, and Quadrant DB RAG integration.
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
import logging
import sqlite3
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import our custom modules
from ai_chatbot_tools import HealthcareToolsRegistry, ParameterValidator
from nlp_processor import ConversationManager, Intent
from quadrant_rag_system import EnhancedHealthcareChatbot

# Database execution module
from healthcare_database_manager_sqlserver import HealthcareDatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('healthcare_chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='../templates')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Initialize the enhanced chatbot system
try:
    enhanced_chatbot = EnhancedHealthcareChatbot()
    database_manager = HealthcareDatabaseManager()
    logger.info("Healthcare chatbot system initialized successfully")
except Exception as e:
    logger.error(f"Error initializing chatbot system: {e}")
    enhanced_chatbot = None
    database_manager = None


class ToolExecutor:
    """
    Implements Step 4: Tool Execution Flow
    Handles database queries and endpoint execution
    """
    
    def __init__(self, db_manager: HealthcareDatabaseManager):
        self.db_manager = db_manager
        self.tools_registry = HealthcareToolsRegistry()
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with validated parameters"""
        try:
            tool_def = self.tools_registry.get_tool(tool_name)
            if not tool_def:
                return {
                    "status": "error",
                    "message": f"Tool '{tool_name}' not found",
                    "data": None
                }
            
            # Execute based on tool type
            if tool_def.tool_type.value == "database_query":
                return self._execute_database_tool(tool_def, parameters)
            elif tool_def.tool_type.value == "booking":
                return self._execute_booking_tool(tool_def, parameters)
            elif tool_def.tool_type.value == "availability":
                return self._execute_availability_tool(tool_def, parameters)
            elif tool_def.tool_type.value == "search":
                return self._execute_search_tool(tool_def, parameters)
            elif tool_def.tool_type.value == "validation":
                return self._execute_validation_tool(tool_def, parameters)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported tool type: {tool_def.tool_type.value}",
                    "data": None
                }
        
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "status": "error",
                "message": f"Tool execution failed: {str(e)}",
                "data": None
            }
    
    def _execute_database_tool(self, tool_def, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database query tools"""
        if not tool_def.sql_template:
            return {"status": "error", "message": "No SQL template defined for tool"}
        
        # Prepare SQL with parameters
        sql_query = tool_def.sql_template
        param_values = []
        
        # Extract parameter values in order
        for param_def in tool_def.parameters:
            value = parameters.get(param_def.name)
            if value is not None:
                param_values.append(value)
            elif not param_def.required:
                param_values.append(param_def.default_value)
            else:
                param_values.append(None)
        
        # Execute query
        results = self.db_manager.execute_query(sql_query, param_values)
        
        return {
            "status": "success",
            "message": f"Found {len(results)} results",
            "data": results,
            "sql_executed": sql_query
        }
    
    def _execute_booking_tool(self, tool_def, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute appointment booking"""
        try:
            # First validate dependencies
            validation_errors = []
            
            # Validate patient
            patient_validation = self.execute_tool("validate_patient", {"patient_id": parameters.get("patient_id")})
            if patient_validation.get("status") != "success" or not patient_validation.get("data"):
                validation_errors.append("Invalid patient ID")
            
            # Validate therapist
            therapist_validation = self.execute_tool("validate_therapist", {"employee_id": parameters.get("employee_id")})
            if therapist_validation.get("status") != "success" or not therapist_validation.get("data"):
                validation_errors.append("Invalid therapist ID")
            
            # Check availability
            availability_check = self.execute_tool("check_availability", {
                "employee_id": parameters.get("employee_id"),
                "start_date": parameters.get("appointment_date")
            })
            
            if validation_errors:
                return {
                    "status": "error",
                    "message": "Validation failed: " + ", ".join(validation_errors),
                    "data": None
                }
            
            # Create appointment
            booking_sql = """
            INSERT INTO Appointment (
                PatientId, EmployeeId, ScheduledDate, ScheduledMinutes,
                AppointmentStatusId, LocationId, ServiceTypeId, Notes,
                HasPayroll, HasBilling, IsBillable, IsInternalAppointment,
                IsNonPayable, GroupAppointment, CreateDate, CreatedBy
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, 0, 0, 1, 0, 0, 'N', GETDATE(), 1)
            """
            
            # Combine date and time
            appointment_datetime = f"{parameters.get('appointment_date')} {parameters.get('appointment_time')}"
            
            booking_params = [
                parameters.get("patient_id"),
                parameters.get("employee_id"),
                appointment_datetime,
                parameters.get("duration_minutes", 60),
                parameters.get("location_id"),
                parameters.get("service_type_id"),
                parameters.get("notes", "")
            ]
            
            booking_result = self.db_manager.execute_query(booking_sql, booking_params, fetch_results=False)
            
            if booking_result is not None:
                return {
                    "status": "success",
                    "message": "Appointment booked successfully!",
                    "data": {
                        "appointment_date": parameters.get("appointment_date"),
                        "appointment_time": parameters.get("appointment_time"),
                        "patient_id": parameters.get("patient_id"),
                        "employee_id": parameters.get("employee_id"),
                        "duration": parameters.get("duration_minutes", 60)
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to create appointment",
                    "data": None
                }
        
        except Exception as e:
            logger.error(f"Booking error: {e}")
            return {
                "status": "error",
                "message": f"Booking failed: {str(e)}",
                "data": None
            }
    
    def _execute_availability_tool(self, tool_def, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute availability checking"""
        return self._execute_database_tool(tool_def, parameters)
    
    def _execute_search_tool(self, tool_def, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute therapist search"""
        return self._execute_database_tool(tool_def, parameters)
    
    def _execute_validation_tool(self, tool_def, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation tools"""
        return self._execute_database_tool(tool_def, parameters)


# Initialize tool executor
if database_manager:
    tool_executor = ToolExecutor(database_manager)
else:
    tool_executor = None


@app.route('/')
def index():
    """Main chatbot interface"""
    return render_template('healthcare_chatbot.html')


@app.route('/admin')
def admin():
    """Admin dashboard"""
    return render_template('healthcare_admin.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with full RAG integration"""
    try:
        if not enhanced_chatbot:
            return jsonify({
                "status": "error",
                "message": "Chatbot system not available",
                "response": "I'm sorry, the chatbot system is currently unavailable. Please try again later."
            })
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = session.get('session_id')
        
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
            session['session_id'] = session_id
        
        if not user_message:
            return jsonify({
                "status": "error",
                "message": "No message provided",
                "response": "Please provide a message."
            })
        
        # Process message through enhanced chatbot
        chatbot_response = enhanced_chatbot.process_message(session_id, user_message)
        
        # If ready for execution, execute the tool
        if chatbot_response.get("status") == "ready_for_execution" and tool_executor:
            tool_name = chatbot_response.get("tool")
            parameters = chatbot_response.get("parameters", {})
            
            execution_result = tool_executor.execute_tool(tool_name, parameters)
            
            if execution_result.get("status") == "success":
                # Format successful response
                data = execution_result.get("data", [])
                message = chatbot_response.get("message", "")
                
                if tool_name == "book_appointment":
                    message = "✅ Great! Your appointment has been successfully booked. Here are the details:"
                elif tool_name == "check_availability":
                    message = f"I found {len(data)} available time slots:"
                elif tool_name in ["find_employees_by_criteria", "suggest_suitable_therapists"]:
                    message = f"I found {len(data)} therapists that match your criteria:"
                elif tool_name == "get_patient_appointments":
                    message = f"Here are your appointments ({len(data)} found):"
                
                formatted_response = {
                    "status": "success",
                    "message": message,
                    "response": message,
                    "data": data,
                    "tool_executed": tool_name,
                    "suggestions": chatbot_response.get("suggestions", [])
                }
            else:
                # Handle execution error
                formatted_response = {
                    "status": "error",
                    "message": execution_result.get("message", "Tool execution failed"),
                    "response": f"I encountered an issue: {execution_result.get('message', 'Unknown error')}",
                    "suggestions": ["Try rephrasing your request", "Check if all required information is provided"]
                }
        else:
            # Return chatbot response as-is for parameter collection, etc.
            formatted_response = {
                "status": chatbot_response.get("status", "unknown"),
                "message": chatbot_response.get("message", ""),
                "response": chatbot_response.get("message", ""),
                "suggestions": chatbot_response.get("suggestions", []),
                "missing_parameters": chatbot_response.get("missing_parameters", []),
                "collected_parameters": chatbot_response.get("collected_so_far", {}),
                "knowledge_context": chatbot_response.get("knowledge_context", [])
            }
        
        return jsonify(formatted_response)
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "response": "I'm sorry, I encountered an unexpected error. Please try again."
        })


@app.route('/api/natural_query', methods=['POST'])
def natural_query():
    """Natural language query endpoint for direct database queries"""
    try:
        if not enhanced_chatbot or not database_manager:
            return jsonify({
                "status": "error",
                "message": "System not available"
            })
        
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({
                "status": "error", 
                "message": "No query provided"
            })
        
        # Use enhanced chatbot for natural language understanding
        session_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        response = enhanced_chatbot.process_message(session_id, user_query)
        
        return jsonify({
            "status": "success",
            "query": user_query,
            "intent": response.get("current_intent"),
            "response": response.get("message"),
            "suggestions": response.get("suggestions", [])
        })
    
    except Exception as e:
        logger.error(f"Natural query error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })


@app.route('/api/feedback', methods=['POST'])
def feedback():
    """User feedback endpoint"""
    try:
        data = request.get_json()
        session_id = session.get('session_id')
        helpful = data.get('helpful', True)
        
        if enhanced_chatbot and session_id:
            result = enhanced_chatbot.provide_feedback(session_id, helpful)
            return jsonify(result)
        
        return jsonify({
            "status": "error",
            "message": "No active session for feedback"
        })
    
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })


@app.route('/api/session_summary')
def session_summary():
    """Get current session summary"""
    try:
        session_id = session.get('session_id')
        
        if enhanced_chatbot and session_id:
            summary = enhanced_chatbot.get_session_summary(session_id)
            return jsonify(summary or {"message": "No active session"})
        
        return jsonify({"message": "No active session"})
    
    except Exception as e:
        logger.error(f"Session summary error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })


@app.route('/api/available_tools')
def available_tools():
    """Get list of available tools"""
    try:
        if enhanced_chatbot:
            tools = enhanced_chatbot.tools_registry.list_available_tools()
            return jsonify({
                "status": "success",
                "tools": tools,
                "count": len(tools)
            })
        
        return jsonify({
            "status": "error",
            "message": "Tools registry not available"
        })
    
    except Exception as e:
        logger.error(f"Available tools error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })


@app.route('/health')
def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "chatbot": enhanced_chatbot is not None,
            "database": database_manager is not None and database_manager.test_connection(),
            "tool_executor": tool_executor is not None,
            "rag_system": enhanced_chatbot.rag_system.qdrant_available if enhanced_chatbot else False,
            "embeddings": enhanced_chatbot.rag_system.embeddings_available if enhanced_chatbot else False
        }
    }
    
    # Overall health status
    all_healthy = all(status["components"].values())
    status["status"] = "healthy" if all_healthy else "degraded"
    
    return jsonify(status)


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


if __name__ == '__main__':
    # Set up logging
    logger.info("Starting Healthcare Chatbot Application")
    
    # Check system health
    health = health_check()
    logger.info(f"System health: {health.json}")
    
    # Run the application
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '127.0.0.1')
    
    logger.info(f"Starting server on {host}:{port} (debug={debug})")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )
