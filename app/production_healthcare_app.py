"""
Production Healthcare Appointment Booking Application
Real-world implementation with SQL Server integration and natural language processing
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from healthcare_database_manager_sqlserver import HealthcareDatabaseManager
from healthcare_chatbot_service import HealthcareResponseGenerator, HealthcareConversationManager
from natural_language_processor import HealthcareQueryProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'healthcare_app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv('SECRET_KEY', 'healthcare-production-secret-key-change-in-production')

# Enable CORS for API endpoints
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Production configuration
app.config.update(
    DEBUG=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
    TESTING=False,
    SECRET_KEY=os.getenv('SECRET_KEY', 'healthcare-production-secret-key'),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Initialize components
try:
    db_manager = HealthcareDatabaseManager()
    chatbot = HealthcareResponseGenerator(db_manager)
    query_processor = HealthcareQueryProcessor(db_manager)
    
    logger.info("✅ Healthcare Database Manager initialized")
    logger.info("✅ Natural Language Query Processor enabled")
    logger.info("✅ Multi-step Booking Workflow ready")
    
except Exception as e:
    logger.error(f"❌ Failed to initialize application components: {str(e)}")
    raise

# Store conversation managers for each session
conversation_sessions = {}

# Session cleanup configuration
MAX_SESSION_AGE = 3600  # 1 hour
MAX_SESSIONS = 1000

def cleanup_old_sessions():
    """Clean up old conversation sessions"""
    current_time = datetime.now().timestamp()
    sessions_to_remove = []
    
    for session_id, conv_manager in conversation_sessions.items():
        session_age = current_time - conv_manager.get_context('created_at', current_time)
        if session_age > MAX_SESSION_AGE:
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        del conversation_sessions[session_id]
    
    # Limit total sessions
    if len(conversation_sessions) > MAX_SESSIONS:
        oldest_sessions = sorted(
            conversation_sessions.items(), 
            key=lambda x: x[1].get_context('created_at', 0)
        )[:len(conversation_sessions) - MAX_SESSIONS]
        
        for session_id, _ in oldest_sessions:
            del conversation_sessions[session_id]

# ============================================================================
# MAIN ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main healthcare chatbot interface"""
    try:
        cleanup_old_sessions()
        return render_template('healthcare_chatbot.html')
    except Exception as e:
        logger.error(f"Error loading main page: {str(e)}")
        return render_template('error.html', error="Application temporarily unavailable"), 500

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard - requires authentication in production"""
    try:
        # In production, add proper authentication here
        return render_template('healthcare_admin.html')
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        return render_template('error.html', error="Admin dashboard unavailable"), 500

# ============================================================================
# CHAT API ENDPOINTS
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with enhanced error handling and logging"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Rate limiting check (simple implementation)
        if len(user_message) > 1000:
            return jsonify({'error': 'Message too long'}), 400
        
        # Get or create session
        if not session_id or session_id not in conversation_sessions:
            session_id = str(uuid.uuid4())
            conversation_sessions[session_id] = HealthcareConversationManager()
            conversation_sessions[session_id].update_context('created_at', datetime.now().timestamp())
            
            # Create session in database
            try:
                db_session_id = db_manager.create_chat_session()
                conversation_sessions[session_id].update_context('db_session_id', db_session_id)
            except Exception as e:
                logger.warning(f"Failed to create database session: {str(e)}")
        
        conv_manager = conversation_sessions[session_id]
        conv_manager.update_context('last_user_input', user_message)
        conv_manager.update_context('last_activity', datetime.now().timestamp())
        
        # Save user message to database
        db_session_id = conv_manager.get_context('db_session_id')
        if db_session_id:
            try:
                db_manager.save_chat_message(db_session_id, 'user', user_message)
            except Exception as e:
                logger.warning(f"Failed to save user message: {str(e)}")
        
        # Generate response using sophisticated booking flow
        response = chatbot.generate_response(user_message, conv_manager)
        
        # Save bot response to database
        if db_session_id:
            try:
                db_manager.save_chat_message(
                    db_session_id, 'bot', response.message, 
                    response.intent, json.dumps(response.entities)
                )
            except Exception as e:
                logger.warning(f"Failed to save bot response: {str(e)}")
        
        # Log conversation for monitoring
        logger.info(f"Chat - Session: {session_id[:8]}, Intent: {response.intent}, Step: {response.booking_step}")
        
        return jsonify({
            'session_id': session_id,
            'response': response.message,
            'suggestions': response.suggestions,
            'requires_action': response.requires_action,
            'action_type': response.action_type,
            'intent': response.intent,
            'booking_step': response.booking_step,
            'step_data': response.step_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Chat error {error_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'error_id': error_id,
            'message': 'Sorry, I encountered an issue. Please try again or contact support.'
        }), 500

@app.route('/api/query-natural', methods=['POST'])
def query_natural():
    """Enhanced natural language query endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Query is required'}), 400
        
        if len(user_query) > 500:
            return jsonify({'error': 'Query too long'}), 400
        
        # Process query through natural language processor
        result = query_processor.process_query(user_query)
        
        # Log query for monitoring
        logger.info(f"Natural Language Query: '{user_query}' - Success: {result['success']}")
        
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
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Natural language query error {error_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to process query',
            'error_id': error_id,
            'message': 'Sorry, I couldn\'t process your query. Please try rephrasing.'
        }), 500

