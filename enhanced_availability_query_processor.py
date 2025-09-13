"""
Enhanced Availability Query Processor with Chain of Thoughts
Integrates schema analysis, query generation, and execution with real-time chain of thoughts
"""

import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sql_schema_parser import create_schema_parser
from dynamic_schema_manager import get_dynamic_schema_manager
from healthcare_database_manager_sqlserver import HealthcareDatabaseManager


@dataclass
class AvailabilityQueryResult:
    """Result of availability query processing"""
    success: bool
    sql_query: Optional[str] = None
    results: List[Dict[str, Any]] = None
    chain_of_thoughts: List[str] = None
    schema_analysis: Dict[str, Any] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    confidence_score: float = 0.0


class EnhancedAvailabilityQueryProcessor:
    """Enhanced availability query processor with chain of thoughts"""
    
    def __init__(self, schema_file_path: str = "chatbot_schema.sql"):
        self.schema_file_path = schema_file_path
        self.schema_manager = get_dynamic_schema_manager()
        self.db_manager = HealthcareDatabaseManager()
        self.chain_of_thoughts = []
        self.start_time = None
        
    def _log_thought(self, thought: str, category: str = "analysis"):
        """Log a chain of thought step"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_thought = f"[{timestamp}] {category.upper()}: {thought}"
        self.chain_of_thoughts.append(formatted_thought)
        print(f"🧠 {formatted_thought}")
        
    def _analyze_query_intent(self, user_query: str) -> Dict[str, Any]:
        """Analyze user query to understand intent and extract entities"""
        self._log_thought("Starting query intent analysis", "intent")
        
        intent_analysis = {
            'intent_type': 'unknown',
            'employee_name': None,
            'day_filter': None,
            'time_filter': None,
            'location_filter': None,
            'confidence': 0.0
        }
        
        query_lower = user_query.lower()
        
        # Check for availability intent
        availability_keywords = ['availability', 'available', 'schedule', 'free', 'open']
        if any(keyword in query_lower for keyword in availability_keywords):
            intent_analysis['intent_type'] = 'availability'
            intent_analysis['confidence'] += 0.3
            self._log_thought(f"Detected availability intent with keywords: {[k for k in availability_keywords if k in query_lower]}", "intent")
        
        # Extract employee name
        name_patterns = [
            r'(?:of|for|about)\s+([a-z]+(?:\s+[a-z]+)*)',
            r'([a-z]+(?:\s+[a-z]+)*)\s*(?:availability|schedule)',
            r'(?:doctor|dr\.?|nurse)\s+([a-z]+(?:\s+[a-z]+)*)',
            r'\b([a-z]+\s+[a-z]+)\b'  # Generic two-word name pattern
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query_lower)
            if match:
                potential_name = match.group(1).strip()
                # Filter out common non-name words
                if potential_name not in ['the', 'on', 'in', 'at', 'this', 'that', 'and', 'or']:
                    intent_analysis['employee_name'] = potential_name.title()
                    intent_analysis['confidence'] += 0.4
                    self._log_thought(f"Extracted employee name: '{intent_analysis['employee_name']}'", "extraction")
                    break
        
        # Extract day filter
        day_patterns = {
            'monday': ['monday', 'mon'],
            'tuesday': ['tuesday', 'tue', 'tues'],
            'wednesday': ['wednesday', 'wed'],
            'thursday': ['thursday', 'thu', 'thur'],
            'friday': ['friday', 'fri'],
            'saturday': ['saturday', 'sat'],
            'sunday': ['sunday', 'sun']
        }
        
        for day, variations in day_patterns.items():
            if any(variation in query_lower for variation in variations):
                intent_analysis['day_filter'] = day
                intent_analysis['confidence'] += 0.2
                self._log_thought(f"Detected day filter: {day}", "extraction")
                break
        
        # Extract time filter
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'morning',
            r'afternoon',
            r'evening'
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, query_lower):
                intent_analysis['time_filter'] = re.search(pattern, query_lower).group(0)
                intent_analysis['confidence'] += 0.1
                self._log_thought(f"Detected time filter: {intent_analysis['time_filter']}", "extraction")
                break
        
        self._log_thought(f"Intent analysis complete. Confidence: {intent_analysis['confidence']:.2f}", "intent")
        return intent_analysis
    
    def _perform_schema_analysis(self, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform schema analysis to identify relevant tables and columns"""
        self._log_thought("Starting schema analysis", "schema")
        
        # Use the dynamic schema manager to get relevant schema
        try:
            schema_result = self.schema_manager.get_schema_for_query(
                f"availability query for employee {intent_analysis.get('employee_name', 'any')}"
            )
            self._log_thought(f"Retrieved schema using {schema_result['search_method']}: {len(schema_result['tables'])} tables", "schema")
        except Exception as e:
            self._log_thought(f"Failed to get schema: {str(e)}", "error")
            return {'error': str(e)}
        
        schema_analysis = {
            'relevant_tables': [],
            'relevant_columns': {},
            'foreign_key_relationships': [],
            'query_requirements': []
        }
        
        # Identify relevant tables for availability queries
        employee_tables = []
        schedule_tables = []
        
        for table_info in schema_result['tables']:
            table_name = table_info['table_name']
            table_name_lower = table_name.lower()
            
            # Look for employee-related tables
            if any(keyword in table_name_lower for keyword in ['employee', 'staff', 'provider', 'doctor', 'nurse']):
                employee_tables.append(table_info)
                schema_analysis['relevant_tables'].append(table_name)
                self._log_thought(f"Identified employee table: {table_name}", "schema")
            
            # Look for schedule/availability tables
            if any(keyword in table_name_lower for keyword in ['schedule', 'availability', 'appointment', 'booking', 'datetime']):
                schedule_tables.append(table_info)
                schema_analysis['relevant_tables'].append(table_name)
                self._log_thought(f"Identified schedule table: {table_name}", "schema")
        
        # Analyze columns in relevant tables
        for table_info in employee_tables + schedule_tables:
            table_name = table_info['table_name']
            schema_analysis['relevant_columns'][table_name] = []
            
            for column in table_info['columns']:
                column_name = column['name']
                column_type = column['data_type']
                column_name_lower = column_name.lower()
                
                # Look for name columns
                if any(keyword in column_name_lower for keyword in ['name', 'first', 'last', 'fname', 'lname']):
                    schema_analysis['relevant_columns'][table_name].append({
                        'column': column_name,
                        'type': column_type,
                        'purpose': 'name_field'
                    })
                    self._log_thought(f"Found name column: {table_name}.{column_name}", "schema")
                
                # Look for date/time columns
                if any(keyword in column_name_lower for keyword in ['date', 'time', 'day', 'schedule', 'start', 'end', 'available']):
                    schema_analysis['relevant_columns'][table_name].append({
                        'column': column_name,
                        'type': column_type,
                        'purpose': 'datetime_field'
                    })
                    self._log_thought(f"Found datetime column: {table_name}.{column_name}", "schema")
                
                # Look for ID/foreign key columns
                if 'id' in column_name_lower or column_name_lower.endswith('_id'):
                    schema_analysis['relevant_columns'][table_name].append({
                        'column': column_name,
                        'type': column_type,
                        'purpose': 'id_field'
                    })
        
        # Use the schema parser to get foreign key relationships
        try:
            parser = create_schema_parser(self.schema_file_path)
            
            # Get relationships for employee tables
            for table_info in employee_tables:
                table_name = table_info['table_name']
                relationships = parser.get_table_relationships(table_name)
                
                for fk in relationships['outgoing']:
                    if fk['referenced_table'] in schema_analysis['relevant_tables']:
                        schema_analysis['foreign_key_relationships'].append({
                            'from_table': table_name,
                            'from_column': fk['local_column'],
                            'to_table': fk['referenced_table'],
                            'to_column': fk['referenced_column']
                        })
                        self._log_thought(f"Relevant FK: {table_name}.{fk['local_column']} -> {fk['referenced_table']}.{fk['referenced_column']}", "schema")
                
                for fk in relationships['incoming']:
                    if fk['table_name'] in schema_analysis['relevant_tables']:
                        schema_analysis['foreign_key_relationships'].append({
                            'from_table': fk['table_name'],
                            'from_column': fk['column_name'],
                            'to_table': table_name,
                            'to_column': fk['referenced_column']
                        })
                        self._log_thought(f"Relevant FK: {fk['table_name']}.{fk['column_name']} -> {table_name}.{fk['referenced_column']}", "schema")
        
        except Exception as e:
            self._log_thought(f"Warning: Could not analyze FK relationships: {str(e)}", "warning")
        
        self._log_thought("Schema analysis complete", "schema")
        return schema_analysis
    
    def _generate_availability_query(self, intent_analysis: Dict[str, Any], schema_analysis: Dict[str, Any]) -> str:
        """Generate SQL query for availability based on intent and schema analysis"""
        self._log_thought("Starting SQL query generation", "query")
        
        # Base query structure
        select_clause = "SELECT DISTINCT"
        from_clause = "FROM"
        where_clause = "WHERE"
        join_clause = ""
        
        # Find the main employee and schedule tables
        employee_table = None
        schedule_table = None
        
        # Look for Employee table (primary employee table)
        for table_name in schema_analysis['relevant_tables']:
            if table_name == 'Employee' or 'employee' in table_name.lower():
                employee_table = table_name
                if table_name == 'Employee':  # Prefer exact match
                    break
        
        # Look for schedule/availability table
        for table_name in schema_analysis['relevant_tables']:
            if any(keyword in table_name.lower() for keyword in ['availability', 'schedule', 'datetime']):
                schedule_table = table_name
                break
        
        if not employee_table:
            self._log_thought("No employee table found, using fallback", "query")
            employee_table = "Employee"
        
        if not schedule_table:
            self._log_thought("No schedule table found, using fallback", "query")
            schedule_table = "EmployeeAvailabilityDateTime"
        
        self._log_thought(f"Using employee table: {employee_table}, schedule table: {schedule_table}", "query")
        
        # Build SELECT clause based on available columns
        select_fields = []
        
        # Look for name columns in employee table
        if employee_table in schema_analysis['relevant_columns']:
            name_columns = [col for col in schema_analysis['relevant_columns'][employee_table] if col['purpose'] == 'name_field']
            if name_columns:
                # Use the actual name columns found
                first_name_col = next((col['column'] for col in name_columns if 'first' in col['column'].lower()), None)
                last_name_col = next((col['column'] for col in name_columns if 'last' in col['column'].lower()), None)
                
                if first_name_col and last_name_col:
                    select_fields.append(f"e.{first_name_col} + ' ' + e.{last_name_col} AS EmployeeName")
                else:
                    # Use the first name column found
                    name_col = name_columns[0]['column']
                    select_fields.append(f"e.{name_col} AS EmployeeName")
            else:
                # Fallback
                select_fields.append(f"e.FirstName + ' ' + e.LastName AS EmployeeName")
        else:
            select_fields.append(f"e.FirstName + ' ' + e.LastName AS EmployeeName")
        
        # Add other standard fields (using actual column names from schema)
        select_fields.extend([
            f"e.EmployeeId",
            f"s.WeekDay",
            f"s.AvailableFrom",
            f"s.AvailableTo",
            f"s.AvailabilityStatusId",
            f"e.LastName",
            f"e.FirstName"  # Include ORDER BY columns for DISTINCT compatibility
        ])
        
        select_clause += " " + ", ".join(select_fields)
        self._log_thought(f"SELECT clause: {select_clause}", "query")
        
        # Build FROM and JOIN clauses
        from_clause += f" {employee_table} e"
        
        # Find foreign key relationship between employee and schedule tables
        join_condition = None
        for fk in schema_analysis['foreign_key_relationships']:
            if (fk['from_table'] == schedule_table and fk['to_table'] == employee_table):
                join_condition = f"s.{fk['from_column']} = e.{fk['to_column']}"
                break
            elif (fk['from_table'] == employee_table and fk['to_table'] == schedule_table):
                join_condition = f"e.{fk['from_column']} = s.{fk['to_column']}"
                break
        
        if not join_condition:
            # Try common patterns based on actual schema
            if schedule_table in schema_analysis['relevant_columns']:
                id_columns = [col for col in schema_analysis['relevant_columns'][schedule_table] if col['purpose'] == 'id_field']
                employee_id_col = next((col['column'] for col in id_columns if 'employee' in col['column'].lower() and col['column'] != 'EmployeeAvailabilityDateTimeId'), None)
                if employee_id_col:
                    join_condition = f"e.EmployeeId = s.{employee_id_col}"  # Use the EmployeeId column, not the primary key
                else:
                    join_condition = "e.EmployeeId = s.EmployeeId"  # Based on actual schema
            else:
                join_condition = "e.EmployeeId = s.EmployeeId"  # Based on actual schema
        
        join_clause = f"INNER JOIN {schedule_table} s ON {join_condition}"
        self._log_thought(f"JOIN clause: {join_clause}", "query")
        
        # Build WHERE clause (using actual column name AvailabilityStatusId)
        where_conditions = ["s.AvailabilityStatusId = 1"]  # Assuming 1 means available
        
        # Add employee name filter if specified
        if intent_analysis['employee_name']:
            name_parts = intent_analysis['employee_name'].split()
            if len(name_parts) >= 2:
                first_name, last_name = name_parts[0], name_parts[-1]
                # Use actual column names if available
                if employee_table in schema_analysis['relevant_columns']:
                    name_columns = [col for col in schema_analysis['relevant_columns'][employee_table] if col['purpose'] == 'name_field']
                    first_name_col = next((col['column'] for col in name_columns if 'first' in col['column'].lower()), 'FirstName')
                    last_name_col = next((col['column'] for col in name_columns if 'last' in col['column'].lower()), 'LastName')
                else:
                    first_name_col, last_name_col = 'FirstName', 'LastName'
                
                where_conditions.append(f"(e.{first_name_col} LIKE '%{first_name}%' AND e.{last_name_col} LIKE '%{last_name}%')")
                self._log_thought(f"Added name filter: {first_name} {last_name}", "query")
            else:
                name = name_parts[0]
                # Use actual column names if available
                if employee_table in schema_analysis['relevant_columns']:
                    name_columns = [col for col in schema_analysis['relevant_columns'][employee_table] if col['purpose'] == 'name_field']
                    if name_columns:
                        name_conditions = []
                        for col in name_columns:
                            name_conditions.append(f"e.{col['column']} LIKE '%{name}%'")
                        where_conditions.append(f"({' OR '.join(name_conditions)})")
                    else:
                        where_conditions.append(f"(e.FirstName LIKE '%{name}%' OR e.LastName LIKE '%{name}%')")
                else:
                    where_conditions.append(f"(e.FirstName LIKE '%{name}%' OR e.LastName LIKE '%{name}%')")
                self._log_thought(f"Added name filter: {name}", "query")
        
        # Add day filter if specified (using actual column name WeekDay)
        if intent_analysis['day_filter']:
            day_number = {
                'sunday': 1, 'monday': 2, 'tuesday': 3, 'wednesday': 4,
                'thursday': 5, 'friday': 6, 'saturday': 7
            }.get(intent_analysis['day_filter'].lower(), None)
            
            if day_number:
                where_conditions.append(f"s.WeekDay = {day_number}")
                self._log_thought(f"Added day filter: {intent_analysis['day_filter']} (day {day_number})", "query")
        
        where_clause += " " + " AND ".join(where_conditions)
        
        # Add ORDER BY clause (using actual column names)
        order_clause = "ORDER BY e.LastName, e.FirstName, s.WeekDay, s.AvailableFrom"
        
        # Combine all clauses
        sql_query = f"{select_clause}\n{from_clause}\n{join_clause}\n{where_clause}\n{order_clause}"
        
        self._log_thought("SQL query generation complete", "query")
        self._log_thought(f"Generated query:\n{sql_query}", "query")
        
        return sql_query
    
    def _execute_query(self, sql_query: str) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
        """Execute the generated SQL query"""
        self._log_thought("Executing SQL query", "execution")
        
        try:
            results = self.db_manager.execute_query(sql_query)
            self._log_thought(f"Query executed successfully. {len(results)} results returned.", "execution")
            return True, results, None
        except Exception as e:
            error_msg = str(e)
            self._log_thought(f"Query execution failed: {error_msg}", "error")
            return False, [], error_msg
    
    def process_availability_query(self, user_query: str) -> AvailabilityQueryResult:
        """Process an availability query with full chain of thoughts"""
        self.start_time = time.time()
        self.chain_of_thoughts = []
        
        self._log_thought(f"Processing query: '{user_query}'", "start")
        
        try:
            # Step 1: Analyze query intent
            intent_analysis = self._analyze_query_intent(user_query)
            
            # Step 2: Perform schema analysis
            schema_analysis = self._perform_schema_analysis(intent_analysis)
            
            if 'error' in schema_analysis:
                return AvailabilityQueryResult(
                    success=False,
                    error_message=schema_analysis['error'],
                    chain_of_thoughts=self.chain_of_thoughts,
                    execution_time=time.time() - self.start_time
                )
            
            # Step 3: Generate SQL query
            sql_query = self._generate_availability_query(intent_analysis, schema_analysis)
            
            # Step 4: Execute query
            success, results, error_msg = self._execute_query(sql_query)
            
            execution_time = time.time() - self.start_time
            self._log_thought(f"Total processing time: {execution_time:.3f} seconds", "completion")
            
            return AvailabilityQueryResult(
                success=success,
                sql_query=sql_query,
                results=results or [],
                chain_of_thoughts=self.chain_of_thoughts,
                schema_analysis=schema_analysis,
                execution_time=execution_time,
                error_message=error_msg,
                confidence_score=intent_analysis['confidence']
            )
            
        except Exception as e:
            execution_time = time.time() - self.start_time
            self._log_thought(f"Processing failed: {str(e)}", "error")
            
            return AvailabilityQueryResult(
                success=False,
                error_message=str(e),
                chain_of_thoughts=self.chain_of_thoughts,
                execution_time=execution_time
            )


# Singleton instance
_availability_processor = None

def get_availability_query_processor():
    """Get the singleton availability query processor"""
    global _availability_processor
    if _availability_processor is None:
        _availability_processor = EnhancedAvailabilityQueryProcessor()
    return _availability_processor
