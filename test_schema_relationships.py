#!/usr/bin/env python3
"""
Test script to verify foreign key relationships are captured correctly
"""

from sql_schema_parser import create_schema_parser

def test_relationships():
    """Test relationship parsing"""
    parser = create_schema_parser()
    schema = parser.parse_schema_file()
    
    print("=== Testing Foreign Key Relationships ===\n")
    
    # Test Appointment table relationships
    print("1. Appointment Table Relationships:")
    appointment_rels = parser.get_table_relationships('Appointment')
    print(f"   Outgoing FKs: {len(appointment_rels['outgoing'])}")
    for fk in appointment_rels['outgoing']:
        print(f"   - {fk['local_column']} → {fk['referenced_table']}.{fk['referenced_column']}")
    
    print(f"   Incoming FKs: {len(appointment_rels['incoming'])}")
    for fk in appointment_rels['incoming']:
        print(f"   - {fk['from_table']}.{fk['from_column']} → Appointment.{fk['to_column']}")
    
    print("\n2. Employee Table Relationships:")
    employee_rels = parser.get_table_relationships('Employee')
    print(f"   Outgoing FKs: {len(employee_rels['outgoing'])}")
    for fk in employee_rels['outgoing']:
        print(f"   - {fk['local_column']} → {fk['referenced_table']}.{fk['referenced_column']}")
    
    print(f"   Incoming FKs: {len(employee_rels['incoming'])}")
    for fk in employee_rels['incoming'][:5]:  # Show first 5 to avoid clutter
        print(f"   - {fk['from_table']}.{fk['from_column']} → Employee.{fk['to_column']}")
    
    print("\n3. JOIN Suggestions:")
    joins = parser.generate_join_suggestions('Employee', 'Appointment')
    print(f"   Employee ↔ Appointment:")
    for join in joins:
        print(f"   - {join}")
    
    joins = parser.generate_join_suggestions('Patient', 'Appointment')
    print(f"   Patient ↔ Appointment:")
    for join in joins:
        print(f"   - {join}")
    
    print("\n4. Related Tables (Employee):")
    related = parser.get_related_tables('Employee', max_depth=1)
    print(f"   Direct relationships: {len(related['direct'])}")
    for rel in related['direct'][:10]:  # Show first 10
        print(f"   - {rel['table']} ({rel['type']}): {rel['join_condition']}")
    
    print("\n5. Query Context Generation:")
    context = parser.generate_query_context(['Employee', 'Appointment', 'Patient'])
    print(context[:1000] + "..." if len(context) > 1000 else context)
    
    print("\n6. Table Summary with Relationships:")
    summary = parser.generate_table_summary_with_relationships('EmployeeAvailabilityDateTime')
    print(summary)

if __name__ == "__main__":
    test_relationships()
