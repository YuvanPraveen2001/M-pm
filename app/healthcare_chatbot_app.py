"""
Healthcare Appointment Booking Chatbot Application
Advanced Flask app implementing the sophisticated booking workflow
"""

import os
import sys
import json
import uuid
import sqlite3
import time
import threading
from flask import Flask, render_template, request, jsonify, session, Response
from datetime import datetime, time as time_type, date

# Custom JSON encoder for datetime objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, time_type):
            return obj.strftime('%H:%M:%S')
        return super().default(obj)

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from healthcare_database_manager_sqlserver import HealthcareDatabaseManager
from healthcare_chatbot_service import HealthcareResponseGenerator, HealthcareConversationManager
from schema_api import register_schema_management_routes
from dotenv import load_dotenv

# WebSocket integration
try:
    from websocket_chain_of_thoughts import init_websocket_with_app
    WEBSOCKET_AVAILABLE = True
except ImportError:
    print("⚠️ WebSocket support not available")
    WEBSOCKET_AVAILABLE = False

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='../templates')
app.secret_key = os.getenv('SECRET_KEY', 'healthcare-booking-secret-key')

# Initialize WebSocket if available
if WEBSOCKET_AVAILABLE:
    websocket_cot = init_websocket_with_app(app)
    print("✅ WebSocket chain of thoughts initialized")
else:
    websocket_cot = None

# Initialize components
db_manager = HealthcareDatabaseManager()
chatbot = HealthcareResponseGenerator(db_manager)

# Register schema management API routes
register_schema_management_routes(app, db_manager)

print("✅ Healthcare Database Manager initialized")
print("✅ Natural Language Query Processor enabled")
print("✅ Multi-step Booking Workflow ready")
print("✅ Schema Management API enabled")

# Store conversation managers for each session
conversation_sessions = {}

# Store live thoughts for streaming
live_thoughts = {}
live_thoughts_lock = threading.Lock()

def add_live_thought(session_id, thought):
    """Add a live thought for a session"""
    with live_thoughts_lock:
        if session_id not in live_thoughts:
            live_thoughts[session_id] = []
        live_thoughts[session_id].append({
            'thought': thought,
            'timestamp': datetime.now().isoformat()
        })

def get_live_thoughts(session_id):
    """Get and clear live thoughts for a session"""
    with live_thoughts_lock:
        thoughts = live_thoughts.get(session_id, [])
        if session_id in live_thoughts:
            live_thoughts[session_id] = []
        return thoughts

