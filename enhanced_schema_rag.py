"""
Enhanced Healthcare Database Schema RAG System
Retrieves complete table schemas directly from the database to ensure accurate column names
Uses Ollama LLM for intelligent SQL query generation
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import re

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
class DatabaseTable:
    """Represents a complete database table schema"""
    table_name: str
    schema_name: str = "dbo"
    columns: List[Dict[str, Any]] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    description: str = ""
    business_concepts: List[str] = field(default_factory=list)


@dataclass
class EnhancedSchemaResult:
    """Result from enhanced schema retrieval"""
    tables: List[DatabaseTable]
    complete_schema: Dict[str, Dict]
    suggested_joins: List[str]
    confidence_score: float


class EnhancedSchemaRAG:
    """Enhanced RAG system that retrieves complete table schemas from database"""
    
    def __init__(self, db_manager, use_memory: bool = True):
        """Initialize the Enhanced Schema RAG system"""
        print("🔍 DEBUG: Initializing enhanced healthcare schema RAG system...")
        
        self.db_manager = db_manager
        self.collection_name = "enhanced_healthcare_schema"
        self.use_memory = use_memory
        
        # Initialize Qdrant client
        if use_memory:
            print("💾 Using in-memory Qdrant mode (recommended for Mac)")
            if QdrantClient is not None:
                self.client = QdrantClient(":memory:")
            else:
                print("⚠️ Warning: Qdrant client not available, using fallback mode")
                self.client = None
        else:
            self.client = None
        
        # Initialize embedding model
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
        
        # Retrieve and cache complete database schema
        self.complete_schema = self._retrieve_complete_database_schema()
        
        # Try to index schema if components are available
        if self.client and self.embedding_model and self.complete_schema:
            try:
                self._index_complete_schema()
                print("✅ Complete database schema indexed successfully")
            except Exception as e:
                print(f"⚠️ Warning: Could not index complete schema: {str(e)}")
        
        print("✅ DEBUG: Enhanced healthcare schema RAG system ready")

    def _retrieve_complete_database_schema(self) -> Dict[str, DatabaseTable]:
        """Retrieve complete table schemas directly from the database"""
        print("🔍 Retrieving complete database schema from SQL Server...")
        
        # Query to get all table information
        schema_query = """
        SELECT 
            t.TABLE_SCHEMA,
            t.TABLE_NAME,
            t.TABLE_TYPE,
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.ORDINAL_POSITION,
            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as IS_PRIMARY_KEY,
            CASE WHEN fk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as IS_FOREIGN_KEY,
            fk.REFERENCED_TABLE_SCHEMA,
            fk.REFERENCED_TABLE_NAME,
            fk.REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLES t
        LEFT JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
        LEFT JOIN (
            SELECT 
                ku.TABLE_SCHEMA,
                ku.TABLE_NAME,
                ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                AND tc.TABLE_SCHEMA = ku.TABLE_SCHEMA
                AND tc.TABLE_NAME = ku.TABLE_NAME
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ) pk ON c.TABLE_SCHEMA = pk.TABLE_SCHEMA AND c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
        LEFT JOIN (
            SELECT 
                ku.TABLE_SCHEMA,
                ku.TABLE_NAME,
                ku.COLUMN_NAME,
                cku.TABLE_SCHEMA as REFERENCED_TABLE_SCHEMA,
                cku.TABLE_NAME as REFERENCED_TABLE_NAME,
                cku.COLUMN_NAME as REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku ON rc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                AND rc.CONSTRAINT_SCHEMA = ku.TABLE_SCHEMA
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE cku ON rc.UNIQUE_CONSTRAINT_NAME = cku.CONSTRAINT_NAME
                AND rc.UNIQUE_CONSTRAINT_SCHEMA = cku.TABLE_SCHEMA
            WHERE ku.ORDINAL_POSITION = cku.ORDINAL_POSITION
        ) fk ON c.TABLE_SCHEMA = fk.TABLE_SCHEMA AND c.TABLE_NAME = fk.TABLE_NAME AND c.COLUMN_NAME = fk.COLUMN_NAME
        WHERE t.TABLE_TYPE = 'BASE TABLE'
            AND t.TABLE_SCHEMA = 'dbo'
            AND t.TABLE_NAME IN ('Patient', 'Employee', 'Appointment', 'Auth', 'Location', 'ServiceType', 'EmployeeAvailabilityDateTime', 'Site', 'Gender', 'TreatmentType', 'AppointmentStatus')
        ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
        """
        
        try:
            results = self.db_manager.execute_query(schema_query)
            
            # Group results by table
            tables_data = {}
            for row in results:
                table_name = row['TABLE_NAME']
                if table_name not in tables_data:
                    tables_data[table_name] = DatabaseTable(
                        table_name=table_name,
                        schema_name=row['TABLE_SCHEMA'],
                        columns=[],
                        primary_keys=[],
                        foreign_keys=[],
                        business_concepts=self._get_business_concepts(table_name)
                    )
                
                if row['COLUMN_NAME']:  # Only add if column exists
                    column_info = {
                        'name': row['COLUMN_NAME'],
                        'data_type': row['DATA_TYPE'],
                        'is_nullable': row['IS_NULLABLE'] == 'YES',
                        'is_primary_key': row['IS_PRIMARY_KEY'] == 1,
                        'is_foreign_key': row['IS_FOREIGN_KEY'] == 1,
                        'max_length': row['CHARACTER_MAXIMUM_LENGTH'],
                        'precision': row['NUMERIC_PRECISION'],
                        'scale': row['NUMERIC_SCALE'],
                        'ordinal_position': row['ORDINAL_POSITION'],
                        'default_value': row['COLUMN_DEFAULT']
                    }
                    
                    tables_data[table_name].columns.append(column_info)
                    
                    # Add to primary keys if applicable
                    if row['IS_PRIMARY_KEY'] == 1:
                        tables_data[table_name].primary_keys.append(row['COLUMN_NAME'])
                    
                    # Add to foreign keys if applicable
                    if row['IS_FOREIGN_KEY'] == 1 and row['REFERENCED_TABLE_NAME']:
                        fk_info = {
                            'column': row['COLUMN_NAME'],
                            'references_table': row['REFERENCED_TABLE_NAME'],
                            'references_column': row['REFERENCED_COLUMN_NAME']
                        }
                        if fk_info not in tables_data[table_name].foreign_keys:
                            tables_data[table_name].foreign_keys.append(fk_info)
            
            print(f"✅ Retrieved complete schema for {len(tables_data)} tables")
            for table_name, table_data in tables_data.items():
                print(f"  📋 {table_name}: {len(table_data.columns)} columns, {len(table_data.primary_keys)} PKs, {len(table_data.foreign_keys)} FKs")
            
            return tables_data
            
        except Exception as e:
            print(f"⚠️ Warning: Could not retrieve complete database schema: {e}")
            return self._get_fallback_schema()

    def _get_business_concepts(self, table_name: str) -> List[str]:
        """Get business concepts for a table name"""
        concepts_map = {
            'Patient': ['patient', 'client', 'individual', 'person', 'demographics', 'contact'],
            'Employee': ['employee', 'staff', 'therapist', 'provider', 'clinician', 'supervisor', 'doctor', 'practitioner'],
            'Appointment': ['appointment', 'session', 'visit', 'meeting', 'service', 'treatment', 'therapy', 'scheduled', 'booking'],
            'Auth': ['authorization', 'insurance', 'approval', 'coverage', 'funding', 'diagnosis', 'treatment plan'],
            'Location': ['location', 'address', 'site', 'facility', 'clinic', 'office', 'place', 'where'],
            'ServiceType': ['service', 'treatment', 'therapy', 'intervention', 'procedure', 'session type'],
            'EmployeeAvailabilityDateTime': ['availability', 'schedule', 'free time', 'open slots', 'calendar', 'time slots', 'when available'],
            'Site': ['site', 'location', 'facility', 'clinic', 'branch'],
            'Gender': ['gender', 'sex', 'male', 'female'],
            'TreatmentType': ['treatment', 'therapy type', 'service category'],
            'AppointmentStatus': ['status', 'appointment status', 'scheduled', 'completed', 'cancelled']
        }
        return concepts_map.get(table_name, [table_name.lower()])

    def _get_fallback_schema(self) -> Dict[str, DatabaseTable]:
        """Provide fallback schema if database retrieval fails"""
        return {
            'Patient': DatabaseTable(
                table_name='Patient',
                columns=[
                    {'name': 'PatientId', 'data_type': 'int', 'is_primary_key': True},
                    {'name': 'FirstName', 'data_type': 'nvarchar'},
                    {'name': 'LastName', 'data_type': 'nvarchar'},
                    {'name': 'Email', 'data_type': 'varchar'},
                    {'name': 'IsActive', 'data_type': 'bit'}
                ],
                primary_keys=['PatientId'],
                business_concepts=['patient', 'client', 'person']
            ),
            'Employee': DatabaseTable(
                table_name='Employee',
                columns=[
                    {'name': 'EmployeeId', 'data_type': 'int', 'is_primary_key': True},
                    {'name': 'FirstName', 'data_type': 'varchar'},
                    {'name': 'LastName', 'data_type': 'varchar'},
                    {'name': 'Email', 'data_type': 'varchar'},
                    {'name': 'Active', 'data_type': 'bit'}
                ],
                primary_keys=['EmployeeId'],
                business_concepts=['employee', 'staff', 'provider']
            )
        }

    def _index_complete_schema(self):
        """Index the complete schema in Qdrant"""
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
            
            for table_name, table_schema in self.complete_schema.items():
                # Create comprehensive text for embedding
                text_content = self._create_complete_table_text(table_schema)
                
                # Generate embedding
                embedding = self._get_embedding(text_content)
                
                # Create point with complete metadata
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "table_name": table_name,
                        "schema_name": table_schema.schema_name,
                        "business_concepts": table_schema.business_concepts,
                        "columns": [col["name"] for col in table_schema.columns],
                        "column_details": table_schema.columns,
                        "text_content": text_content,
                        "primary_keys": table_schema.primary_keys,
                        "foreign_keys": table_schema.foreign_keys
                    }
                )
                points.append(point)
                point_id += 1
            
            # Upload points to Qdrant
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                print(f"✅ Indexed {len(points)} complete schema points in Qdrant")
        
        except Exception as e:
            print(f"⚠️ Warning: Error indexing complete schema: {e}")

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using the configured model"""
        if not self.embedding_model:
            return [0.0] * 384  # Default dimension for fallback
        
        try:
            if self.embedding_type == "ollama":
                embedding = self.embedding_model.embed_query(text)
                return embedding
            elif self.embedding_type == "sentence_transformer":
                embedding = self.embedding_model.encode(text).tolist()
                return embedding
            else:
                return [0.0] * 384
        except Exception as e:
            print(f"⚠️ Warning: Could not generate embedding: {e}")
            return [0.0] * 384

    def _create_complete_table_text(self, table_schema: DatabaseTable) -> str:
        """Create comprehensive text representation of complete table schema"""
        text_parts = [
            f"Table {table_schema.table_name}: Healthcare database table"
        ]
        
        # Add column information
        column_descriptions = []
        for col in table_schema.columns:
            col_desc = f"{col['name']} ({col['data_type']}"
            if col.get('is_primary_key'):
                col_desc += ", PRIMARY KEY"
            if col.get('is_foreign_key'):
                col_desc += ", FOREIGN KEY"
            if not col.get('is_nullable', True):
                col_desc += ", NOT NULL"
            col_desc += ")"
            column_descriptions.append(col_desc)
        
        text_parts.append(f"Columns: {', '.join(column_descriptions)}")
        
        if table_schema.primary_keys:
            text_parts.append(f"Primary keys: {', '.join(table_schema.primary_keys)}")
        
        if table_schema.foreign_keys:
            fk_desc = [f"{fk['column']} references {fk['references_table']}.{fk['references_column']}" 
                      for fk in table_schema.foreign_keys]
            text_parts.append(f"Foreign keys: {', '.join(fk_desc)}")
        
        if table_schema.business_concepts:
            text_parts.append(f"Business concepts: {', '.join(table_schema.business_concepts)}")
        
        return ". ".join(text_parts)

    def retrieve_relevant_schema_for_query(self, user_query: str, top_k: int = 5) -> EnhancedSchemaResult:
        """Retrieve relevant schema information based on user query"""
        if not self.client or not self.embedding_model:
            print("⚠️ Warning: RAG components not available, using all schema")
            return self._get_all_schema_result()
        
        try:
            # Generate embedding for user query
            query_embedding = self._get_embedding(user_query)
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=0.2
            )
            
            print(f"🔍 DEBUG: Found {len(search_results)} schema results for query: {user_query}")
            
            # Process results and extract relevant tables
            relevant_tables = []
            table_names = set()
            
            for result in search_results:
                table_name = result.payload.get("table_name")
                print(f"🔍 DEBUG: Processing schema for table: {table_name}, score: {result.score}")
                
                if table_name and table_name in self.complete_schema:
                    if table_name not in table_names:
                        relevant_tables.append(self.complete_schema[table_name])
                        table_names.add(table_name)
            
            # If no tables found via embedding search, use keyword-based fallback
            if not relevant_tables:
                print("⚠️ No tables found via embedding search, using keyword fallback")
                relevant_tables = self._get_tables_by_keywords(user_query)
            
            # Generate suggested joins
            suggested_joins = self._generate_join_suggestions(relevant_tables)
            
            # Calculate overall confidence
            avg_confidence = sum(result.score for result in search_results) / len(search_results) if search_results else 0.7
            
            return EnhancedSchemaResult(
                tables=relevant_tables,
                complete_schema={t.table_name: t for t in relevant_tables},
                suggested_joins=suggested_joins,
                confidence_score=avg_confidence
            )
            
        except Exception as e:
            print(f"⚠️ Warning: Error retrieving schema: {e}")
            return self._get_all_schema_result()

    def _get_tables_by_keywords(self, user_query: str) -> List[DatabaseTable]:
        """Get tables based on keyword matching as fallback"""
        query_lower = user_query.lower()
        relevant_tables = []
        
        # Simple keyword matching for common queries
        if any(word in query_lower for word in ['patient', 'appointment', 'booking']):
            relevant_tables.extend(['Patient', 'Appointment'])
        
        if any(word in query_lower for word in ['employee', 'provider', 'therapist', 'doctor', 'staff']):
            relevant_tables.append('Employee')
        
        if any(word in query_lower for word in ['auth', 'authorization']):
            relevant_tables.append('Auth')
        
        if any(word in query_lower for word in ['location', 'office', 'site']):
            relevant_tables.extend(['Location', 'Site'])
        
        if any(word in query_lower for word in ['service', 'treatment']):
            relevant_tables.extend(['ServiceType', 'TreatmentType'])
        
        if any(word in query_lower for word in ['available', 'availability', 'schedule']):
            relevant_tables.extend(['Employee', 'EmployeeAvailabilityDateTime'])
        
        # Remove duplicates and get table objects
        unique_tables = list(set(relevant_tables))
        if not unique_tables:
            unique_tables = ['Patient', 'Employee', 'Appointment']  # Default tables
        
        result_tables = []
        for table_name in unique_tables:
            if table_name in self.complete_schema:
                result_tables.append(self.complete_schema[table_name])
        
        return result_tables

    def _get_all_schema_result(self) -> EnhancedSchemaResult:
        """Get all schema tables as fallback"""
        all_tables = list(self.complete_schema.values())
        suggested_joins = self._generate_join_suggestions(all_tables)
        
        return EnhancedSchemaResult(
            tables=all_tables,
            complete_schema=self.complete_schema,
            suggested_joins=suggested_joins,
            confidence_score=0.5
        )

    def _generate_join_suggestions(self, tables: List[DatabaseTable]) -> List[str]:
        """Generate JOIN suggestions based on foreign key relationships"""
        joins = []
        table_names = [t.table_name for t in tables]
        
        for table in tables:
            table_alias = table.table_name[0].lower()
            
            for fk in table.foreign_keys:
                ref_table = fk['references_table']
                if ref_table in table_names:
                    ref_alias = ref_table[0].lower()
                    join_clause = f"JOIN {ref_table} {ref_alias} ON {table_alias}.{fk['column']} = {ref_alias}.{fk['references_column']}"
                    joins.append(join_clause)
        
        return joins

    def generate_sql_with_complete_schema(self, user_query: str, schema_result: EnhancedSchemaResult) -> str:
        """Generate SQL query using complete schema information and LLM"""
        
        if self.chat_available and self.chat_model:
            return self._generate_sql_with_llm_complete(user_query, schema_result)
        else:
            return self._generate_sql_fallback(user_query, schema_result)

    def _generate_sql_with_llm_complete(self, user_query: str, schema_result: EnhancedSchemaResult) -> str:
        """Generate SQL using LLM with complete schema context"""
        try:
            # Format complete schema for LLM
            schema_context = self._format_complete_schema_for_llm(schema_result)
            
            # Create comprehensive prompt
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", """You are a SQL expert for a healthcare database. Generate a precise SQL query based on the user's request and the provided complete database schema.

