"""
Dynamic Schema Management System
Provides real-time schema updates and vector database management
No compromise on table/column name changes
Uses real schema from chatbot_schema.sql file
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Import model configuration
from model_config import EMBED_MODEL, CHAT_MODEL

# Import SQL schema parser
from sql_schema_parser import SQLSchemaParser

# Database and embedding imports
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
    print("Warning: Required packages not available")
    QdrantClient = None


@dataclass
class SchemaUpdateInfo:
    """Information about schema updates"""
    update_id: str
    timestamp: datetime
    tables_updated: List[str] = field(default_factory=list)
    columns_added: Dict[str, List[str]] = field(default_factory=dict)
    columns_removed: Dict[str, List[str]] = field(default_factory=dict)
    columns_modified: Dict[str, List[str]] = field(default_factory=dict)
    success: bool = False
    error_message: Optional[str] = None


class DynamicSchemaManager:
    """Manages dynamic schema updates with vector database synchronization"""
    
    def __init__(self, db_manager=None, vector_store_path: str = "./vector_store", schema_file_path: str = None):
        """Initialize the Dynamic Schema Manager"""
        print("🔄 Initializing Dynamic Schema Management System...")
        
        self.db_manager = db_manager
        self.vector_store_path = vector_store_path
        self.collection_name = "healthcare_schema_dynamic"
        self.schema_version = "1.0"
        
        # Initialize SQL schema parser
        if schema_file_path is None:
            schema_file_path = os.path.join(os.getcwd(), 'chatbot_schema.sql')
        
        self.schema_parser = SQLSchemaParser(schema_file_path)
        print(f"📁 Using schema file: {schema_file_path}")
        
        # Initialize vector database
        self._initialize_vector_database()
        
        # Initialize embedding model
        self._initialize_embedding_model()
        
        # Initialize chat model
        self._initialize_chat_model()
        
        # Schema cache
        self.current_schema = {}
        self.schema_hash = None
        
        # Load schema from SQL file
        self._load_schema_from_file()
        
        print("✅ Dynamic Schema Management System ready")

    def _initialize_vector_database(self):
        """Initialize or reinitialize vector database"""
        try:
            # Always use in-memory for fresh start
            print("🗑️ Initializing fresh vector database...")
            if QdrantClient is not None:
                self.client = QdrantClient(":memory:")
                print("✅ Fresh vector database initialized")
            else:
                print("⚠️ Warning: Qdrant client not available")
                self.client = None
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize vector database: {e}")
            self.client = None

    def _initialize_embedding_model(self):
        """Initialize embedding model"""
        try:
            if OllamaEmbeddings is not None:
                self.embedding_model = OllamaEmbeddings(model=EMBED_MODEL)
                self.embedding_type = "ollama"
                print(f"✅ Embedding model loaded: {EMBED_MODEL}")
            else:
                raise ImportError("OllamaEmbeddings not available")
        except Exception as e:
            print(f"⚠️ Warning: Could not load Ollama embedding model: {e}")
            try:
                if SentenceTransformer is not None:
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.embedding_type = "sentence_transformer"
                    print("✅ Fallback embedding model loaded")
                else:
                    self.embedding_model = None
                    self.embedding_type = None
            except Exception as e2:
                print(f"⚠️ Warning: Could not load fallback embedding model: {e2}")
                self.embedding_model = None
                self.embedding_type = None

    def _initialize_chat_model(self):
        """Initialize chat model for SQL generation"""
        try:
            if ChatOllama is not None:
                self.chat_model = ChatOllama(model=CHAT_MODEL, temperature=0.1)
                print(f"✅ Chat model loaded: {CHAT_MODEL}")
                self.chat_available = True
            else:
                self.chat_model = None
                self.chat_available = False
        except Exception as e:
            print(f"⚠️ Warning: Could not load chat model: {e}")
            self.chat_model = None
            self.chat_available = False

    def _load_schema_from_file(self):
        """Load schema from SQL file"""
        print("📊 Loading schema from SQL file...")
        
        try:
            schema_info = self.schema_parser.parse_schema_file()
            if schema_info:
                # Set ordinal positions for columns
                for table_name, table_info in schema_info.items():
                    for i, column in enumerate(table_info['columns']):
                        column['ordinal_position'] = i + 1
                
                self.current_schema = schema_info
                self.schema_hash = self._calculate_schema_hash(schema_info)
                self._rebuild_vector_database()
                print(f"✅ Schema loaded from file: {len(schema_info)} tables")
            else:
                print("⚠️ Warning: Could not load schema from file")
        except Exception as e:
            print(f"❌ Error loading schema from file: {e}")

    def get_current_database_schema(self, table_filter: List[str] = None) -> Dict[str, Any]:
        """Get current database schema from SQL file (not live database)"""
        print("� Using schema from SQL file...")
        
        if table_filter:
            print(f"🔍 Filtering schema for {len(table_filter)} tables...")
            filtered_schema = {}
            for table_name in table_filter:
                if table_name in self.current_schema:
                    filtered_schema[table_name] = self.current_schema[table_name]
            return filtered_schema
        else:
            return self.current_schema.copy()

    def _calculate_schema_hash(self, schema_info: Dict) -> str:
        """Calculate hash of schema for change detection"""
        import hashlib
        schema_str = json.dumps(schema_info, sort_keys=True, default=str)
        return hashlib.md5(schema_str.encode()).hexdigest()

    def check_for_schema_changes(self) -> SchemaUpdateInfo:
        """Check for schema changes by re-parsing the SQL file"""
        print("🔍 Checking for schema file changes...")
        
        # Re-parse schema file
        new_schema = self.schema_parser.parse_schema_file()
        new_hash = self._calculate_schema_hash(new_schema)
        
        update_info = SchemaUpdateInfo(
            update_id=f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now()
        )
        
        if self.schema_hash is None or new_hash != self.schema_hash:
            print("🔄 Schema file changes detected!")
            
            # Analyze changes
            old_schema = self.current_schema
            
            # Find table changes
            old_tables = set(old_schema.keys())
            new_tables = set(new_schema.keys())
            
            added_tables = new_tables - old_tables
            removed_tables = old_tables - new_tables
            common_tables = old_tables & new_tables
            
            update_info.tables_updated = list(added_tables) + list(removed_tables) + list(common_tables)
            
            # Find column changes for common tables
            for table_name in common_tables:
                old_columns = {col['name'] for col in old_schema.get(table_name, {}).get('columns', [])}
                new_columns = {col['name'] for col in new_schema.get(table_name, {}).get('columns', [])}
                
                added_cols = new_columns - old_columns
                removed_cols = old_columns - new_columns
                
                if added_cols:
                    update_info.columns_added[table_name] = list(added_cols)
                if removed_cols:
                    update_info.columns_removed[table_name] = list(removed_cols)
            
            # Update current schema
            self.current_schema = new_schema
            self.schema_hash = new_hash
            
            print(f"📊 Schema update summary:")
            print(f"  - Tables added: {len(added_tables)}")
            print(f"  - Tables removed: {len(removed_tables)}")
            print(f"  - Columns added: {sum(len(cols) for cols in update_info.columns_added.values())}")
            print(f"  - Columns removed: {sum(len(cols) for cols in update_info.columns_removed.values())}")
            
        else:
            print("✅ No schema file changes detected")
        
        return update_info

    def force_schema_update(self) -> SchemaUpdateInfo:
        """Force a complete schema update from SQL file"""
        print("🔄 Forcing complete schema update from SQL file...")
        
        # Clear current schema to force update
        self.schema_hash = None
        
        # Reload schema from file
        self._load_schema_from_file()
        
        # Check for changes (will rebuild vector database)
        update_info = self.check_for_schema_changes()
        if self.current_schema:
            self._rebuild_vector_database()
            update_info.success = True
            update_info.tables_updated = list(self.current_schema.keys())
            print("✅ Forced schema update completed")
        else:
            update_info.error_message = "No schema found to update"
            
        return update_info

    def _rebuild_vector_database(self):
        """Rebuild the vector database with current schema"""
        if not self.client or not self.embedding_model:
            print("⚠️ Warning: Vector database or embedding model not available")
            return
        
        try:
            print("🔄 Rebuilding vector database with current schema...")
            
            # Delete existing collection
            try:
                self.client.delete_collection(self.collection_name)
            except:
                pass
            
            # Create new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            
            # Index current schema
            points = []
            point_id = 1
            
            for table_name, table_info in self.current_schema.items():
                # Create comprehensive text representation
                text_content = self._create_schema_text(table_info)
                
                # Generate embedding
                embedding = self._get_embedding(text_content)
                
                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "table_name": table_name,
                        "table_schema": table_info.get('table_schema', 'dbo'),
                        "table_description": table_info.get('table_description', ''),
                        "columns": [col['name'] for col in table_info['columns']],
                        "column_details": table_info['columns'],
                        "primary_keys": table_info['primary_keys'],
                        "foreign_keys": table_info['foreign_keys'],
                        "text_content": text_content,
                        "last_updated": table_info.get('last_updated', datetime.now().isoformat()),
                        "schema_version": self.schema_version
                    }
                )
                points.append(point)
                point_id += 1
            
            # Upload points
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                print(f"✅ Vector database rebuilt with {len(points)} schema points")
            
        except Exception as e:
            print(f"❌ Error rebuilding vector database: {e}")

    def _create_schema_text(self, table_info: Dict) -> str:
        """Create comprehensive text representation of table schema"""
        text_parts = [
            f"Table {table_info['table_name']}: {table_info.get('table_description', 'Healthcare database table')}"
        ]
        
        # Add column information with full details
        column_descriptions = []
        for col in table_info['columns']:
            col_desc = f"{col['name']} ({col['data_type']}"
            
            if col.get('character_maximum_length'):
                col_desc += f"({col['character_maximum_length']})"
            elif col.get('numeric_precision') and col.get('numeric_scale'):
                col_desc += f"({col['numeric_precision']},{col['numeric_scale']})"
            
            if col.get('is_primary_key'):
                col_desc += ", PRIMARY KEY"
            if col.get('is_foreign_key'):
                col_desc += ", FOREIGN KEY"
            if not col.get('is_nullable', True):
                col_desc += ", NOT NULL"
            if col.get('column_description'):
                col_desc += f", {col['column_description']}"
            
            col_desc += ")"
            column_descriptions.append(col_desc)
        
        text_parts.append(f"Columns: {', '.join(column_descriptions[:10])}")  # Limit for embedding
        
        if table_info['primary_keys']:
            text_parts.append(f"Primary keys: {', '.join(table_info['primary_keys'])}")
        
        if table_info['foreign_keys']:
            fk_desc = [f"{fk['column']} references {fk['references_table']}.{fk['references_column']}" 
                      for fk in table_info['foreign_keys'][:5]]  # Limit for embedding
            text_parts.append(f"Foreign keys: {', '.join(fk_desc)}")
        
        return ". ".join(text_parts)

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        if not self.embedding_model:
            return [0.0] * 384
        
        try:
            if self.embedding_type == "ollama":
                return self.embedding_model.embed_query(text)
            elif self.embedding_type == "sentence_transformer":
                return self.embedding_model.encode(text).tolist()
            else:
                return [0.0] * 384
        except Exception as e:
            print(f"⚠️ Warning: Could not generate embedding: {e}")
            return [0.0] * 384

    def get_schema_for_query(self, user_query: str, top_k: int = 5) -> Dict[str, Any]:
        """Get relevant schema for user query"""
        if not self.client or not self.embedding_model:
            print("⚠️ Using complete schema (vector search not available)")
            return {
                "tables": list(self.current_schema.values()),
                "confidence_score": 0.5,
                "search_method": "complete_schema"
            }
        
        try:
            # Generate query embedding
            query_embedding = self._get_embedding(user_query)
            
            # Search vector database
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=0.2
            )
            
            relevant_tables = []
            for result in search_results:
                table_name = result.payload.get("table_name")
                if table_name in self.current_schema:
                    relevant_tables.append(self.current_schema[table_name])
            
            if not relevant_tables:
                # Fallback to keyword matching
                relevant_tables = self._get_tables_by_keywords(user_query)
            
            confidence = sum(result.score for result in search_results) / len(search_results) if search_results else 0.7
            
            return {
                "tables": relevant_tables,
                "confidence_score": confidence,
                "search_method": "vector_search"
            }
            
        except Exception as e:
            print(f"⚠️ Vector search failed: {e}")
            return {
                "tables": self._get_tables_by_keywords(user_query),
                "confidence_score": 0.6,
                "search_method": "keyword_fallback"
            }

    def _get_tables_by_keywords(self, user_query: str) -> List[Dict]:
        """Get tables using keyword matching"""
        query_lower = user_query.lower()
        relevant_tables = []
        
        keywords_map = {
            'patient': ['Patient'],
            'employee': ['Employee'],
            'appointment': ['Appointment', 'AppointmentStatus'],
            'auth': ['Auth'],
            'location': ['Location', 'Site'],
            'service': ['ServiceType'],
            'availability': ['Employee', 'EmployeeAvailabilityDateTime'],
            'treatment': ['TreatmentType'],
            'gender': ['Gender']
        }
        
        matched_tables = set()
        for keyword, tables in keywords_map.items():
            if keyword in query_lower:
                matched_tables.update(tables)
        
        if not matched_tables:
            matched_tables = {'Patient', 'Employee', 'Appointment'}  # Default
        
        for table_name in matched_tables:
            if table_name in self.current_schema:
                relevant_tables.append(self.current_schema[table_name])
        
        return relevant_tables

    def generate_sql_with_current_schema(self, user_query: str, relevant_tables: List[Dict]) -> str:
        """Generate SQL using current schema and LLM"""
        if not self.chat_available:
            return self._generate_basic_sql(user_query, relevant_tables)
        
        try:
            # Format schema for LLM
            schema_context = self._format_schema_for_llm(relevant_tables)
            
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", """You are a SQL expert for a healthcare database. Generate precise SQL queries using ONLY the exact table and column names provided.