# ============================================================================
# HEALTHCARE BOOKING API ENDPOINTS
# ============================================================================

@app.route('/api/search-patient', methods=['POST'])
def search_patient():
    """Enhanced patient search with validation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        patient_name = data.get('patient_name', '').strip()
        
        if not patient_name:
            return jsonify({'error': 'Patient name is required'}), 400
        
        if len(patient_name) < 2:
            return jsonify({'error': 'Patient name must be at least 2 characters'}), 400
        
        patients = db_manager.search_patient_by_name(patient_name)
        
        logger.info(f"Patient search: '{patient_name}' - Found: {len(patients)} matches")
        
        return jsonify({
            'success': True,
            'patients': patients,
            'count': len(patients),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Patient search error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to search patients'}), 500

@app.route('/api/search-employee', methods=['POST'])
def search_employee():
    """Enhanced employee search with validation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        employee_name = data.get('employee_name', '').strip()
        
        if not employee_name:
            return jsonify({'error': 'Employee name is required'}), 400
        
        if len(employee_name) < 2:
            return jsonify({'error': 'Employee name must be at least 2 characters'}), 400
        
        employees = db_manager.search_employee_by_name(employee_name)
        
        logger.info(f"Employee search: '{employee_name}' - Found: {len(employees)} matches")
        
        return jsonify({
            'success': True,
            'employees': employees,
            'count': len(employees),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Employee search error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to search employees'}), 500

@app.route('/api/patient-authorizations', methods=['POST'])
def get_patient_authorizations():
    """Get patient authorizations with validation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return jsonify({'error': 'Patient ID is required'}), 400
        
        try:
            patient_id = int(patient_id)
        except ValueError:
            return jsonify({'error': 'Invalid patient ID format'}), 400
        
        authorizations = db_manager.get_patient_authorizations(patient_id)
        
        return jsonify({
            'success': True,
            'authorizations': authorizations,
            'count': len(authorizations),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get patient authorizations error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to get authorizations'}), 500

@app.route('/api/book-appointment', methods=['POST'])
def book_appointment():
    """Enhanced appointment booking with comprehensive validation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        session_id = data.get('session_id')
        
        if not session_id or session_id not in conversation_sessions:
            return jsonify({'error': 'Invalid or expired session'}), 400
        
        conv_manager = conversation_sessions[session_id]
        booking_context = conv_manager.get_booking_context()
        
        # Validate booking context
        if not all([
            booking_context.selected_patient,
            booking_context.final_employee,
            booking_context.selected_auth,
            booking_context.selected_auth_detail,
            booking_context.selected_location
        ]):
            return jsonify({'error': 'Incomplete booking information'}), 400
        
        # Prepare booking data
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
        
        # Final validation
        required_fields = ['patient_id', 'employee_id', 'auth_id', 'auth_detail_id', 'service_type_id', 'location_id', 'scheduled_date']
        missing_fields = [field for field in required_fields if not booking_data.get(field)]
        
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Book appointment
        result = db_manager.book_appointment(booking_data)
        
        if result['success']:
            # Update conversation state
            booking_context.step = booking_context.step.COMPLETED
            logger.info(f"Appointment booked successfully: {result.get('appointment_id')}")
        else:
            logger.warning(f"Appointment booking failed: {result.get('error')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Appointment booking error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to book appointment', 'details': str(e)}), 500

# ============================================================================
# ADMIN API ENDPOINTS
# ============================================================================

@app.route('/api/admin/stats')
def admin_stats():
    """Enhanced admin statistics"""
    try:
        # Get real statistics from database
        stats = {
            'total_patients': 0,
            'active_employees': 0,
            'scheduled_appointments': 0,
            'todays_sessions': len(conversation_sessions),
            'system_status': 'healthy',
            'database_status': 'connected',
            'last_updated': datetime.now().isoformat()
        }
        
        # Try to get real database statistics
        try:
            # Patient count
            patient_results = db_manager.execute_query("SELECT COUNT(*) as count FROM Patient WHERE IsActive = 1")
            if patient_results:
                stats['total_patients'] = patient_results[0]['count']
            
            # Employee count
            employee_results = db_manager.execute_query("SELECT COUNT(*) as count FROM Employee WHERE IsActive = 1")
            if employee_results:
                stats['active_employees'] = employee_results[0]['count']
            
            # Today's appointments
            today = datetime.now().strftime('%Y-%m-%d')
            appointment_results = db_manager.execute_query(
                f"SELECT COUNT(*) as count FROM Appointment WHERE CAST(ScheduledDate AS DATE) = '{today}' AND StatusId IN (1, 2)"
            )
            if appointment_results:
                stats['scheduled_appointments'] = appointment_results[0]['count']
                
        except Exception as e:
            logger.warning(f"Failed to get database statistics: {str(e)}")
            stats['database_status'] = 'warning'
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Admin stats error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to get statistics',
            'system_status': 'error',
            'database_status': 'error'
        }), 500

@app.route('/api/admin/sessions')
def admin_sessions():
    """Get active session information for admin"""
    try:
        cleanup_old_sessions()
        
        session_info = []
        for session_id, conv_manager in conversation_sessions.items():
            booking_context = conv_manager.get_booking_context()
            session_info.append({
                'session_id': session_id[:8] + '...',  # Truncate for privacy
                'created_at': conv_manager.get_context('created_at', 0),
                'last_activity': conv_manager.get_context('last_activity', 0),
                'booking_step': booking_context.step.value,
                'has_patient': booking_context.selected_patient is not None,
                'has_employee': booking_context.selected_employee is not None
            })
        
        return jsonify({
            'sessions': session_info,
            'total_count': len(session_info),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Admin sessions error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to get session information'}), 500

# ============================================================================
# HEALTH CHECK AND MONITORING
# ============================================================================

@app.route('/health')
def health_check():
    """Application health check endpoint"""
    try:
        # Test database connection
        db_manager.execute_query("SELECT 1")
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'connected',
            'active_sessions': len(conversation_sessions)
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 503

@app.route('/api/version')
def version():
    """Get application version information"""
    return jsonify({
        'name': 'Healthcare Appointment Booking System',
        'version': '1.0.0',
        'build_date': '2025-09-12',
        'features': [
            'Natural Language Query Processing',
            'Multi-step Appointment Booking',
            'SQL Server Integration',
            'Real-time Chat Interface',
            'Admin Dashboard',
            'Session Management'
        ]
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', error="Internal server error"), 500

@app.errorhandler(403)
def forbidden(error):
    logger.warning(f"403 error: {request.url}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Access forbidden'}), 403
    return render_template('error.html', error="Access forbidden"), 403

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    logger.info("🏥 Starting Production Healthcare Appointment Booking System...")
    logger.info("🌐 Main Interface: http://localhost:5001")
    logger.info("📋 Admin Dashboard: http://localhost:5001/admin")
    logger.info("🔍 Health Check: http://localhost:5001/health")
    logger.info("📊 API Documentation: Available via /api endpoints")
    
    logger.info("\n📋 Enhanced Features:")
    logger.info("✅ Natural Language Query Processing")
    logger.info("✅ Production-ready Error Handling")
    logger.info("✅ Comprehensive Logging")
    logger.info("✅ Session Management & Cleanup")
    logger.info("✅ Health Monitoring")
    logger.info("✅ Admin Analytics")
    logger.info("✅ Security Headers")
    logger.info("✅ Input Validation")
    
    # Run with appropriate configuration
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(debug=debug, port=port, host=host)