COMPLETE DATABASE SCHEMA:
{schema_context}

CRITICAL RULES:
1. Use ONLY the exact table names and column names provided in the schema
2. Do NOT assume any column names - use only what's explicitly listed
3. Use proper table aliases (e.g., p for Patient, e for Employee, a for Appointment)
4. Include appropriate JOIN clauses based on foreign key relationships
5. Add proper WHERE clauses for filtering (e.g., Active = 1, IsActive = 1)
6. Use clear and readable SQL formatting
7. Return ONLY the SQL query without explanations or markdown formatting

Generate a precise SQL query for: {user_query}"""),
                ("human", "{user_query}")
            ])
            
            # Generate SQL
            chain = prompt_template | self.chat_model | StrOutputParser()
            
            sql_query = chain.invoke({
                "user_query": user_query,
                "schema_context": schema_context
            })
            
            # Clean up the SQL query
            sql_query = sql_query.strip()
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            print(f"🔍 DEBUG: Generated SQL using LLM:\n{sql_query}")
            
            return sql_query.strip()
            
        except Exception as e:
            print(f"⚠️ Warning: LLM SQL generation failed: {e}")
            return self._generate_sql_fallback(user_query, schema_result)

    def _format_complete_schema_for_llm(self, schema_result: EnhancedSchemaResult) -> str:
        """Format complete schema information for LLM prompt"""
        schema_text = []
        
        for table in schema_result.tables:
            table_section = [f"\nTable: {table.table_name}"]
            table_section.append("Columns:")
            
            for col in table.columns:
                col_info = f"  - {col['name']} ({col['data_type']}"
                
                if col.get('max_length'):
                    col_info += f"({col['max_length']})"
                elif col.get('precision') and col.get('scale'):
                    col_info += f"({col['precision']},{col['scale']})"
                
                if col.get('is_primary_key'):
                    col_info += ", PRIMARY KEY"
                if col.get('is_foreign_key'):
                    col_info += ", FOREIGN KEY"
                if not col.get('is_nullable', True):
                    col_info += ", NOT NULL"
                
                col_info += ")"
                table_section.append(col_info)
            
            if table.primary_keys:
                table_section.append(f"Primary Keys: {', '.join(table.primary_keys)}")
            
            if table.foreign_keys:
                table_section.append("Foreign Keys:")
                for fk in table.foreign_keys:
                    table_section.append(f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}")
            
            schema_text.extend(table_section)
        
        if schema_result.suggested_joins:
            schema_text.append("\nCommon Join Patterns:")
            for join in schema_result.suggested_joins:
                schema_text.append(f"  - {join}")
        
        return "\n".join(schema_text)

    def _generate_sql_fallback(self, user_query: str, schema_result: EnhancedSchemaResult) -> str:
        """Generate SQL using rule-based approach (fallback)"""
        query_lower = user_query.lower()
        
        # Determine main table
        main_table = self._determine_main_table_from_schema(query_lower, schema_result.tables)
        
        # Basic SELECT query
        main_table_obj = next((t for t in schema_result.tables if t.table_name == main_table), None)
        if not main_table_obj:
            return "SELECT 'Error: Could not determine main table' as ErrorMessage"
        
        # Build basic columns
        select_columns = []
        table_alias = main_table[0].lower()
        
        # Add ID and name columns if they exist
        for col in main_table_obj.columns:
            if col.get('is_primary_key'):
                select_columns.append(f"{table_alias}.{col['name']}")
            elif any(name_part in col['name'].lower() for name_part in ['firstname', 'lastname', 'name']):
                select_columns.append(f"{table_alias}.{col['name']}")
        
        if not select_columns:
            select_columns = [f"{table_alias}.*"]
        
        # Build basic query
        sql_parts = [
            f"SELECT {', '.join(select_columns[:5])}",  # Limit columns
            f"FROM {main_table} {table_alias}",
            f"WHERE {table_alias}.Active = 1 OR {table_alias}.IsActive = 1"
        ]
        
        return "\n".join(sql_parts)

    def _determine_main_table_from_schema(self, query_lower: str, tables: List[DatabaseTable]) -> str:
        """Determine main table from complete schema"""
        # Priority based on query keywords
        for table in tables:
            for concept in table.business_concepts:
                if concept in query_lower:
                    return table.table_name
        
        # Default priority order
        priority_order = ["Appointment", "Patient", "Employee", "Auth", "Location"]
        for table_name in priority_order:
            if any(t.table_name == table_name for t in tables):
                return table_name
        
        return tables[0].table_name if tables else "Patient"


# Singleton instance for the enhanced schema RAG
enhanced_schema_rag = None

def get_enhanced_schema_rag(db_manager) -> EnhancedSchemaRAG:
    """Get or create the enhanced schema RAG instance"""
    global enhanced_schema_rag
    if enhanced_schema_rag is None:
        enhanced_schema_rag = EnhancedSchemaRAG(db_manager)
    return enhanced_schema_rag