@app.route('/')
def index():
    """Main chatbot interface"""
    return render_template('healthcare_chatbot.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with sophisticated booking flow"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get or create session
        if not session_id or session_id not in conversation_sessions:
            session_id = str(uuid.uuid4())
            conversation_sessions[session_id] = HealthcareConversationManager()
            
            # Try to create session in database (graceful failure)
            try:
                print("🔍 DEBUG: Attempting to create database session...")
                db_session_id = db_manager.create_chat_session()
                conversation_sessions[session_id].update_context('db_session_id', db_session_id)
                print(f"✅ DEBUG: Database session created: {db_session_id}")
            except Exception as db_error:
                print(f"⚠️  WARNING: Could not create database session: {str(db_error)}")
                print("🔍 DEBUG: Continuing without database session logging...")
                conversation_sessions[session_id].update_context('db_session_id', None)
        
        conv_manager = conversation_sessions[session_id]
        conv_manager.update_context('last_user_input', user_message)
        
        # Add live thoughts simulation
        add_live_thought(session_id, "🔍 Processing your message...")
        time.sleep(0.2)
        add_live_thought(session_id, "🤖 Analyzing intent and extracting entities")
        time.sleep(0.3)
        add_live_thought(session_id, "🗄️ Connecting to healthcare database")
        
        # Save user message (graceful failure)
        db_session_id = conv_manager.get_context('db_session_id')
        if db_session_id:
            try:
                print("🔍 DEBUG: Saving user message to database...")
                db_manager.save_chat_message(db_session_id, 'user', user_message)
                print("✅ DEBUG: User message saved to database")
                add_live_thought(session_id, "📋 User message saved to database")
            except Exception as db_error:
                print(f"⚠️  WARNING: Could not save user message: {str(db_error)}")
                add_live_thought(session_id, "⚠️ Database logging unavailable")
        
        add_live_thought(session_id, "🧠 Generating intelligent response...")
        
        # Generate response using sophisticated booking flow
        print("🔍 DEBUG: Generating chatbot response...")
        response = chatbot.generate_response(user_message, conv_manager)
        print("✅ DEBUG: Chatbot response generated")
        
        add_live_thought(session_id, "✅ Response generated successfully")
        
        # Save bot response (graceful failure)
        if db_session_id:
            try:
                print("🔍 DEBUG: Saving bot response to database...")
                entities_json = json.dumps(response.entities) if response.entities else "{}"
                db_manager.save_chat_message(
                    db_session_id, 'bot', response.message, 
                    response.intent, entities_json
                )
                print("✅ DEBUG: Bot response saved to database")
            except Exception as db_error:
                print(f"⚠️  WARNING: Could not save bot response: {str(db_error)}")
        
        print("🔍 DEBUG: Preparing JSON response...")
        
        # Prepare response data with custom JSON encoding
        response_data = {
            'session_id': session_id,
            'response': response.message,
            'status': response.status,
            'data': response.data,
            'suggested_actions': response.suggested_actions,
            'booking_step': response.booking_step.value if response.booking_step else None,
            'chain_of_thoughts': response.chain_of_thoughts,
            'websocket_session_id': response.websocket_session_id,
            'processing_time_ms': response.processing_time_ms,
            'confidence_score': response.confidence_score,
            'timestamp': datetime.now().isoformat()
        }
        
        # Convert to JSON string using custom encoder, then back to dict for jsonify
        json_str = json.dumps(response_data, cls=CustomJSONEncoder)
        return jsonify(json.loads(json_str))
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/search-patient', methods=['POST'])
def search_patient():
    """Search for patients by name"""
    try:
        data = request.get_json()
        patient_name = data.get('patient_name', '').strip()
        
        if not patient_name:
            return jsonify({'error': 'Patient name is required'}), 400
        
        patients = db_manager.search_patient_by_name(patient_name)
        
        return jsonify({
            'success': True,
            'patients': patients,
            'count': len(patients)
        })
        
    except Exception as e:
        print(f"Error searching patients: {str(e)}")
        return jsonify({'error': 'Failed to search patients'}), 500

@app.route('/api/search-employee', methods=['POST'])
def search_employee():
    """Search for employees by name"""
    try:
        data = request.get_json()
        employee_name = data.get('employee_name', '').strip()
        
        if not employee_name:
            return jsonify({'error': 'Employee name is required'}), 400
        
        employees = db_manager.search_employee_by_name(employee_name)
        
        return jsonify({
            'success': True,
            'employees': employees,
            'count': len(employees)
        })
        
    except Exception as e:
        print(f"Error searching employees: {str(e)}")
        return jsonify({'error': 'Failed to search employees'}), 500

@app.route('/api/patient-authorizations', methods=['POST'])
def get_patient_authorizations():
    """Get authorizations for a patient"""
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return jsonify({'error': 'Patient ID is required'}), 400
        
        authorizations = db_manager.get_patient_authorizations(patient_id)
        
        return jsonify({
            'success': True,
            'authorizations': authorizations,
            'count': len(authorizations)
        })
        
    except Exception as e:
        print(f"Error getting patient authorizations: {str(e)}")
        return jsonify({'error': 'Failed to get authorizations'}), 500

@app.route('/api/auth-details', methods=['POST'])
def get_auth_details():
    """Get authorization details"""
    try:
        data = request.get_json()
        auth_id = data.get('auth_id')
        
        if not auth_id:
            return jsonify({'error': 'Authorization ID is required'}), 400
        
        auth_details = db_manager.get_auth_details(auth_id)
        
        return jsonify({
            'success': True,
            'auth_details': auth_details,
            'count': len(auth_details)
        })
        
    except Exception as e:
        print(f"Error getting auth details: {str(e)}")
        return jsonify({'error': 'Failed to get authorization details'}), 500

@app.route('/api/patient-locations', methods=['POST'])
def get_patient_locations():
    """Get locations for a patient"""
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return jsonify({'error': 'Patient ID is required'}), 400
        
        locations = db_manager.get_patient_locations(patient_id)
        
        return jsonify({
            'success': True,
            'locations': locations,
            'count': len(locations)
        })
        
    except Exception as e:
        print(f"Error getting patient locations: {str(e)}")
        return jsonify({'error': 'Failed to get locations'}), 500

@app.route('/api/suggest-employees', methods=['POST'])
def suggest_employees():
    """Get employee suggestions based on criteria"""
    try:
        data = request.get_json()
        service_type_id = data.get('service_type_id')
        treatment_type_id = data.get('treatment_type_id')
        location_id = data.get('location_id')
        patient_id = data.get('patient_id')
        start_datetime = data.get('start_datetime', datetime.now().isoformat())
        
        if not all([service_type_id, treatment_type_id, location_id, patient_id]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        suggestions = db_manager.suggest_employees(
            service_type_id, treatment_type_id, location_id, patient_id, start_datetime
        )
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions)
        })
        
    except Exception as e:
        print(f"Error getting employee suggestions: {str(e)}")
        return jsonify({'error': 'Failed to get employee suggestions'}), 500

