"""
Quadrant Database RAG (Retrieval-Augmented Generation) System
Integrates with the healthcare chatbot for enhanced context understanding
and knowledge retrieval using vector embeddings.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import sqlite3
import numpy as np

# Quadrant DB client imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams, PointStruct
except ImportError:
    print("Warning: qdrant-client not installed. Install with: pip install qdrant-client")
    QdrantClient = None

# Ollama imports for embeddings
try:
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.chat_models import ChatOllama
except ImportError:
    print("Warning: langchain-community not installed. Install with: pip install langchain-community")
    OllamaEmbeddings = None
    ChatOllama = None

from ai_chatbot_tools import HealthcareToolsRegistry
from nlp_processor import ConversationManager, ConversationContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants from app.py
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "phi3:mini"


@dataclass
class HealthcareDocument:
    """Represents a healthcare knowledge document"""
    id: str
    content: str
    document_type: str  # 'schema', 'procedure', 'faq', 'guideline'
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class HealthcareKnowledgeBase:
    """Manages healthcare-specific knowledge documents"""
    
    def __init__(self):
        self.documents: Dict[str, HealthcareDocument] = {}
        self._load_healthcare_knowledge()
    
    def _load_healthcare_knowledge(self):
        """Load healthcare-specific knowledge documents"""
        
        # Schema-related documents
        self.add_document(HealthcareDocument(
            id="schema_appointment",
            content="""
            Appointment Table Schema:
            - AppointmentId: Unique identifier for each appointment
            - PatientId: References Patient table
            - EmployeeId: References Employee (therapist) table
            - ScheduledDate: Date and time of appointment
            - ScheduledMinutes: Duration of appointment
            - AppointmentStatusId: Status (1=Scheduled, 2=Completed, 3=Cancelled)
            - LocationId: Where the appointment takes place
            - ServiceTypeId: Type of therapy service
            - Notes: Additional notes about the appointment
            
            Common queries:
            - Find available appointment slots
            - Book new appointments
            - View patient appointment history
            - Check therapist schedules
            """,
            document_type="schema",
            metadata={"table": "Appointment", "category": "booking"}
        ))
        
        self.add_document(HealthcareDocument(
            id="schema_employee",
            content="""
            Employee Table Schema (Therapists):
            - EmployeeId: Unique identifier for therapist
            - FirstName, LastName: Therapist name
            - Gender: Gender of therapist
            - Email, PhoneCell: Contact information
            - HighestDegree: Education level
            - ServiceAreaZip: Service area zip code
            - Active: Whether therapist is currently active
            - ZoneId: Service zone/area
            - TreatmentTypeId: Specialization in treatment types
            
            Related tables:
            - EmployeeAvailabilityDateTime: Therapist availability windows
            - EmployeeZoneMapping: Zone assignments
            - EmployeeTreatmentTypeMapping: Treatment specializations
            - EmployeeLanguageMapping: Languages spoken
            """,
            document_type="schema",
            metadata={"table": "Employee", "category": "therapist"}
        ))
        
        self.add_document(HealthcareDocument(
            id="booking_procedures",
            content="""
            Appointment Booking Procedures:
            
            1. Patient Validation:
               - Verify patient exists and is active
               - Check patient eligibility
            
            2. Therapist Selection:
               - Check therapist availability
               - Verify therapist qualifications
               - Consider patient preferences (gender, language, location)
            
            3. Availability Check:
               - Check EmployeeAvailabilityDateTime for time windows
               - Verify no conflicting appointments exist
               - Consider minimum advance booking time (24 hours)
            
            4. Booking Creation:
               - Create appointment record
               - Update availability status
               - Send confirmation
            
            Business Rules:
            - No double booking allowed
            - 24-hour minimum advance booking
            - Maximum 3 months advance booking
            - Same-zone therapists preferred
            """,
            document_type="procedure",
            metadata={"category": "booking", "process": "appointment_booking"}
        ))
        
        self.add_document(HealthcareDocument(
            id="search_criteria",
            content="""
            Therapist Search Criteria and Filters:
            
            Available Filters:
            - Zone/Area: Based on EmployeeZoneMapping
            - Gender: Male, Female, Non-binary
            - Language: From EmployeeLanguageMapping
            - Degree Level: HighestDegree field
            - Zip Code: ServiceAreaZip for location proximity
            - Specialization: Treatment types from EmployeeTreatmentTypeMapping
            - Availability: Based on EmployeeAvailabilityDateTime
            
            Search Priority:
            1. Same zone as patient
            2. Matching preferences (gender, language)
            3. Higher qualifications
            4. Better ratings
            5. Proximity to patient location
            
            Common Search Patterns:
            - "Find female therapist in my area"
            - "Spanish-speaking therapist for anxiety"
            - "Child therapist with PhD"
            - "Therapist available this week"
            """,
            document_type="guideline",
            metadata={"category": "search", "process": "therapist_search"}
        ))
        
        self.add_document(HealthcareDocument(
            id="availability_faq",
            content="""
            Frequently Asked Questions - Availability:
            
            Q: How do I check if a therapist is available?
            A: Use the check_availability tool with therapist ID and desired date/time.
            
            Q: What if my preferred time is not available?
            A: The system will suggest alternative times within your preferences.
            
            Q: How far in advance can I book?
            A: Appointments can be booked up to 3 months in advance.
            
            Q: What's the minimum advance booking time?
            A: Appointments must be booked at least 24 hours in advance.
            
            Q: Can I see multiple therapists?
            A: Yes, you can book with different therapists for different services.
            
            Q: How do I find therapists in my area?
            A: Use zone or zip code filters to find nearby therapists.
            """,
            document_type="faq",
            metadata={"category": "availability", "topic": "booking_questions"}
        ))
        
        logger.info(f"Loaded {len(self.documents)} healthcare knowledge documents")
    
    def add_document(self, document: HealthcareDocument):
        """Add a document to the knowledge base"""
        self.documents[document.id] = document
    
    def get_document(self, doc_id: str) -> Optional[HealthcareDocument]:
        """Get a document by ID"""
        return self.documents.get(doc_id)
    
    def get_documents_by_type(self, doc_type: str) -> List[HealthcareDocument]:
        """Get all documents of a specific type"""
        return [doc for doc in self.documents.values() if doc.document_type == doc_type]
    
    def search_documents(self, query: str, category: Optional[str] = None) -> List[HealthcareDocument]:
        """Simple text search in documents"""
        results = []
        query_lower = query.lower()
        
        for doc in self.documents.values():
            if category and doc.metadata.get('category') != category:
                continue
                
            if query_lower in doc.content.lower():
                results.append(doc)
        
        return results


class QuadrantRAGSystem:
    """
    RAG system using Quadrant DB for vector storage and retrieval
    Integrates with healthcare chatbot for enhanced responses
    """
    
    def __init__(self, 
                 qdrant_host: str = "localhost",
                 qdrant_port: int = 6333,
                 collection_name: str = "healthcare_knowledge"):
        
        self.collection_name = collection_name
        self.knowledge_base = HealthcareKnowledgeBase()
        
        # Initialize Quadrant client
        if QdrantClient:
            try:
                self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
                self.qdrant_available = True
                logger.info(f"Connected to Quadrant DB at {qdrant_host}:{qdrant_port}")
            except Exception as e:
                logger.warning(f"Could not connect to Quadrant DB: {e}")
                self.qdrant_client = None
                self.qdrant_available = False
        else:
            self.qdrant_client = None
            self.qdrant_available = False
        
        # Initialize embeddings model
        if OllamaEmbeddings:
            try:
                self.embeddings = OllamaEmbeddings(model=EMBED_MODEL)
                self.embeddings_available = True
                logger.info(f"Initialized embeddings with model: {EMBED_MODEL}")
            except Exception as e:
                logger.warning(f"Could not initialize embeddings: {e}")
                self.embeddings = None
                self.embeddings_available = False
        else:
            self.embeddings = None
            self.embeddings_available = False
        
        # Initialize chat model
        if ChatOllama:
            try:
                self.chat_model = ChatOllama(model=CHAT_MODEL)
                self.chat_available = True
                logger.info(f"Initialized chat model: {CHAT_MODEL}")
            except Exception as e:
                logger.warning(f"Could not initialize chat model: {e}")
                self.chat_model = None
                self.chat_available = False
        else:
            self.chat_model = None
            self.chat_available = False
        
        # Initialize collection if Quadrant is available
        if self.qdrant_available and self.embeddings_available:
            self._initialize_collection()
            self._index_knowledge_base()
    
    def _initialize_collection(self):
        """Initialize Quadrant collection for healthcare documents"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)
            
            if not collection_exists:
                # Create collection with appropriate vector size
                sample_embedding = self.embeddings.embed_query("test")
                vector_size = len(sample_embedding)
                
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                logger.info(f"Created Quadrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error initializing Quadrant collection: {e}")
            self.qdrant_available = False
    
    def _index_knowledge_base(self):
        """Index all documents in the knowledge base"""
        if not (self.qdrant_available and self.embeddings_available):
            logger.warning("Cannot index documents - Quadrant or embeddings not available")
            return
        
        try:
            points = []
            for doc_id, document in self.knowledge_base.documents.items():
                # Generate embedding for document content
                embedding = self.embeddings.embed_query(document.content)
                document.embedding = embedding
                
                # Create Quadrant point
                point = PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "content": document.content,
                        "document_type": document.document_type,
                        "metadata": document.metadata,
                        "indexed_at": datetime.now().isoformat()
                    }
                )
                points.append(point)
            
            # Upload points to Quadrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Indexed {len(points)} documents in Quadrant DB")
            
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
    
    def search_similar_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        if not (self.qdrant_available and self.embeddings_available):
            # Fallback to text search
            logger.info("Using fallback text search")
            docs = self.knowledge_base.search_documents(query)
            return [{"document": doc, "score": 0.5} for doc in docs[:limit]]
        
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in Quadrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )
            
            results = []
            for result in search_results:
                results.append({
                    "content": result.payload["content"],
                    "document_type": result.payload["document_type"],
                    "metadata": result.payload["metadata"],
                    "score": result.score,
                    "id": result.id
                })
            
            logger.info(f"Found {len(results)} similar documents for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def enhance_response_with_rag(self, user_query: str, base_response: str, context: Dict[str, Any]) -> str:
        """Enhance chatbot response using RAG"""
        if not self.chat_available:
            return base_response
        
        try:
            # Search for relevant documents
            relevant_docs = self.search_similar_documents(user_query, limit=3)
            
            if not relevant_docs:
                return base_response
            
            # Build context from relevant documents
            rag_context = "\n\n".join([
                f"Document {i+1} ({doc['document_type']}):\n{doc['content']}"
                for i, doc in enumerate(relevant_docs)
            ])
            
            # Create enhanced prompt
            enhanced_prompt = f"""
            You are a healthcare appointment booking assistant. Use the following context to provide accurate and helpful responses.
            
            Context from knowledge base:
            {rag_context}
            
            User query: {user_query}
            
            Current conversation context: {json.dumps(context, indent=2)}
            
            Base response: {base_response}
            
            Please provide an enhanced response that:
            1. Incorporates relevant information from the context
            2. Maintains accuracy about healthcare procedures
            3. Provides helpful guidance for appointment booking
            4. Is conversational and user-friendly
            
            Enhanced response:
            """
            
            # Generate enhanced response
            enhanced_response = self.chat_model.invoke(enhanced_prompt)
            
            logger.info("Enhanced response using RAG")
            return enhanced_response if isinstance(enhanced_response, str) else enhanced_response.content
            
        except Exception as e:
            logger.error(f"Error enhancing response with RAG: {e}")
            return base_response
    
    def get_contextual_suggestions(self, user_query: str, intent: str) -> List[str]:
        """Get contextual suggestions based on user query and intent"""
        relevant_docs = self.search_similar_documents(user_query, limit=2)
        
        suggestions = []
        
        # Intent-based suggestions
        if intent == "book_appointment":
            suggestions.extend([
                "What type of therapy service do you need?",
                "Do you have a preferred therapist gender?",
                "What date and time works best for you?",
                "Which location is most convenient?"
            ])
        elif intent == "check_availability":
            suggestions.extend([
                "Which therapist are you interested in?",
                "What date range are you considering?",
                "Do you have preferred time slots?",
                "Any specific requirements for the appointment?"
            ])
        elif intent == "find_therapist":
            suggestions.extend([
                "What type of therapy are you looking for?",
                "Do you have location preferences?",
                "Any language preferences?",
                "What qualifications are important to you?"
            ])
        
        # Add suggestions from relevant documents
        for doc in relevant_docs:
            if doc["document_type"] == "faq":
                # Extract questions from FAQ content
                faq_lines = doc["content"].split('\n')
                for line in faq_lines:
                    if line.startswith('Q:'):
                        question = line[2:].strip()
                        if question not in suggestions:
                            suggestions.append(question)
        
        return suggestions[:6]  # Limit to 6 suggestions
    
    def add_user_feedback(self, session_id: str, query: str, response: str, helpful: bool):
        """Add user feedback for improving the system"""
        feedback_data = {
            "session_id": session_id,
            "query": query,
            "response": response,
            "helpful": helpful,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store feedback (could be extended to use Quadrant for feedback storage)
        logger.info(f"User feedback: {feedback_data}")
        
        # In a real implementation, you might:
        # 1. Store feedback in a database
        # 2. Use feedback to retrain models
        # 3. Update knowledge base based on common questions


class EnhancedHealthcareChatbot:
    """
    Enhanced healthcare chatbot with RAG integration
    Combines natural language processing with vector-based knowledge retrieval
    """
    
    def __init__(self):
        self.tools_registry = HealthcareToolsRegistry()
        self.conversation_manager = ConversationManager(self.tools_registry)
        self.rag_system = QuadrantRAGSystem()
        
        logger.info("Enhanced Healthcare Chatbot initialized with RAG system")
    
    def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Process user message with RAG enhancement"""
        
        # Get base response from conversation manager
        base_response = self.conversation_manager.process_user_input(session_id, user_message)
        
        # Get conversation context
        context = self.conversation_manager.get_conversation_summary(session_id)
        
        # Enhance response with RAG if appropriate
        if base_response.get("status") in ["collecting_parameters", "ready_for_execution"]:
            enhanced_message = self.rag_system.enhance_response_with_rag(
                user_message, 
                base_response.get("message", ""),
                context or {}
            )
            base_response["message"] = enhanced_message
        
        # Add contextual suggestions
        intent = context.get("current_intent") if context else "unknown"
        suggestions = self.rag_system.get_contextual_suggestions(user_message, intent)
        base_response["suggestions"] = suggestions
        
        # Add knowledge context for debugging
        relevant_docs = self.rag_system.search_similar_documents(user_message, limit=2)
        base_response["knowledge_context"] = [
            {"type": doc["document_type"], "score": doc["score"]} 
            for doc in relevant_docs
        ]
        
        return base_response
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get enhanced session summary"""
        base_summary = self.conversation_manager.get_conversation_summary(session_id)
        if base_summary:
            # Could add RAG-based insights here
            base_summary["rag_available"] = self.rag_system.qdrant_available
            base_summary["embeddings_available"] = self.rag_system.embeddings_available
        
        return base_summary
    
    def provide_feedback(self, session_id: str, helpful: bool):
        """Provide feedback on the last interaction"""
        context = self.conversation_manager.get_conversation_summary(session_id)
        if context and context.get("conversation_length", 0) > 0:
            # Get last interaction
            last_history = context.get("conversation_history", [])
            if len(last_history) >= 2:
                last_query = last_history[-2].get("content", "")
                last_response = last_history[-1].get("content", "")
                
                self.rag_system.add_user_feedback(session_id, last_query, last_response, helpful)
                return {"status": "success", "message": "Thank you for your feedback!"}
        
        return {"status": "error", "message": "No recent interaction found to provide feedback on."}


# Example usage and testing
if __name__ == "__main__":
    # Initialize enhanced chatbot
    chatbot = EnhancedHealthcareChatbot()
    
    # Test conversation
    session_id = "test_rag_session"
    
    test_queries = [
        "I need to book an appointment",
        "I'm looking for a female therapist who speaks Spanish",
        "What's the availability for next Wednesday?",
        "How far in advance can I book appointments?"
    ]
    
    print("Testing Enhanced Healthcare Chatbot with RAG:")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        response = chatbot.process_message(session_id, query)
        
        print(f"Status: {response.get('status')}")
        print(f"Response: {response.get('message')}")
        
        if response.get('suggestions'):
            print("Suggestions:")
            for suggestion in response.get('suggestions', []):
                print(f"  - {suggestion}")
        
        if response.get('knowledge_context'):
            print("Knowledge used:")
            for ctx in response.get('knowledge_context', []):
                print(f"  - {ctx['type']} (score: {ctx['score']:.3f})")
        
        print("-" * 30)
    
    # Test session summary
    summary = chatbot.get_session_summary(session_id)
    if summary:
        print(f"\nSession Summary:")
        print(f"Intent: {summary.get('current_intent')}")
        print(f"Tool: {summary.get('selected_tool')}")
        print(f"Parameters: {summary.get('collected_parameters')}")
        print(f"RAG Available: {summary.get('rag_available')}")
