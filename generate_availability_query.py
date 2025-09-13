#!/usr/bin/env python3
"""
Query generator for employee availability search
"""

from dynamic_schema_manager import get_dynamic_schema_manager
from sql_schema_parser import create_schema_parser

def get_availability_query_for_employee(employee_name: str):
    """Generate SQL query for employee availability"""
    print(f"=== Generating Availability Query for '{employee_name}' ===\n")
    
    # Initialize components
    manager = get_dynamic_schema_manager()
    parser = create_schema_parser()
    
    # Get relevant schema for availability query
    query = f"get availability of employee {employee_name}"
    relevant_schema = manager.get_schema_for_query(query)
    
    print("1. Schema Analysis:")
    print(f"   Search method: {relevant_schema['search_method']}")
    print(f"   Tables found: {len(relevant_schema['tables'])}")
    
    # Identify key tables for availability query
    key_tables = {}
    for table in relevant_schema['tables']:
        table_name = table['table_name']
        if table_name in ['Employee', 'EmployeeAvailabilityDateTime', 'Gender', 'Site']:
            key_tables[table_name] = table
            print(f"   ✅ {table_name}: {len(table['columns'])} columns")
    
    print("\n2. Table Relationships:")
    
    # Analyze relationships between key tables
    if 'Employee' in key_tables:
        employee_rels = parser.get_table_relationships('Employee')
        print(f"   Employee outgoing FKs: {len(employee_rels['outgoing'])}")
        for fk in employee_rels['outgoing']:
            if fk['referenced_table'] in ['Gender', 'Site']:
                print(f"     • {fk['local_column']} → {fk['referenced_table']}.{fk['referenced_column']}")
    
    # Check for Employee-EmployeeAvailabilityDateTime relationship
    if 'EmployeeAvailabilityDateTime' in key_tables:
        avail_cols = [col['name'] for col in key_tables['EmployeeAvailabilityDateTime']['columns']]
        if 'EmployeeId' in avail_cols:
            print(f"     • EmployeeAvailabilityDateTime.EmployeeId → Employee.EmployeeId (implicit FK)")
    
    print("\n3. Column Analysis:")
    
    # Show relevant columns for the query
    if 'Employee' in key_tables:
        emp_cols = key_tables['Employee']['columns']
        name_cols = [col for col in emp_cols if 'name' in col['name'].lower()]
        print(f"   Employee name columns:")
        for col in name_cols:
            print(f"     • {col['name']} ({col['data_type']})")
    
    if 'EmployeeAvailabilityDateTime' in key_tables:
        avail_cols = key_tables['EmployeeAvailabilityDateTime']['columns']
        time_cols = [col for col in avail_cols if any(word in col['name'].lower() for word in ['day', 'time', 'date', 'available'])]
        print(f"   Availability time columns:")
        for col in time_cols:
            print(f"     • {col['name']} ({col['data_type']})")
    
    print("\n4. Generated SQL Query:")
    
    # Generate the SQL query
    sql_query = generate_employee_availability_sql(employee_name, key_tables)
    print(f"   {sql_query}")
    
    print("\n5. Query Explanation:")
    print("   This query:")
    print("   • Searches for employees with matching first/last name")
    print("   • Joins with availability schedule")
    print("   • Includes gender and site information via foreign keys")
    print("   • Filters for active employees only")
    print("   • Shows availability time slots and days")
    
    return sql_query, key_tables

def generate_employee_availability_sql(employee_name: str, tables: dict) -> str:
    """Generate SQL for employee availability search"""
    
    # Parse employee name
    name_parts = employee_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""
    
    # Base query structure
    sql_parts = []
    
    # SELECT clause
    select_cols = [
        "e.EmployeeId",
        "e.FirstName",
        "e.LastName",
        "e.Email",
        "e.PhoneCell",
        "e.Title",
        "s.Name AS SiteName",
        "g.GenderType",
        "ead.WeekDay",
        "ead.AvailableFrom",
        "ead.AvailableTo",
        "ead.AvailabilityDateFrom",
        "ead.AvailabilityDateTo"
    ]
    
    sql_parts.append(f"SELECT {', '.join(select_cols)}")
    
    # FROM clause with JOINs
    sql_parts.append("FROM Employee e")
    
    # JOIN with availability table
    if 'EmployeeAvailabilityDateTime' in tables:
        sql_parts.append("LEFT JOIN EmployeeAvailabilityDateTime ead ON e.EmployeeId = ead.EmployeeId")
    
    # JOIN with Gender table
    if 'Gender' in tables:
        sql_parts.append("LEFT JOIN Gender g ON e.Gender = g.GenderID")
    
    # JOIN with Site table  
    if 'Site' in tables:
        sql_parts.append("LEFT JOIN Site s ON e.SiteId = s.SiteId")
    
    # WHERE clause
    where_conditions = []
    
    # Name matching
    if first_name and last_name:
        where_conditions.append(f"(e.FirstName LIKE '%{first_name}%' AND e.LastName LIKE '%{last_name}%')")
    elif first_name:
        where_conditions.append(f"(e.FirstName LIKE '%{first_name}%' OR e.LastName LIKE '%{first_name}%')")
    
    # Active employee filter
    where_conditions.append("e.Active = 1")
    
    # Availability status filter
    where_conditions.append("(ead.AvailabilityStatusId IS NULL OR ead.AvailabilityStatusId = 1)")
    
    if where_conditions:
        sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
    
    # ORDER BY
    sql_parts.append("ORDER BY e.LastName, e.FirstName, ead.WeekDay, ead.AvailableFrom")
    
    return "\n".join(sql_parts)

def test_specific_query():
    """Test the specific query from the user"""
    print("=== Testing Specific Query: 'get me the availibility of jon snow' ===\n")
    
    sql_query, tables = get_availability_query_for_employee("jon snow")
    
    print(f"\n=== Final SQL Query ===")
    print(sql_query)
    
    print(f"\n=== Tables Used ===")
    for table_name, table_info in tables.items():
        print(f"• {table_name}: {len(table_info['columns'])} columns")

if __name__ == "__main__":
    test_specific_query()