@app.route('/api/check-eligibility', methods=['POST'])
def check_employee_eligibility():
    """Check employee eligibility for service"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        service_type_id = data.get('service_type_id')
        location_id = data.get('location_id')
        treatment_type_id = data.get('treatment_type_id')
        
        if not all([employee_id, service_type_id, location_id, treatment_type_id]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        eligibility = db_manager.check_employee_eligibility(
            employee_id, service_type_id, location_id, treatment_type_id
        )
        
        return jsonify({
            'success': True,
            'eligibility': eligibility
        })
        
    except Exception as e:
        print(f"Error checking eligibility: {str(e)}")
        return jsonify({'error': 'Failed to check eligibility'}), 500

@app.route('/api/check-conflicts', methods=['POST'])
def check_appointment_conflicts():
    """Check for appointment conflicts"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        start_datetime = data.get('start_datetime')
        duration_minutes = data.get('duration_minutes', 60)
        
        if not all([employee_id, start_datetime]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        conflicts = db_manager.check_appointment_conflicts(
            employee_id, start_datetime, duration_minutes
        )
        
        return jsonify({
            'success': True,
            'conflicts': conflicts,
            'has_conflicts': len(conflicts) > 0
        })
        
    except Exception as e:
        print(f"Error checking conflicts: {str(e)}")
        return jsonify({'error': 'Failed to check conflicts'}), 500

@app.route('/api/book-appointment', methods=['POST'])
def book_appointment():
    """Book a new appointment"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        # Get booking context from session
        if session_id not in conversation_sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        conv_manager = conversation_sessions[session_id]
        booking_context = conv_manager.get_booking_context()
        
        # Prepare booking data from context
        booking_data = {
            'patient_id': booking_context.selected_patient.get('PatientId'),
            'employee_id': booking_context.final_employee.get('EmployeeId'),
            'auth_id': booking_context.selected_auth.get('AuthId'),
            'auth_detail_id': booking_context.selected_auth_detail.get('AuthDetailId'),
            'service_type_id': booking_context.selected_auth_detail.get('ServiceTypeId'),
            'location_id': booking_context.selected_location.get('LocationId'),
            'scheduled_date': booking_context.appointment_datetime,
            'scheduled_minutes': booking_context.duration_minutes,
            'notes': booking_context.notes
        }
        
        # Override with any provided data
        booking_data.update(data.get('booking_data', {}))
        
        # Book appointment
        result = db_manager.book_appointment(booking_data)
        
        if result['success']:
            # Update conversation state
            booking_context.step = booking_context.step.COMPLETED
            
        return jsonify(result)
        
    except Exception as e:
        print(f"Error booking appointment: {str(e)}")
        return jsonify({'error': 'Failed to book appointment', 'details': str(e)}), 500

@app.route('/api/query-direct', methods=['POST'])
def query_direct():
    """Direct natural language query endpoint (for testing)"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Process query directly through the natural language processor
        from natural_language_processor import HealthcareQueryProcessor
        query_processor = HealthcareQueryProcessor(db_manager)
        
        result = query_processor.process_query(user_query)
        
        return jsonify({
            'success': result['success'],
            'message': result.get('message', ''),
            'results': result.get('results', []),
            'sql_query': result.get('sql_query', ''),
            'analysis': result.get('analysis', {}),
            'formatted_results': result.get('formatted_results', []),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in direct query endpoint: {str(e)}")
        return jsonify({'error': 'Failed to process query', 'details': str(e)}), 500

@app.route('/api/session-context/<session_id>')
def get_session_context(session_id):
    """Get session context for debugging"""
    try:
        if session_id in conversation_sessions:
            conv_manager = conversation_sessions[session_id]
            booking_context = conv_manager.get_booking_context()
            
            return jsonify({
                'session_id': session_id,
                'booking_step': booking_context.step.value,
                'context': conv_manager.context,
                'has_patient': booking_context.selected_patient is not None,
                'has_employee': booking_context.selected_employee is not None,
                'has_auth': booking_context.selected_auth is not None,
                'has_location': booking_context.selected_location is not None
            })
        
        return jsonify({'error': 'Session not found'}), 404
        
    except Exception as e:
        print(f"Error getting session context: {str(e)}")
        return jsonify({'error': 'Failed to get session context'}), 500

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    return render_template('healthcare_admin.html')

@app.route('/api/admin/stats')
def admin_stats():
    """Get admin statistics"""
    try:
        # This would be implemented based on your actual database structure
        return jsonify({
            'total_patients': 0,
            'active_employees': 0,
            'scheduled_appointments': 0,
            'todays_sessions': 0
        })
        
    except Exception as e:
        print(f"Error getting admin stats: {str(e)}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@app.route('/api/test-db')
def test_database():
    """Test database connection"""
    try:
        print("🔍 DEBUG: Testing database connection...")
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print("✅ DEBUG: Database connection test successful")
            serverCre = {
                'success': True,
                'message': 'Database connection successful',
                'test_result': result[0] if result else None,
                'server': os.getenv('SQL_SERVER', 'localhost'),
                'database': os.getenv('SQL_DATABASE', 'AIStagingDB_20250811')
            }
            print(f"🔍 DEBUG: Test result - {serverCre}")
            return jsonify(serverCre)
            
    except Exception as e:
        print(f"❌ ERROR: Database connection test failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Database connection failed',
            'server': os.getenv('SQL_SERVER', 'localhost'),
            'database': os.getenv('SQL_DATABASE', 'AIStagingDB_20250811')
        }), 500

@app.route('/api/live-thoughts/<session_id>')
def stream_live_thoughts(session_id):
    """Stream live thoughts for a session using Server-Sent Events"""
    def generate():
        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected', 'message': 'Live thoughts stream connected'})}\n\n"
        
        # Poll for live thoughts
        last_count = 0
        max_polls = 300  # 30 seconds max (100ms * 300)
        polls = 0
        
        while polls < max_polls:
            thoughts = get_live_thoughts(session_id)
            if thoughts:
                for thought in thoughts:
                    yield f"data: {json.dumps({'type': 'thought', 'data': thought})}\n\n"
                last_count += len(thoughts)
            
            # Check if session is done processing (no more thoughts expected)
            if session_id in conversation_sessions:
                # If we have thoughts and no new ones for a while, close stream
                if last_count > 0 and not thoughts:
                    time.sleep(0.5)  # Wait a bit more
                    final_thoughts = get_live_thoughts(session_id)
                    if final_thoughts:
                        for thought in final_thoughts:
                            yield f"data: {json.dumps({'type': 'thought', 'data': thought})}\n\n"
                    break
            
            time.sleep(0.1)  # Poll every 100ms
            polls += 1
        
        # Send completion message
        yield f"data: {json.dumps({'type': 'complete', 'message': 'Thinking process complete'})}\n\n"
    
    return Response(generate(), mimetype='text/plain',
                   headers={'Cache-Control': 'no-cache',
                           'Connection': 'keep-alive',
                           'Access-Control-Allow-Origin': '*'})

@app.route('/schema')
def schema_management():
    """Schema Management Dashboard"""
    return render_template('schema_management.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    print("🏥 Starting Healthcare Appointment Booking Chatbot...")
    print("🌐 Open http://localhost:5001 to start booking appointments")
    print("📋 Admin Dashboard: http://localhost:5001/admin")
    print("\n📋 Booking Flow Steps:")
    print("1. Patient Search & Confirmation")
    print("2. Provider Search & Selection")
    print("3. Authorization Verification")
    print("4. Service Selection")
    print("5. Location Selection")
    print("6. Employee Eligibility Check")
    print("7. Provider Suggestions")
    print("8. Final Appointment Booking")
    
    app.run(debug=False, port=5001, host='0.0.0.0')
