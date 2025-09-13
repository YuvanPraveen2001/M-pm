"""
Healthcare Database Schema RAG System
Processes and stores database schema information with relationships in Qdrant
for intelligent SQL query generation based on user queries.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import re
import asyncio

# Import model configuration
from model_config import EMBED_MODEL, CHAT_MODEL, get_embedding_model_config, get_chat_model_config

# Qdrant and embedding imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.chat_models import ChatOllama
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
except ImportError:
    print("Warning: Required packages not installed. Install with: pip install qdrant-client sentence-transformers langchain-community")
    QdrantClient = None
    SentenceTransformer = None
    OllamaEmbeddings = None
    ChatOllama = None

logger = logging.getLogger(__name__)


@dataclass
class TableSchema:
    """Represents a database table schema with relationships"""
    table_name: str
    description: str = ""
    columns: List[Dict[str, Any]] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    referenced_by: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    business_concepts: List[str] = field(default_factory=list)


@dataclass
class SchemaQueryResult:
    """Result from schema retrieval"""
    tables: List[TableSchema]
    relationships: List[Dict[str, Any]]
    suggested_joins: List[str]
    confidence_score: float


class HealthcareSchemaRAG:
    """RAG system for healthcare database schema"""
    
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333, use_memory: bool = True):
        """Initialize the Healthcare Schema RAG system (default to memory mode for Mac compatibility)"""
        print("🔍 DEBUG: Initializing healthcare schema RAG system...")
        
        self.collection_name = "healthcare_schema"
        self.use_memory = use_memory
        
        if use_memory:
            # Use in-memory mode for better Mac compatibility
            print("💾 Using in-memory Qdrant mode (recommended for Mac)")
            if QdrantClient is not None:
                self.client = QdrantClient(":memory:")
            else:
                print("⚠️ Warning: Qdrant client not available, using fallback mode")
                self.client = None
        else:
            try:
                # Try to connect to local Qdrant server
                if QdrantClient is not None:
                    self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
                    print(f"✅ Connected to Qdrant at {qdrant_host}:{qdrant_port}")
                else:
                    print("⚠️ Warning: Qdrant client not available")
                    self.client = None
            except Exception as e:
                print(f"⚠️ Warning: Could not connect to Qdrant server: {str(e)}")
                print("💾 Falling back to in-memory mode")
                if QdrantClient is not None:
                    self.client = QdrantClient(":memory:")
                else:
                    self.client = None
                self.use_memory = True
        
        # Initialize embedding model - try Ollama first, fallback to SentenceTransformer
        try:
            if OllamaEmbeddings is not None:
                self.embedding_model = OllamaEmbeddings(model=EMBED_MODEL)
                self.embedding_type = "ollama"
                print(f"✅ Ollama embedding model loaded: {EMBED_MODEL}")
            else:
                raise ImportError("OllamaEmbeddings not available")
        except Exception as e:
            print(f"⚠️ Warning: Could not load Ollama embedding model: {e}")
            try:
                if SentenceTransformer is not None:
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.embedding_type = "sentence_transformer"
                    print("✅ Fallback embedding model loaded (SentenceTransformer)")
                else:
                    print("⚠️ SentenceTransformer not available")
                    self.embedding_model = None
                    self.embedding_type = None
            except Exception as e2:
                print(f"⚠️ Warning: Could not load fallback embedding model: {e2}")
                self.embedding_model = None
                self.embedding_type = None

        # Initialize chat model for SQL generation
        try:
            if ChatOllama is not None:
                self.chat_model = ChatOllama(model=CHAT_MODEL, temperature=0.1)
                print(f"✅ Ollama chat model loaded: {CHAT_MODEL}")
                self.chat_available = True
            else:
                print("⚠️ ChatOllama not available")
                self.chat_model = None
                self.chat_available = False
        except Exception as e:
            print(f"⚠️ Warning: Could not load Ollama chat model: {e}")
            self.chat_model = None
            self.chat_available = False
        
        # Initialize schema data
        self.healthcare_schema = self._parse_healthcare_schema()
        
        # Try to index schema if components are available
        if self.client and self.embedding_model:
            try:
                self._index_schema_in_qdrant()
                print("✅ Schema indexed successfully")
            except Exception as e:
                print(f"⚠️ Warning: Could not index schema: {str(e)}")
        
        print("✅ DEBUG: Healthcare schema RAG system ready")

    def index_schema_file(self, schema_file_path: str) -> bool:
        """Index a schema file in Qdrant (public method for setup scripts)"""
        try:
            # For now, we're using the built-in schema definitions
            # This method can be extended to parse actual SQL files
            return True
        except Exception as e:
            print(f"❌ Error indexing schema file: {str(e)}")
            return False
    
    def _parse_healthcare_schema(self) -> Dict[str, TableSchema]:
        """Parse the healthcare database schema into structured format"""
        
        # Define the healthcare database schema with business concepts
        schema_definitions = {
            "Patient": TableSchema(
                table_name="Patient",
                description="Central patient information including demographics and contact details",
                columns=[
                    {"name": "PatientId", "type": "int", "is_primary": True, "description": "Unique patient identifier"},
                    {"name": "FirstName", "type": "nvarchar(250)", "description": "Patient first name"},
                    {"name": "LastName", "type": "nvarchar(250)", "description": "Patient last name"},
                    {"name": "MiddleName", "type": "nvarchar(250)", "description": "Patient middle name"},
                    {"name": "DOB", "type": "date", "description": "Date of birth"},
                    {"name": "Gender", "type": "int", "description": "Gender ID (references Gender table)"},
                    {"name": "Email", "type": "varchar(100)", "description": "Patient email address"},
                    {"name": "SiteId", "type": "int", "description": "Site where patient is treated"},
                    {"name": "IsActive", "type": "bit", "description": "Whether patient is currently active"}
                ],
                primary_keys=["PatientId"],
                foreign_keys=[
                    {"column": "Gender", "references_table": "Gender", "references_column": "GenderID"},
                    {"column": "SiteId", "references_table": "Site", "references_column": "SiteId"}
                ],
                business_concepts=["patient", "client", "individual", "person", "demographics", "contact info"]
            ),
            
            "Employee": TableSchema(
                table_name="Employee",
                description="Healthcare providers and staff information including therapists, supervisors, and admin staff",
                columns=[
                    {"name": "EmployeeId", "type": "int", "is_primary": True, "description": "Unique employee identifier"},
                    {"name": "FirstName", "type": "varchar(250)", "description": "Employee first name"},
                    {"name": "LastName", "type": "varchar(250)", "description": "Employee last name"},
                    {"name": "MiddleName", "type": "varchar(250)", "description": "Employee middle name"},
                    {"name": "Title", "type": "varchar(250)", "description": "Professional title"},
                    {"name": "NPI", "type": "varchar(250)", "description": "National Provider Identifier"},
                    {"name": "Email", "type": "varchar(255)", "description": "Employee email address"},
                    {"name": "PhoneOffice", "type": "varchar(20)", "description": "Office phone number"},
                    {"name": "PhoneCell", "type": "varchar(250)", "description": "Cell phone number"},
                    {"name": "HiringDate", "type": "datetime", "description": "Date employee was hired"},
                    {"name": "TerminationDate", "type": "datetime", "description": "Date employee was terminated"},
                    {"name": "IsSupervisor", "type": "bit", "description": "Whether employee is a supervisor"},
                    {"name": "Active", "type": "bit", "description": "Whether employee is currently active"},
                    {"name": "SiteId", "type": "int", "description": "Site where employee works"},
                    {"name": "TreatmentTypeId", "type": "int", "description": "Type of treatment employee provides"}
                ],
                primary_keys=["EmployeeId"],
                foreign_keys=[
                    {"column": "SiteId", "references_table": "Site", "references_column": "SiteId"},
                    {"column": "TreatmentTypeId", "references_table": "TreatmentType", "references_column": "TreatmentTypeid"}
                ],
                business_concepts=["employee", "staff", "therapist", "provider", "clinician", "supervisor", "doctor", "practitioner"]
            ),
            
            "Appointment": TableSchema(
                table_name="Appointment",
                description="Scheduled appointments between patients and healthcare providers",
                columns=[
                    {"name": "AppointmentId", "type": "int", "is_primary": True, "description": "Unique appointment identifier"},
                    {"name": "PatientId", "type": "int", "description": "Patient receiving service"},
                    {"name": "EmployeeId", "type": "int", "description": "Provider delivering service"},
                    {"name": "ScheduledDate", "type": "datetime", "description": "Scheduled date and time"},
                    {"name": "ScheduledMinutes", "type": "int", "description": "Duration in minutes"},
                    {"name": "AppointmentStatusId", "type": "int", "description": "Current appointment status"},
                    {"name": "LocationId", "type": "int", "description": "Where appointment takes place"},
                    {"name": "ServiceTypeId", "type": "int", "description": "Type of service being provided"},
                    {"name": "AuthId", "type": "int", "description": "Authorization for this appointment"},
                    {"name": "Notes", "type": "nvarchar(4000)", "description": "Appointment notes"},
                    {"name": "RenderedDate", "type": "datetime", "description": "Actual date service was provided"},
                    {"name": "RenderedMinutes", "type": "int", "description": "Actual duration of service"}
                ],
                primary_keys=["AppointmentId"],
                foreign_keys=[
                    {"column": "PatientId", "references_table": "Patient", "references_column": "PatientId"},
                    {"column": "EmployeeId", "references_table": "Employee", "references_column": "EmployeeId"},
                    {"column": "LocationId", "references_table": "Location", "references_column": "LocationId"},
                    {"column": "ServiceTypeId", "references_table": "ServiceType", "references_column": "ServiceTypeId"},
                    {"column": "AuthId", "references_table": "Auth", "references_column": "AuthId"}
                ],
                business_concepts=["appointment", "session", "visit", "meeting", "service", "treatment", "therapy", "scheduled", "booking"]
            ),
            
            "Auth": TableSchema(
                table_name="Auth",
                description="Authorization records for patient treatments and services",
                columns=[
                    {"name": "AuthId", "type": "int", "is_primary": True, "description": "Unique authorization identifier"},
                    {"name": "PatientId", "type": "int", "description": "Patient this authorization covers"},
                    {"name": "AuthNumber", "type": "varchar(250)", "description": "Authorization number from insurance"},
                    {"name": "StartDate", "type": "datetime", "description": "Authorization start date"},
                    {"name": "EndDate", "type": "datetime", "description": "Authorization end date"},
                    {"name": "TreatmentTypeId", "type": "int", "description": "Type of treatment authorized"},
                    {"name": "FundingSourceID", "type": "int", "description": "Insurance or funding source"},
                    {"name": "Diagnosis1", "type": "varchar(100)", "description": "Primary diagnosis"},
                    {"name": "SupervisorId", "type": "int", "description": "Supervising provider"},
                    {"name": "Valid", "type": "bit", "description": "Whether authorization is valid"}
                ],
                primary_keys=["AuthId"],
                foreign_keys=[
                    {"column": "PatientId", "references_table": "Patient", "references_column": "PatientId"},
                    {"column": "TreatmentTypeId", "references_table": "TreatmentType", "references_column": "TreatmentTypeid"}
                ],
                business_concepts=["authorization", "insurance", "approval", "coverage", "funding", "diagnosis", "treatment plan"]
            ),
            
            "Location": TableSchema(
                table_name="Location",
                description="Physical locations where services are provided",
                columns=[
                    {"name": "LocationId", "type": "int", "is_primary": True, "description": "Unique location identifier"},
                    {"name": "Name", "type": "varchar(250)", "description": "Location name"},
                    {"name": "Address1", "type": "varchar(1000)", "description": "Primary address"},
                    {"name": "City", "type": "varchar(250)", "description": "City"},
                    {"name": "StateId", "type": "int", "description": "State"},
                    {"name": "ZipCode", "type": "varchar(10)", "description": "ZIP code"},
                    {"name": "Phone", "type": "varchar(20)", "description": "Location phone number"},
                    {"name": "Active", "type": "bit", "description": "Whether location is active"}
                ],
                primary_keys=["LocationId"],
                business_concepts=["location", "address", "site", "facility", "clinic", "office", "place", "where"]
            ),
            
            "ServiceType": TableSchema(
                table_name="ServiceType",
                description="Types of healthcare services that can be provided",
                columns=[
                    {"name": "ServiceTypeId", "type": "int", "is_primary": True, "description": "Unique service type identifier"},
                    {"name": "ServiceTypeDesc", "type": "varchar(250)", "description": "Service type description"},
                    {"name": "TreatmentTypeId", "type": "int", "description": "Related treatment type"},
                    {"name": "IsBillable", "type": "bit", "description": "Whether service is billable"},
                    {"name": "IsActive", "type": "bit", "description": "Whether service type is active"}
                ],
                primary_keys=["ServiceTypeId"],
                foreign_keys=[
                    {"column": "TreatmentTypeId", "references_table": "TreatmentType", "references_column": "TreatmentTypeid"}
                ],
                business_concepts=["service", "treatment", "therapy", "intervention", "procedure", "session type"]
            ),
            
            "EmployeeAvailabilityDateTime": TableSchema(
                table_name="EmployeeAvailabilityDateTime",
                description="Employee availability schedules and time slots",
                columns=[
                    {"name": "EmployeeAvailabilityDateTimeId", "type": "int", "is_primary": True, "description": "Unique availability record identifier"},
                    {"name": "EmployeeId", "type": "int", "description": "Employee this availability belongs to"},
                    {"name": "WeekDay", "type": "int", "description": "Day of week (1=Monday, 7=Sunday)"},
                    {"name": "AvailableFrom", "type": "time", "description": "Start time of availability"},
                    {"name": "AvailableTo", "type": "time", "description": "End time of availability"},
                    {"name": "AvailabilityDateFrom", "type": "datetime", "description": "Start date of availability period"},
                    {"name": "AvailabilityDateTo", "type": "datetime", "description": "End date of availability period"}
                ],
                primary_keys=["EmployeeAvailabilityDateTimeId"],
                foreign_keys=[
                    {"column": "EmployeeId", "references_table": "Employee", "references_column": "EmployeeId"}
                ],
                business_concepts=["availability", "schedule", "free time", "open slots", "calendar", "time slots", "when available"]
            )
        }
        
        # Add referenced_by relationships
        for table_name, table_schema in schema_definitions.items():
            for fk in table_schema.foreign_keys:
                ref_table = fk["references_table"]
                if ref_table in schema_definitions:
                    schema_definitions[ref_table].referenced_by.append({
                        "table": table_name,
                        "column": fk["column"],
                        "references_column": fk["references_column"]
                    })
        
        return schema_definitions
    
    def _index_schema_in_qdrant(self):
        """Index the schema information in Qdrant for retrieval"""
        try:
            # Create collection if it doesn't exist
            try:
                self.client.delete_collection(self.collection_name)
            except:
                pass
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            
            points = []
            point_id = 1
            
            for table_name, table_schema in self.healthcare_schema.items():
                # Create comprehensive text for embedding
                text_content = self._create_table_text_representation(table_schema)
                
                # Generate embedding
                embedding = self._get_embedding(text_content)
                
                # Create point with metadata
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "table_name": table_name,
                        "description": table_schema.description,
                        "business_concepts": table_schema.business_concepts,
                        "columns": [col["name"] for col in table_schema.columns],
                        "text_content": text_content,
                        "primary_keys": table_schema.primary_keys,
                        "foreign_keys": table_schema.foreign_keys,
                        "referenced_by": table_schema.referenced_by
                    }
                )
                points.append(point)
                point_id += 1
        except Exception as e:
            print(f"⚠️ Warning: Error indexing schema: {e}")

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using the configured model"""
        if not self.embedding_model:
            return [0.0] * 384  # Default dimension for fallback
        
        try:
            if self.embedding_type == "ollama":
                # Ollama embeddings
                embedding = self.embedding_model.embed_query(text)
                return embedding
            elif self.embedding_type == "sentence_transformer":
                # SentenceTransformer embeddings
                embedding = self.embedding_model.encode(text).tolist()
                return embedding
            else:
                return [0.0] * 384
        except Exception as e:
            print(f"⚠️ Warning: Could not generate embedding: {e}")
            return [0.0] * 384

    def _create_table_text_representation(self, table_schema: TableSchema) -> str:
        """Create a comprehensive text representation of a table schema"""
        text_parts = [
            f"Table {table_schema.table_name}: {table_schema.description}",
            f"Columns: {', '.join([col['name'] for col in table_schema.columns])}",
            f"Primary keys: {', '.join(table_schema.primary_keys) if table_schema.primary_keys else 'None'}"
        ]
        
        if table_schema.foreign_keys:
            fk_desc = [f"{fk['column']} references {fk['references_table']}.{fk['references_column']}" 
                      for fk in table_schema.foreign_keys]
            text_parts.append(f"Foreign keys: {', '.join(fk_desc)}")
        
        if table_schema.business_concepts:
            text_parts.append(f"Business concepts: {', '.join(table_schema.business_concepts)}")
        
        return ". ".join(text_parts)

    def _complete_indexing(self, points: List) -> None:
        """Complete the indexing process by uploading points to Qdrant"""
        try:
            if points:
                # Upload points to Qdrant
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                print(f"✅ Indexed {len(points)} schema points in Qdrant")
            else:
                print("⚠️ No points to index")
        except Exception as e:
            print(f"⚠️ Warning: Error uploading points to Qdrant: {e}")

    def retrieve_relevant_schema(self, query: str, top_k: int = 5) -> SchemaQueryResult:
        """Retrieve relevant schema information based on query"""
        if not self.client or not self.embedding_model:
            # Fallback: return all schema information
            return SchemaQueryResult(
                tables=list(self.healthcare_schema.values()),
                relationships=[],
                suggested_joins=[],
                confidence_score=0.5
            )
        
        try:
            query_embedding = self._get_embedding(query)
            
            # Search for relevant schema components
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k
            )
            
            # Process results and build schema result
            relevant_tables = []
            table_names = set()
            confidence_scores = []
            
            for result in search_results:
                table_name = result.payload.get("table_name")
                if table_name and table_name in self.healthcare_schema:
                    if table_name not in table_names:
                        relevant_tables.append(self.healthcare_schema[table_name])
                        table_names.add(table_name)
                    confidence_scores.append(result.score)
            
            # Generate suggested joins
            suggested_joins = self._generate_join_suggestions(list(table_names))
            
            # Calculate overall confidence
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            return SchemaQueryResult(
                tables=relevant_tables,
                relationships=self._extract_relationships(relevant_tables),
                suggested_joins=suggested_joins,
                confidence_score=avg_confidence
            )
            
        except Exception as e:
            print(f"⚠️ Warning: Error retrieving schema: {e}")
            # Fallback to all tables
            return SchemaQueryResult(
                tables=list(self.healthcare_schema.values()),
                relationships=[],
                suggested_joins=[],
                confidence_score=0.3
            )
            for ref in table_schema.referenced_by:
                ref_info.append(f"Referenced by {ref['table']}.{ref['column']}")
            text_parts.append(f"Referenced by: {'; '.join(ref_info)}")
        
        return "\n".join(text_parts)
    
    def retrieve_relevant_schema(self, query: str, top_k: int = 5) -> SchemaQueryResult:
        """Retrieve relevant schema based on query"""
        if not self.client or not self.embedding_model:
            print("⚠️ Warning: RAG components not available, using fallback schema")
            return self._get_fallback_schema_result(query)
        
        try:
            # Generate embedding for user query
            query_embedding = self._get_embedding(query)
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k * 2,  # Get more results to filter
                score_threshold=0.2  # Lower threshold to get more results
            )
            
            print(f"🔍 DEBUG: Found {len(search_results)} search results for query: {query}")
            
            # Process results and extract unique tables
            relevant_tables = {}
            relationships = []
            
            for result in search_results:
                table_name = result.payload.get("table_name")
                print(f"🔍 DEBUG: Processing result for table: {table_name}, score: {result.score}")
                if table_name and table_name in self.healthcare_schema:
                    if table_name not in relevant_tables:
                        relevant_tables[table_name] = self.healthcare_schema[table_name]
                        
                        # Add relationships for this table
                        table_schema = self.healthcare_schema[table_name]
                        for fk in table_schema.foreign_keys:
                            relationships.append({
                                "from_table": table_name,
                                "from_column": fk["column"],
                                "to_table": fk["references_table"],
                                "to_column": fk["references_column"],
                                "relationship_type": "foreign_key"
                            })
            
            # If no tables found via embedding search, use fallback
            if not relevant_tables:
                print("⚠️ No tables found via embedding search, using fallback")
                return self._get_fallback_schema_result(query)
            
            # Generate suggested joins
            suggested_joins = self._generate_suggested_joins(list(relevant_tables.keys()))
            
            # Calculate overall confidence
            avg_confidence = sum(result.score for result in search_results[:top_k]) / min(len(search_results), top_k) if search_results else 0.0
            
            return SchemaQueryResult(
                tables=list(relevant_tables.values()),
                relationships=relationships,
                suggested_joins=suggested_joins,
                confidence_score=avg_confidence
            )
            
        except Exception as e:
            print(f"⚠️ Warning: Error retrieving schema: {e}")
            return self._get_fallback_schema_result(query)
    
    def _get_fallback_schema_result(self, query: str) -> SchemaQueryResult:
        """Provide fallback schema when RAG is not available"""
        query_lower = query.lower()
        relevant_tables = []
        
        # Simple keyword matching for common queries
        if any(word in query_lower for word in ['patient', 'appointment', 'booking']):
            relevant_tables.extend(['Patient', 'Appointment'])
        
        if any(word in query_lower for word in ['employee', 'provider', 'therapist', 'doctor']):
            relevant_tables.append('Employee')
        
        if any(word in query_lower for word in ['auth', 'authorization']):
            relevant_tables.append('Auth')
        
        if any(word in query_lower for word in ['location', 'office']):
            relevant_tables.append('Location')
        
        if any(word in query_lower for word in ['service', 'treatment']):
            relevant_tables.append('ServiceType')
        
        if any(word in query_lower for word in ['available', 'availability', 'schedule']):
            relevant_tables.extend(['Employee', 'EmployeeAvailabilityDateTime'])
        
        # Remove duplicates and get table schemas
        unique_tables = list(set(relevant_tables))
        if not unique_tables:
            unique_tables = ['Patient', 'Employee', 'Appointment']  # Default tables
        
        tables = []
        relationships = []
        
        for table_name in unique_tables:
            if table_name in self.healthcare_schema:
                table_schema = self.healthcare_schema[table_name]
                tables.append(table_schema)
                
                # Add relationships for this table
                for fk in table_schema.foreign_keys:
                    relationships.append({
                        "from_table": table_name,
                        "from_column": fk["column"],
                        "to_table": fk["references_table"],
                        "to_column": fk["references_column"],
                        "relationship_type": "foreign_key"
                    })
        
        # Generate suggested joins
        suggested_joins = self._generate_suggested_joins(unique_tables)
        
        return SchemaQueryResult(
            tables=tables,
            relationships=relationships,
            suggested_joins=suggested_joins,
            confidence_score=0.7  # Default confidence for fallback
        )

    def _fallback_schema_retrieval(self, user_query: str) -> SchemaQueryResult:
        """Fallback schema retrieval using keyword matching"""
        query_lower = user_query.lower()
        relevant_tables = {}
        
        # Simple keyword matching
        for table_name, table_schema in self.healthcare_schema.items():
            # Check if query matches table concepts
            for concept in table_schema.business_concepts:
                if concept.lower() in query_lower:
                    relevant_tables[table_name] = table_schema
                    break
            
            # Check if query matches table name or description
            if (table_name.lower() in query_lower or 
                any(word in table_schema.description.lower() for word in query_lower.split())):
                relevant_tables[table_name] = table_schema
        
        # If no specific matches, include core tables
        if not relevant_tables:
            core_tables = ["Patient", "Employee", "Appointment"]
            for table_name in core_tables:
                if table_name in self.healthcare_schema:
                    relevant_tables[table_name] = self.healthcare_schema[table_name]
        
        # Generate relationships and joins
        relationships = []
        for table_name, table_schema in relevant_tables.items():
            for fk in table_schema.foreign_keys:
                relationships.append({
                    "from_table": table_name,
                    "from_column": fk["column"],
                    "to_table": fk["references_table"],
                    "to_column": fk["references_column"],
                    "relationship_type": "foreign_key"
                })
        
        suggested_joins = self._generate_suggested_joins(list(relevant_tables.keys()))
        
        return SchemaQueryResult(
            tables=list(relevant_tables.values()),
            relationships=relationships,
            suggested_joins=suggested_joins,
            confidence_score=0.7  # Medium confidence for fallback
        )
    
    def _generate_suggested_joins(self, table_names: List[str]) -> List[str]:
        """Generate suggested JOIN clauses for the given tables"""
        joins = []
        
        # Common join patterns in healthcare data
        join_patterns = [
            ("Patient", "Appointment", "p.PatientId = a.PatientId"),
            ("Employee", "Appointment", "e.EmployeeId = a.EmployeeId"),
            ("Location", "Appointment", "l.LocationId = a.LocationId"),
            ("Auth", "Appointment", "auth.AuthId = a.AuthId"),
            ("ServiceType", "Appointment", "st.ServiceTypeId = a.ServiceTypeId"),
            ("Patient", "Auth", "p.PatientId = auth.PatientId"),
            ("Employee", "EmployeeAvailabilityDateTime", "e.EmployeeId = ead.EmployeeId")
        ]
        
        for table1, table2, join_condition in join_patterns:
            if table1 in table_names and table2 in table_names:
                joins.append(f"JOIN {table2} ON {join_condition}")
        
        return joins
    
    def generate_sql_with_schema(self, user_query: str, schema_result: SchemaQueryResult) -> str:
        """Generate SQL query using the retrieved schema information and LLM"""
        
        # If chat model is available, use LLM for SQL generation
        if self.chat_available and self.chat_model:
            return self._generate_sql_with_llm(user_query, schema_result)
        else:
            # Fallback to rule-based generation
            return self._generate_sql_rule_based(user_query, schema_result)
    
    def _generate_sql_with_llm(self, user_query: str, schema_result: SchemaQueryResult) -> str:
        """Generate SQL using LLM with schema context"""
        try:
            # Prepare schema context
            schema_context = self._format_schema_for_llm(schema_result)
            
            # Create prompt template
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", """You are a SQL expert for a healthcare database. Generate a precise SQL query based on the user's request and the provided schema information.

