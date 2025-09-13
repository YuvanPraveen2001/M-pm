#!/usr/bin/env python3
"""
Test script to verify the complete RAG system with foreign key relationships
"""

import json
from dynamic_schema_manager import get_dynamic_schema_manager
from sql_schema_parser import create_schema_parser

def test_schema_rag_with_relationships():
    """Test the complete schema RAG system including relationships"""
    print("=== Testing Schema RAG System with Foreign Key Relationships ===\n")
    
    # Initialize components
    manager = get_dynamic_schema_manager()
    parser = create_schema_parser()
    
    print("1. Schema Status:")
    status = manager.get_schema_status()
    print(f"   - Total tables: {status['total_tables']}")
    print(f"   - Vector DB ready: {status['vector_database_ready']}")
    print(f"   - Embedding model ready: {status['embedding_model_ready']}")
    print(f"   - Chat model ready: {status['chat_model_ready']}")
    
    print("\n2. Testing Specific Relationship Queries:")
    
    # Test 1: Employee availability query
    print("\n   Test 1: Employee Availability Query")
    relevant_schema = manager.get_schema_for_query("show employees available on wednesday")
    print(f"   - Found {len(relevant_schema['tables'])} relevant tables")
    print(f"   - Search method: {relevant_schema['search_method']}")
    
    # Show the specific tables and their relationships
    for table in relevant_schema['tables']:
        if table['table_name'] in ['Employee', 'EmployeeAvailabilityDateTime']:
            print(f"   - {table['table_name']}: {len(table['columns'])} columns")
            if table['foreign_keys']:
                print(f"     Foreign keys: {len(table['foreign_keys'])}")
                for fk in table['foreign_keys']:
                    print(f"       {fk['column']} → {fk['references_table']}.{fk['references_column']}")
    
    # Test 2: Appointment booking query
    print("\n   Test 2: Appointment Booking Query")
    relevant_schema = manager.get_schema_for_query("book appointment with therapist for patient")
    appointment_tables = [t for t in relevant_schema['tables'] if t['table_name'] in ['Appointment', 'Patient', 'Employee']]
    
    print(f"   - Found {len(appointment_tables)} core appointment tables")
    for table in appointment_tables:
        print(f"   - {table['table_name']}: {len(table['foreign_keys'])} foreign keys")
    
    # Test 3: Generate JOIN suggestions
    print("\n3. Testing JOIN Suggestions:")
    joins = parser.generate_join_suggestions('Employee', 'EmployeeAvailabilityDateTime')
    print("   Employee ↔ EmployeeAvailabilityDateTime:")
    for join in joins:
        print(f"   - {join}")
    
    joins = parser.generate_join_suggestions('Appointment', 'Patient')
    print("   Appointment ↔ Patient:")
    for join in joins:
        print(f"   - {join}")
    
    joins = parser.generate_join_suggestions('Appointment', 'Employee')
    print("   Appointment ↔ Employee:")
    for join in joins:
        print(f"   - {join}")
    
    # Test 4: Related tables analysis
    print("\n4. Related Tables Analysis:")
    related = parser.get_related_tables('Employee', max_depth=1)
    print(f"   Employee - Direct relationships: {len(related['direct'])}")
    for rel in related['direct'][:5]:  # Show first 5
        print(f"   - {rel['table']} ({rel['type']}): {rel['join_condition']}")
    
    related = parser.get_related_tables('Appointment', max_depth=1)
    print(f"   Appointment - Direct relationships: {len(related['direct'])}")
    for rel in related['direct'][:5]:  # Show first 5
        print(f"   - {rel['table']} ({rel['type']}): {rel['join_condition']}")
    
    # Test 5: Query context generation
    print("\n5. Query Context Generation:")
    context = parser.generate_query_context(['Employee', 'EmployeeAvailabilityDateTime', 'Gender'])
    print("   Context for Employee + Availability + Gender:")
    print(context[:500] + "..." if len(context) > 500 else context)
    
    # Test 6: SQL generation with relationships
    print("\n6. SQL Generation Test:")
    sql = manager.generate_sql_with_current_schema(
        "show all female employees available on wednesday", 
        relevant_schema['tables']
    )
    print("   Generated SQL:")
    print(f"   {sql}")
    
    # Test 7: Complex relationship analysis
    print("\n7. Complex Relationship Analysis:")
    employee_rels = parser.get_table_relationships('Employee')
    print(f"   Employee relationships:")
    print(f"   - Outgoing FKs: {len(employee_rels['outgoing'])}")
    print(f"   - Incoming FKs: {len(employee_rels['incoming'])}")
    
    appointment_rels = parser.get_table_relationships('Appointment')
    print(f"   Appointment relationships:")
    print(f"   - Outgoing FKs: {len(appointment_rels['outgoing'])}")
    print(f"   - Incoming FKs: {len(appointment_rels['incoming'])}")
    
    # Test 8: Schema summary with relationships
    print("\n8. Table Summary with Relationships:")
    summary = parser.generate_table_summary_with_relationships('EmployeeAvailabilityDateTime')
    print(summary[:800] + "..." if len(summary) > 800 else summary)
    
    print("\n=== RAG System Test Complete ===")

if __name__ == "__main__":
    test_schema_rag_with_relationships()
