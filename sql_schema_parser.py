"""
SQL Schema Parser
Parses the chatbot_schema.sql file to extract table and column information
"""

import re
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class SQLSchemaParser:
    """Parser for SQL schema files"""
    
    def __init__(self, schema_file_path: str):
        """Initialize parser with schema file path"""
        self.schema_file_path = schema_file_path
        self.parsed_schema = {}
        
    def parse_schema_file(self) -> Dict[str, Any]:
        """Parse the SQL schema file and extract table information"""
        print("📁 Parsing SQL schema file...")
        
        if not os.path.exists(self.schema_file_path):
            print(f"❌ Schema file not found: {self.schema_file_path}")
            return {}
        
        try:
            with open(self.schema_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract CREATE TABLE statements using a more robust pattern
            # Pattern: -- Table: TableName\n-- Description\nCREATE TABLE ... (...);
            pattern = r'-- Table: (\w+)\s*\n-- (.*?)\n(CREATE TABLE[^;]+;)'
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            
            schema_info = {}
            
            for table_name, description, create_statement in matches:
                print(f"  📊 Parsing table: {table_name}")
                
                table_info = self._parse_create_table_statement(
                    table_name, 
                    description.strip(), 
                    create_statement
                )
                
                if table_info:
                    schema_info[table_name] = table_info
            
            print(f"✅ Parsed {len(schema_info)} tables from schema file")
            self.parsed_schema = schema_info
            return schema_info
            
        except Exception as e:
            print(f"❌ Error parsing schema file: {e}")
            return {}
    
    def _parse_create_table_statement(self, table_name: str, description: str, create_statement: str) -> Dict[str, Any]:
        """Parse a single CREATE TABLE statement"""
        try:
            # Extract schema name from CREATE TABLE statement
            schema_match = re.search(r'CREATE TABLE\s+(\w+)\.(\w+)\.(\w+)', create_statement, re.IGNORECASE)
            if schema_match:
                database_name, schema_name, extracted_table_name = schema_match.groups()
            else:
                schema_name = 'dbo'
                extracted_table_name = table_name
            
            table_info = {
                'table_name': table_name,
                'table_schema': schema_name,
                'table_description': description if description != 'Auto-generated description placeholder' else f'{table_name} table for healthcare management',
                'columns': [],
                'primary_keys': [],
                'foreign_keys': [],
                'indexes': [],
                'last_updated': datetime.now().isoformat()
            }
            
            # Extract column definitions
            columns_section = self._extract_columns_section(create_statement)
            if columns_section:
                columns = self._parse_columns(columns_section)
                table_info['columns'] = columns
                
                # Extract primary keys
                table_info['primary_keys'] = self._extract_primary_keys(columns_section)
                
                # Extract foreign keys
                table_info['foreign_keys'] = self._extract_foreign_keys(columns_section)
            
            return table_info
            
        except Exception as e:
            print(f"⚠️ Error parsing table {table_name}: {e}")
            return {}
    
    def _extract_columns_section(self, create_statement: str) -> str:
        """Extract the columns section from CREATE TABLE statement"""
        # Find content between parentheses
        paren_start = create_statement.find('(')
        paren_end = create_statement.rfind(');')
        
        if paren_start != -1 and paren_end != -1:
            return create_statement[paren_start + 1:paren_end].strip()
        
        return ""
    
    def _parse_columns(self, columns_section: str) -> List[Dict[str, Any]]:
        """Parse column definitions"""
        columns = []
        
        # Split into lines and process each line
        lines = [line.strip() for line in columns_section.split('\n') if line.strip()]
        
        for line in lines:
            # Skip constraint definitions
            if any(line.upper().startswith(constraint) for constraint in 
                   ['CONSTRAINT', 'PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE', 'CHECK']):
                continue
            
            # Remove trailing comma
            line = line.rstrip(',').strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Parse the line as a column definition
            column_info = self._parse_single_column(line)
            if column_info:
                columns.append(column_info)
        
        return columns
    
    def _parse_single_column(self, column_def: str) -> Optional[Dict[str, Any]]:
        """Parse a single column definition"""
        try:
            # Remove trailing comma and clean up
            column_def = column_def.rstrip(',').strip()
            
            # Skip constraint lines
            if any(column_def.upper().startswith(constraint) for constraint in 
                   ['CONSTRAINT', 'PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE', 'CHECK']):
                return None
            
            # Split by whitespace but be careful with data types that have spaces
            # Use regex to find column name and data type
            column_match = re.match(r'(\w+)\s+([^,\s]+(?:\([^)]*\))?(?:\s+COLLATE\s+\S+)?)\s*(.*)', column_def)
            
            if not column_match:
                print(f"⚠️ Could not parse column: {column_def}")
                return None
            
            column_name = column_match.group(1).strip()
            data_type_part = column_match.group(2).strip()
            constraints_part = column_match.group(3).strip()
            
            # Parse data type
            data_type, char_length, numeric_precision, numeric_scale = self._parse_data_type(data_type_part)
            
            # Parse constraints
            constraint_text = constraints_part.upper()
            
            is_nullable = 'NOT NULL' not in constraint_text
            is_identity = 'IDENTITY' in constraint_text
            is_primary_key = 'PRIMARY KEY' in constraint_text
            
            # Extract default value
            default_value = None
            default_match = re.search(r'DEFAULT\s+([^,\s]+(?:\([^)]*\))?)', constraint_text)
            if default_match:
                default_value = default_match.group(1)
            
            column_info = {
                'name': column_name,
                'data_type': data_type,
                'is_nullable': is_nullable,
                'column_default': default_value,
                'character_maximum_length': char_length,
                'numeric_precision': numeric_precision,
                'numeric_scale': numeric_scale,
                'ordinal_position': 0,  # Will be set later
                'column_description': f'{column_name} column in healthcare database',
                'is_primary_key': is_primary_key,
                'is_foreign_key': False,  # Will be determined separately
                'is_identity': is_identity
            }
            
            return column_info
            
        except Exception as e:
            print(f"⚠️ Error parsing column: {column_def} - {e}")
            return None
    
    def _parse_data_type(self, data_type_part: str) -> tuple:
        """Parse data type and extract length/precision information"""
        data_type = data_type_part.lower()
        char_length = None
        numeric_precision = None
        numeric_scale = None
        
        # Handle data types with parameters
        if '(' in data_type:
            base_type = data_type.split('(')[0]
            params_str = data_type.split('(')[1].split(')')[0]
            
            if ',' in params_str:
                # Numeric type with precision and scale
                parts = params_str.split(',')
                numeric_precision = int(parts[0].strip()) if parts[0].strip().isdigit() else None
                numeric_scale = int(parts[1].strip()) if parts[1].strip().isdigit() else None
            else:
                # Character type with length
                if params_str.strip().isdigit():
                    char_length = int(params_str.strip())
                elif params_str.strip().upper() == 'MAX':
                    char_length = -1  # Use -1 to indicate MAX
            
            data_type = base_type
        
        return data_type, char_length, numeric_precision, numeric_scale
    
    def _extract_primary_keys(self, columns_section: str) -> List[str]:
        """Extract primary key column names"""
        primary_keys = []
        
        # Look for CONSTRAINT ... PRIMARY KEY
        pk_pattern = r'CONSTRAINT\s+\w+\s+PRIMARY\s+KEY\s*\(([^)]+)\)'
        pk_match = re.search(pk_pattern, columns_section, re.IGNORECASE)
        
        if pk_match:
            pk_columns = pk_match.group(1)
            # Split by comma and clean up
            for col in pk_columns.split(','):
                col_name = col.strip().strip('[]')
                primary_keys.append(col_name)
        else:
            # Look for inline PRIMARY KEY
            lines = columns_section.split('\n')
            for line in lines:
                if 'PRIMARY KEY' in line.upper() and not line.strip().upper().startswith('CONSTRAINT'):
                    # Extract column name
                    parts = line.strip().split()
                    if parts:
                        col_name = parts[0].strip()
                        primary_keys.append(col_name)
        
        return primary_keys
    
    def _extract_foreign_keys(self, columns_section: str) -> List[Dict[str, str]]:
        """Extract foreign key information"""
        foreign_keys = []
        
        # Pattern for CONSTRAINT ... FOREIGN KEY
        fk_pattern = r'CONSTRAINT\s+(\w+)\s+FOREIGN\s+KEY\s*\(([^)]+)\)\s+REFERENCES\s+([^.]+)\.([^.]+)\.([^(]+)\(([^)]+)\)'
        
        fk_matches = re.findall(fk_pattern, columns_section, re.IGNORECASE)
        
        for match in fk_matches:
            constraint_name, fk_column, ref_db, ref_schema, ref_table, ref_column = match
            
            fk_column = fk_column.strip().strip('[]')
            ref_table = ref_table.strip()
            ref_column = ref_column.strip().strip('[]')
            
            foreign_keys.append({
                'column': fk_column,
                'references_table': ref_table,
                'references_column': ref_column,
                'constraint_name': constraint_name.strip()
            })
        
        return foreign_keys
    
    def get_table_names(self) -> List[str]:
        """Get list of all table names"""
        if not self.parsed_schema:
            self.parse_schema_file()
        
        return list(self.parsed_schema.keys())
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get information for a specific table"""
        if not self.parsed_schema:
            self.parse_schema_file()
        
        return self.parsed_schema.get(table_name)
    
    def get_all_tables(self) -> Dict[str, Any]:
        """Get all table information"""
        if not self.parsed_schema:
            self.parse_schema_file()
        
        return self.parsed_schema
    
    def get_table_relationships(self, table_name: str) -> Dict[str, List[Dict]]:
        """Get relationships for a specific table"""
        if not self.parsed_schema:
            self.parse_schema_file()
        
        relationships = {
            'outgoing': [],  # Foreign keys from this table to others
            'incoming': []   # Foreign keys from other tables to this table
        }
        
        # Get outgoing relationships (foreign keys from this table)
        table_info = self.parsed_schema.get(table_name, {})
        if table_info:
            for fk in table_info.get('foreign_keys', []):
                relationships['outgoing'].append({
                    'local_column': fk['column'],
                    'referenced_table': fk['references_table'],
                    'referenced_column': fk['references_column'],
                    'constraint_name': fk['constraint_name']
                })
        
        # Get incoming relationships (foreign keys from other tables to this table)
        for other_table, other_info in self.parsed_schema.items():
            if other_table != table_name:
                for fk in other_info.get('foreign_keys', []):
                    if fk['references_table'] == table_name:
                        relationships['incoming'].append({
                            'from_table': other_table,
                            'from_column': fk['column'],
                            'to_column': fk['references_column'],
                            'constraint_name': fk['constraint_name']
                        })
        
        return relationships
    
    def generate_join_suggestions(self, table1: str, table2: str) -> List[str]:
        """Generate JOIN suggestions between two tables"""
        suggestions = []
        
        if not self.parsed_schema:
            self.parse_schema_file()
        
        table1_info = self.parsed_schema.get(table1, {})
        table2_info = self.parsed_schema.get(table2, {})
        
        if not table1_info or not table2_info:
            return suggestions
        
        # Check direct foreign key relationships
        # Table1 -> Table2
        for fk in table1_info.get('foreign_keys', []):
            if fk['references_table'] == table2:
                suggestions.append(f"JOIN {table2} ON {table1}.{fk['column']} = {table2}.{fk['references_column']}")
        
        # Table2 -> Table1
        for fk in table2_info.get('foreign_keys', []):
            if fk['references_table'] == table1:
                suggestions.append(f"JOIN {table1} ON {table2}.{fk['column']} = {table1}.{fk['references_column']}")
        
        return suggestions
    
    def get_related_tables(self, table_name: str, max_depth: int = 2) -> Dict[str, List[Dict]]:
        """Get all tables related to the given table up to max_depth"""
        if not self.parsed_schema:
            self.parse_schema_file()
        
        related = {
            'direct': [],
            'indirect': []
        }
        
        visited = set()
        queue = [(table_name, 0)]
        
        while queue:
            current_table, depth = queue.pop(0)
            if current_table in visited or depth > max_depth:
                continue
            
            visited.add(current_table)
            relationships = self.get_table_relationships(current_table)
            
            # Process outgoing relationships
            for rel in relationships['outgoing']:
                ref_table = rel['referenced_table']
                relationship_info = {
                    'table': ref_table,
                    'relationship': f"{current_table}.{rel['local_column']} → {ref_table}.{rel['referenced_column']}",
                    'type': 'outgoing',
                    'join_condition': f"{current_table}.{rel['local_column']} = {ref_table}.{rel['referenced_column']}"
                }
                
                if depth == 0:
                    related['direct'].append(relationship_info)
                elif depth == 1:
                    relationship_info['through'] = current_table
                    related['indirect'].append(relationship_info)
                
                if depth < max_depth:
                    queue.append((ref_table, depth + 1))
            
            # Process incoming relationships
            for rel in relationships['incoming']:
                from_table = rel['from_table']
                relationship_info = {
                    'table': from_table,
                    'relationship': f"{from_table}.{rel['from_column']} → {current_table}.{rel['to_column']}",
                    'type': 'incoming',
                    'join_condition': f"{from_table}.{rel['from_column']} = {current_table}.{rel['to_column']}"
                }
                
                if depth == 0:
                    related['direct'].append(relationship_info)
                elif depth == 1:
                    relationship_info['through'] = current_table
                    related['indirect'].append(relationship_info)
                
                if depth < max_depth:
                    queue.append((from_table, depth + 1))
        
        return related
    
    def generate_table_summary_with_relationships(self, table_name: str) -> str:
        """Generate a comprehensive summary including relationships"""
        if not self.parsed_schema:
            self.parse_schema_file()
        
        table_info = self.parsed_schema.get(table_name)
        if not table_info:
            return f"Table '{table_name}' not found."
        
        summary = f"Table: {table_name}\n"
        summary += f"Description: {table_info.get('table_description', 'No description')}\n"
        summary += f"Schema: {table_info.get('table_schema', 'dbo')}\n\n"
        
        # Primary Keys
        primary_keys = table_info.get('primary_keys', [])
        if primary_keys:
            summary += f"Primary Key(s): {', '.join(primary_keys)}\n\n"
        
        # Columns
        summary += "Columns:\n"
        for i, col in enumerate(table_info.get('columns', []), 1):
            summary += f"  {i:2d}. {col['name']} ({col['data_type']}"
            if col.get('character_maximum_length'):
                summary += f"({col['character_maximum_length']})"
            elif col.get('numeric_precision'):
                summary += f"({col['numeric_precision']},{col.get('numeric_scale', 0)})"
            summary += ")"
            
            if not col['is_nullable']:
                summary += " NOT NULL"
            if col.get('is_identity'):
                summary += " IDENTITY"
            if col.get('column_default'):
                summary += f" DEFAULT {col['column_default']}"
            if col.get('is_primary_key'):
                summary += " PRIMARY KEY"
            summary += "\n"
        
        # Foreign Keys (Outgoing)
        fks = table_info.get('foreign_keys', [])
        if fks:
            summary += "\nForeign Keys (Outgoing References):\n"
            for fk in fks:
                summary += f"  - {fk['column']} → {fk['references_table']}.{fk['references_column']}\n"
        
        # Incoming References
        relationships = self.get_table_relationships(table_name)
        if relationships['incoming']:
            summary += "\nIncoming References (Tables that reference this table):\n"
            for rel in relationships['incoming']:
                summary += f"  - {rel['from_table']}.{rel['from_column']} → {table_name}.{rel['to_column']}\n"
        
        # Related Tables
        related = self.get_related_tables(table_name, max_depth=1)
        if related['direct']:
            summary += "\nDirectly Related Tables:\n"
            for rel in related['direct']:
                summary += f"  - {rel['table']} ({rel['type']}): {rel['join_condition']}\n"
        
        return summary
    
    def generate_query_context(self, tables: List[str]) -> str:
        """Generate context for query generation including relationship information"""
        if not self.parsed_schema:
            self.parse_schema_file()
        
        context = "Database Schema Context:\n\n"
        
        for table_name in tables:
            table_info = self.parsed_schema.get(table_name)
            if not table_info:
                continue
            
            context += f"Table: {table_name}\n"
            context += f"Description: {table_info.get('table_description', 'Healthcare table')}\n"
            
            # Columns
            context += "Columns:\n"
            for col in table_info.get('columns', []):
                context += f"  - {col['name']} ({col['data_type']}"
                if not col['is_nullable']:
                    context += ", NOT NULL"
                if col.get('is_primary_key'):
                    context += ", PRIMARY KEY"
                context += ")\n"
            
            # Relationships
            relationships = self.get_table_relationships(table_name)
            if relationships['outgoing']:
                context += "References:\n"
                for rel in relationships['outgoing']:
                    context += f"  - {rel['local_column']} → {rel['referenced_table']}.{rel['referenced_column']}\n"
            
            context += "\n"
        
        # Generate JOIN suggestions
        if len(tables) > 1:
            context += "Suggested JOINs:\n"
            for i, table1 in enumerate(tables):
                for table2 in tables[i+1:]:
                    joins = self.generate_join_suggestions(table1, table2)
                    for join in joins:
                        context += f"  - {join}\n"
            context += "\n"
        
        return context


# Helper function to create parser
def create_schema_parser(schema_file_path: str = None) -> SQLSchemaParser:
    """Create a schema parser instance"""
    if schema_file_path is None:
        # Default to chatbot_schema.sql in current directory
        schema_file_path = os.path.join(os.getcwd(), 'chatbot_schema.sql')
    
    return SQLSchemaParser(schema_file_path)


if __name__ == "__main__":
    # Test the parser
    parser = create_schema_parser()
    schema = parser.parse_schema_file()
    
    print(f"\nParsed {len(schema)} tables:")
    for table_name in schema.keys():
        table_info = schema[table_name]
        print(f"  - {table_name}: {len(table_info['columns'])} columns")