CURRENT DATABASE SCHEMA (REAL-TIME):
{schema_context}

CRITICAL REQUIREMENTS:
1. Use ONLY the exact table names and column names provided above
2. Do NOT assume any column names - use only what's explicitly listed
3. Use proper table aliases (e.g., p for Patient, e for Employee)
4. Include appropriate JOINs based on foreign key relationships
5. Add WHERE clauses for active records where applicable
6. Return ONLY the SQL query without explanations

Generate SQL for: {user_query}"""),
                ("human", "{user_query}")
            ])
            
            chain = prompt_template | self.chat_model | StrOutputParser()
            
            sql_query = chain.invoke({
                "user_query": user_query,
                "schema_context": schema_context
            })
            
            # Clean SQL
            sql_query = sql_query.strip()
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except Exception as e:
            print(f"⚠️ LLM SQL generation failed: {e}")
            return self._generate_basic_sql(user_query, relevant_tables)

    def _format_schema_for_llm(self, tables: List[Dict]) -> str:
        """Format schema for LLM prompt"""
        schema_text = []
        
        for table_info in tables:
            table_section = [f"\nTable: {table_info['table_name']}"]
            if table_info.get('table_description'):
                table_section.append(f"Description: {table_info['table_description']}")
            
            table_section.append("Columns:")
            
            for col in table_info['columns']:
                col_info = f"  - {col['name']} ({col['data_type']}"
                
                if col.get('character_maximum_length'):
                    col_info += f"({col['character_maximum_length']})"
                elif col.get('numeric_precision') and col.get('numeric_scale'):
                    col_info += f"({col['numeric_precision']},{col['numeric_scale']})"
                
                if col.get('is_primary_key'):
                    col_info += ", PRIMARY KEY"
                if col.get('is_foreign_key'):
                    col_info += ", FOREIGN KEY"
                if not col.get('is_nullable', True):
                    col_info += ", NOT NULL"
                
                col_info += ")"
                table_section.append(col_info)
            
            if table_info['primary_keys']:
                table_section.append(f"Primary Keys: {', '.join(table_info['primary_keys'])}")
            
            if table_info['foreign_keys']:
                table_section.append("Foreign Keys:")
                for fk in table_info['foreign_keys']:
                    table_section.append(f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}")
            
            schema_text.extend(table_section)
        
        return "\n".join(schema_text)

    def _generate_basic_sql(self, user_query: str, tables: List[Dict]) -> str:
        """Generate basic SQL as fallback"""
        if not tables:
            return "SELECT 'No tables available' as Message"
        
        main_table = tables[0]
        table_name = main_table['table_name']
        table_alias = table_name[0].lower()
        
        # Get primary key and a few other columns
        columns = []
        for col in main_table['columns'][:5]:  # Limit columns
            columns.append(f"{table_alias}.{col['name']}")
        
        sql = f"SELECT {', '.join(columns)} FROM {table_name} {table_alias}"
        
        # Add basic WHERE clause if Active column exists
        active_columns = [col['name'] for col in main_table['columns'] if 'active' in col['name'].lower()]
        if active_columns:
            sql += f" WHERE {table_alias}.{active_columns[0]} = 1"
        
        return sql

    def get_schema_status(self) -> Dict[str, Any]:
        """Get current schema status"""
        return {
            "total_tables": len(self.current_schema),
            "schema_version": self.schema_version,
            "last_updated": max([table.get('last_updated', '') for table in self.current_schema.values()]) if self.current_schema else None,
            "schema_hash": self.schema_hash,
            "vector_database_ready": self.client is not None,
            "embedding_model_ready": self.embedding_model is not None,
            "chat_model_ready": self.chat_available,
            "tables": list(self.current_schema.keys())
        }


# Global instance
dynamic_schema_manager = None

def get_dynamic_schema_manager(db_manager=None) -> DynamicSchemaManager:
    """Get or create dynamic schema manager instance"""
    global dynamic_schema_manager
    if dynamic_schema_manager is None:
        dynamic_schema_manager = DynamicSchemaManager(db_manager)
    return dynamic_schema_manager

def force_schema_refresh(db_manager=None) -> SchemaUpdateInfo:
    """Force a complete schema refresh"""
    global dynamic_schema_manager
    if dynamic_schema_manager is None:
        dynamic_schema_manager = DynamicSchemaManager(db_manager)
    return dynamic_schema_manager.force_schema_update()