Database Schema Context:
{schema_context}

Rules:
1. Only use tables and columns that exist in the schema
2. Use proper JOIN syntax when accessing multiple tables
3. Be precise with column names and table names
4. Include appropriate WHERE clauses for filtering
5. Use clear and readable SQL formatting
6. Return only the SQL query without explanations

Example patterns:
- For availability queries: Use Employee, Location, and date-based filtering
- For appointments: Use Appointment table with Patient and Employee joins
- For employee searches: Use Employee table with Location joins if needed

Generate a SQL query for: {user_query}"""),
                ("human", "{user_query}")
            ])
            
            # Generate SQL
            chain = prompt_template | self.chat_model | StrOutputParser()
            
            sql_query = chain.invoke({
                "user_query": user_query,
                "schema_context": schema_context
            })
            
            # Clean up the SQL query (remove markdown formatting if present)
            sql_query = sql_query.strip()
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except Exception as e:
            print(f"⚠️ Warning: LLM SQL generation failed: {e}")
            # Fallback to rule-based generation
            return self._generate_sql_rule_based(user_query, schema_result)
    
    def _format_schema_for_llm(self, schema_result: SchemaQueryResult) -> str:
        """Format schema information for LLM prompt"""
        schema_text = "Database Tables and Structure:\n\n"
        
        for table in schema_result.tables:
            schema_text += f"Table: {table.table_name}\n"
            schema_text += f"Description: {table.description}\n"
            schema_text += "Columns:\n"
            
            for col in table.columns:
                col_info = f"  - {col['name']} ({col['type']}"
                if col.get('nullable', True):
                    col_info += ", nullable"
                if col.get('primary_key', False):
                    col_info += ", PRIMARY KEY"
                col_info += ")"
                schema_text += col_info + "\n"
            
            if table.foreign_keys:
                schema_text += "Foreign Keys:\n"
                for fk in table.foreign_keys:
                    schema_text += f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}\n"
            
            schema_text += "\n"
        
        if schema_result.suggested_joins:
            schema_text += "Common Join Patterns:\n"
            for join in schema_result.suggested_joins:
                schema_text += f"  - {join}\n"
        
        return schema_text
    
    def _generate_sql_rule_based(self, user_query: str, schema_result: SchemaQueryResult) -> str:
        """Generate SQL query using rule-based approach (fallback)"""
        query_lower = user_query.lower()
        
        # Determine the main table based on the query
        main_table = self._determine_main_table(query_lower, schema_result.tables)
        
        # Build SELECT clause
        select_columns = self._determine_select_columns(query_lower, schema_result.tables)
        
        # Build FROM and JOIN clauses
        from_clause, joins = self._build_joins(main_table, schema_result)
        
        # Build WHERE clause
        where_conditions = self._build_where_conditions(query_lower, schema_result.tables)
        
        # Construct the final SQL
        sql_parts = [f"SELECT {', '.join(select_columns)}"]
        sql_parts.append(f"FROM {main_table}")
        
        for join in joins:
            sql_parts.append(join)
        
        if where_conditions:
            sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
        
        return "\n".join(sql_parts)
    
    def _determine_main_table(self, query_lower: str, tables: List[TableSchema]) -> str:
        """Determine the main table for the query"""
        # Priority order based on common query patterns
        priority_order = ["Appointment", "Patient", "Employee", "Auth", "Location"]
        
        for table_name in priority_order:
            if any(t.table_name == table_name for t in tables):
                return table_name
        
        # Return first table if no priority match
        return tables[0].table_name if tables else "Patient"
    
    def _determine_select_columns(self, query_lower: str, tables: List[TableSchema]) -> List[str]:
        """Determine which columns to select based on the query"""
        columns = []
        
        # Default columns for common queries
        for table in tables:
            if table.table_name == "Patient":
                columns.extend(["p.PatientId", "p.FirstName", "p.LastName"])
            elif table.table_name == "Employee":
                columns.extend(["e.EmployeeId", "e.FirstName", "e.LastName", "e.Title"])
            elif table.table_name == "Appointment":
                columns.extend(["a.AppointmentId", "a.ScheduledDate", "a.ScheduledMinutes"])
        
        # If no specific columns, use basic ones
        if not columns:
            main_table = tables[0] if tables else None
            if main_table:
                id_column = next((col["name"] for col in main_table.columns if col.get("is_primary")), None)
                if id_column:
                    columns.append(f"{main_table.table_name[0].lower()}.{id_column}")
        
        return columns if columns else ["*"]
    
    def _build_joins(self, main_table: str, schema_result: SchemaQueryResult) -> Tuple[str, List[str]]:
        """Build JOIN clauses based on the schema relationships"""
        joins = []
        table_aliases = {main_table: main_table[0].lower()}
        
        for relationship in schema_result.relationships:
            from_table = relationship["from_table"]
            to_table = relationship["to_table"]
            
            if from_table == main_table:
                alias = to_table[0].lower()
                table_aliases[to_table] = alias
                join_clause = f"LEFT JOIN {to_table} {alias} ON {table_aliases[from_table]}.{relationship['from_column']} = {alias}.{relationship['to_column']}"
                joins.append(join_clause)
        
        return main_table + " " + table_aliases[main_table], joins
    
    def _build_where_conditions(self, query_lower: str, tables: List[TableSchema]) -> List[str]:
        """Build WHERE conditions based on the query"""
        conditions = []
        
        # Extract names from query
        if "john" in query_lower:
            conditions.append("(p.FirstName LIKE '%John%' OR e.FirstName LIKE '%John%')")
        
        # Extract date references
        if "today" in query_lower:
            conditions.append("CAST(a.ScheduledDate AS DATE) = CAST(GETDATE() AS DATE)")
        elif "tomorrow" in query_lower:
            conditions.append("CAST(a.ScheduledDate AS DATE) = CAST(DATEADD(day, 1, GETDATE()) AS DATE)")
        elif "wednesday" in query_lower:
            conditions.append("DATEPART(weekday, a.ScheduledDate) = 4")  # Wednesday
        
        # Add active filters
        conditions.append("p.IsActive = 1")
        conditions.append("e.Active = 1")
        
        return conditions


# Singleton instance for the healthcare schema RAG
healthcare_schema_rag = None

def get_healthcare_schema_rag() -> HealthcareSchemaRAG:
    """Get or create the healthcare schema RAG instance"""
    global healthcare_schema_rag
    if healthcare_schema_rag is None:
        healthcare_schema_rag = HealthcareSchemaRAG()
    return healthcare_schema_rag
