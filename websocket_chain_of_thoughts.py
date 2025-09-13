"""
WebSocket implementation for real-time chain of thoughts visualization
Provides real-time updates of the chatbot's thinking process to the frontend
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time

logger = logging.getLogger(__name__)


class ChainOfThoughtsWebSocket:
    """WebSocket handler for real-time chain of thoughts"""
    
    def __init__(self, app: Flask = None):
        """Initialize WebSocket with Flask app"""
        self.app = app
        self.socketio = None
        self.active_sessions: Dict[str, Dict] = {}
        self.thought_queues: Dict[str, List] = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize SocketIO with Flask app"""
        self.app = app
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='threading',
            logger=True,
            engineio_logger=True
        )
        
        # Register WebSocket event handlers
        self._register_handlers()
        
        logger.info("✅ WebSocket initialized for chain of thoughts")
    
    def _register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            session_id = self._generate_session_id()
            join_room(session_id)
            
            self.active_sessions[session_id] = {
                'connected_at': datetime.now().isoformat(),
                'user_agent': None,
                'status': 'connected'
            }
            self.thought_queues[session_id] = []
            
            emit('session_created', {
                'session_id': session_id,
                'status': 'connected',
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"🔌 Client connected: session {session_id}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            # Note: In Flask-SocketIO, we can't easily get session_id here
            # We'll clean up stale sessions periodically
            logger.info("🔌 Client disconnected")
        
        @self.socketio.on('join_session')
        def handle_join_session(data):
            """Handle client joining a specific session"""
            session_id = data.get('session_id')
            if session_id and session_id in self.active_sessions:
                join_room(session_id)
                emit('session_joined', {
                    'session_id': session_id,
                    'status': 'joined',
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"👥 Client joined session: {session_id}")
            else:
                emit('error', {'message': 'Invalid session ID'})
        
        @self.socketio.on('request_thought_history')
        def handle_thought_history(data):
            """Send thought history for a session"""
            session_id = data.get('session_id')
            if session_id and session_id in self.thought_queues:
                emit('thought_history', {
                    'session_id': session_id,
                    'thoughts': self.thought_queues[session_id],
                    'timestamp': datetime.now().isoformat()
                })
        
        @self.socketio.on('clear_thoughts')
        def handle_clear_thoughts(data):
            """Clear thoughts for a session"""
            session_id = data.get('session_id')
            if session_id and session_id in self.thought_queues:
                self.thought_queues[session_id] = []
                emit('thoughts_cleared', {
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"🧹 Cleared thoughts for session: {session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return f"cot_{uuid.uuid4().hex[:12]}"
    
    def emit_thought(self, session_id: str, thought: Dict[str, Any]):
        """Emit a single thought to the client"""
        if not self.socketio:
            logger.warning("WebSocket not initialized")
            return
        
        # Add timestamp and ID to thought
        thought_with_meta = {
            'id': f"thought_{len(self.thought_queues.get(session_id, []))}",
            'timestamp': datetime.now().isoformat(),
            **thought
        }
        
        # Store in queue
        if session_id not in self.thought_queues:
            self.thought_queues[session_id] = []
        self.thought_queues[session_id].append(thought_with_meta)
        
        # Emit to client
        self.socketio.emit('new_thought', {
            'session_id': session_id,
            'thought': thought_with_meta
        }, room=session_id)
        
        logger.debug(f"💭 Emitted thought to session {session_id}: {thought.get('step', 'Unknown')}")
    
    def emit_thought_step(self, session_id: str, step: str, description: str, 
                         status: str = 'processing', data: Optional[Dict] = None):
        """Emit a thought step with standardized format"""
        thought = {
            'step': step,
            'description': description,
            'status': status,  # processing, completed, error
            'data': data or {}
        }
        self.emit_thought(session_id, thought)
    
    def emit_query_analysis(self, session_id: str, query: str, intent: str, entities: List[str]):
        """Emit query analysis step"""
        self.emit_thought_step(
            session_id,
            "Query Analysis",
            f"Analyzing user query: '{query[:50]}{'...' if len(query) > 50 else ''}'",
            "completed",
            {
                'query': query,
                'intent': intent,
                'entities': entities
            }
        )
    
    def emit_schema_retrieval(self, session_id: str, query: str, tables_found: int, confidence: float):
        """Emit schema retrieval step"""
        self.emit_thought_step(
            session_id,
            "Schema Retrieval",
            f"Retrieved {tables_found} relevant database tables (confidence: {confidence:.2f})",
            "completed",
            {
                'query': query,
                'tables_count': tables_found,
                'confidence': confidence
            }
        )
    
    def emit_sql_generation(self, session_id: str, sql_query: str, complexity: str = "medium"):
        """Emit SQL generation step"""
        self.emit_thought_step(
            session_id,
            "SQL Generation",
            f"Generated {complexity} complexity SQL query ({len(sql_query)} characters)",
            "completed",
            {
                'sql_preview': sql_query[:100] + "..." if len(sql_query) > 100 else sql_query,
                'sql_length': len(sql_query),
                'complexity': complexity
            }
        )
    
    def emit_database_query(self, session_id: str, status: str, rows_returned: Optional[int] = None, 
                           error: Optional[str] = None):
        """Emit database query execution step"""
        if status == "executing":
            description = "Executing SQL query against database..."
        elif status == "completed" and rows_returned is not None:
            description = f"Query executed successfully, returned {rows_returned} rows"
        elif status == "error":
            description = f"Query failed: {error}"
        else:
            description = "Database query status update"
        
        self.emit_thought_step(
            session_id,
            "Database Query",
            description,
            status,
            {
                'rows_returned': rows_returned,
                'error': error
            }
        )
    
    def emit_tool_selection(self, session_id: str, tool_name: str, reason: str):
        """Emit tool selection step"""
        self.emit_thought_step(
            session_id,
            "Tool Selection",
            f"Selected tool '{tool_name}': {reason}",
            "completed",
            {
                'tool_name': tool_name,
                'reason': reason
            }
        )
    
    def emit_response_generation(self, session_id: str, response_type: str, confidence: float):
        """Emit response generation step"""
        self.emit_thought_step(
            session_id,
            "Response Generation",
            f"Generating {response_type} response (confidence: {confidence:.2f})",
            "completed",
            {
                'response_type': response_type,
                'confidence': confidence
            }
        )
    
    def emit_error(self, session_id: str, error_type: str, error_message: str, step: str = "Unknown"):
        """Emit error step"""
        self.emit_thought_step(
            session_id,
            f"Error in {step}",
            f"{error_type}: {error_message}",
            "error",
            {
                'error_type': error_type,
                'error_message': error_message,
                'step': step
            }
        )
    
    def emit_completion(self, session_id: str, total_steps: int, duration_ms: int):
        """Emit completion step"""
        self.emit_thought_step(
            session_id,
            "Process Complete",
            f"Completed {total_steps} thinking steps in {duration_ms}ms",
            "completed",
            {
                'total_steps': total_steps,
                'duration_ms': duration_ms
            }
        )
    
    def create_session(self) -> str:
        """Create a new thinking session"""
        session_id = self._generate_session_id()
        self.active_sessions[session_id] = {
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        self.thought_queues[session_id] = []
        return session_id
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session_data in self.active_sessions.items():
            created_at = datetime.fromisoformat(session_data['created_at'])
            age_hours = (current_time - created_at).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            if session_id in self.thought_queues:
                del self.thought_queues[session_id]
        
        if sessions_to_remove:
            logger.info(f"🧹 Cleaned up {len(sessions_to_remove)} old sessions")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions"""
        return {
            'active_sessions': len(self.active_sessions),
            'total_thoughts': sum(len(thoughts) for thoughts in self.thought_queues.values()),
            'avg_thoughts_per_session': (
                sum(len(thoughts) for thoughts in self.thought_queues.values()) / 
                len(self.thought_queues) if self.thought_queues else 0
            )
        }


# Singleton instance
chain_of_thoughts_ws = None

def get_chain_of_thoughts_ws() -> ChainOfThoughtsWebSocket:
    """Get or create the chain of thoughts WebSocket instance"""
    global chain_of_thoughts_ws
    if chain_of_thoughts_ws is None:
        chain_of_thoughts_ws = ChainOfThoughtsWebSocket()
    return chain_of_thoughts_ws

def init_websocket_with_app(app: Flask) -> ChainOfThoughtsWebSocket:
    """Initialize WebSocket with Flask app"""
    global chain_of_thoughts_ws
    chain_of_thoughts_ws = ChainOfThoughtsWebSocket(app)
    return chain_of_thoughts_ws
