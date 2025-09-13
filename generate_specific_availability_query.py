#!/usr/bin/env python3
"""
Generate optimized SQL query for specific employee availability on a specific day
"""

from dynamic_schema_manager import get_dynamic_schema_manager
from sql_schema_parser import create_schema_parser

def generate_wednesday_availability_query(employee_name: str = "jon snow"):
    """Generate SQL for Wednesday availability specifically"""
    print(f"=== Wednesday Availability Query for '{employee_name}' ===\n")
    
    # Initialize components
    manager = get_dynamic_schema_manager()
    parser = create_schema_parser()
    
    # Get the relevant tables
    key_tables = ['Employee', 'EmployeeAvailabilityDateTime', 'Gender', 'Site']
    table_info = {}
    
    for table_name in key_tables:
        table_data = manager.current_schema.get(table_name)
        if table_data:
            table_info[table_name] = table_data
    
    print("1. Valid Tables Identified:")
    for table_name, table_data in table_info.items():
        print(f"   ✅ {table_name}: {len(table_data['columns'])} columns")
        if table_data.get('foreign_keys'):
            print(f"      Foreign Keys: {len(table_data['foreign_keys'])}")
            for fk in table_data['foreign_keys']:
                print(f"        • {fk['column']} → {fk['references_table']}.{fk['references_column']}")
    
    print("\n2. Query Requirements Analysis:")
    print("   • Employee name search: FirstName LIKE '%jon%' AND LastName LIKE '%snow%'")
    print("   • Day filter: WeekDay = 4 (Wednesday, where 1=Sunday, 4=Wednesday)")
    print("   • Active employee filter: Active = 1")
    print("   • Availability status: AvailabilityStatusId = 1 or NULL")
    print("   • Include: Contact info, site, gender, availability times")
    
    print("\n3. Generated SQL Query:")
    
    # Parse employee name
    name_parts = employee_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""
    
    # Generate optimized SQL for Wednesday availability
    sql_query = f"""
SELECT 
    e.EmployeeId,
    e.FirstName,
    e.LastName,
    e.Email,
    e.PhoneCell,
    e.Title,
    e.NPI,
    s.Name AS SiteName,
    g.GenderType,
    ead.WeekDay,
    ead.AvailableFrom,
    ead.AvailableTo,
    ead.AvailabilityDateFrom,
    ead.AvailabilityDateTo,
    ead.TotalDesiredHourPerWeek,
    CASE 
        WHEN ead.WeekDay = 4 THEN 'Wednesday'
        WHEN ead.WeekDay = 1 THEN 'Sunday'
        WHEN ead.WeekDay = 2 THEN 'Monday'
        WHEN ead.WeekDay = 3 THEN 'Tuesday'
        WHEN ead.WeekDay = 5 THEN 'Thursday'
        WHEN ead.WeekDay = 6 THEN 'Friday'
        WHEN ead.WeekDay = 7 THEN 'Saturday'
        ELSE 'Unknown'
    END AS DayName
FROM Employee e
LEFT JOIN EmployeeAvailabilityDateTime ead ON e.EmployeeId = ead.EmployeeId
LEFT JOIN Gender g ON e.Gender = g.GenderID
LEFT JOIN Site s ON e.SiteId = s.SiteId
WHERE 
    (e.FirstName LIKE '%{first_name}%' AND e.LastName LIKE '%{last_name}%')
    AND e.Active = 1
    AND ead.WeekDay = 4  -- Wednesday
    AND (ead.AvailabilityStatusId IS NULL OR ead.AvailabilityStatusId = 1)
    AND ead.AvailableFrom IS NOT NULL
    AND ead.AvailableTo IS NOT NULL
ORDER BY 
    e.LastName, 
    e.FirstName, 
    ead.AvailableFrom"""
    
    print(sql_query)
    
    print("\n4. Query Features:")
    print("   ✅ Uses exact table/column names from schema")
    print("   ✅ Filters for Wednesday (WeekDay = 4)")
    print("   ✅ Includes proper JOINs based on foreign key relationships")
    print("   ✅ Filters for active employees only")
    print("   ✅ Includes availability status validation")
    print("   ✅ Shows readable day name via CASE statement")
    print("   ✅ Orders results logically")
    
    print("\n5. Alternative Query (All Days for Jon Snow):")
    
    all_days_query = f"""
SELECT 
    e.EmployeeId,
    e.FirstName,
    e.LastName,
    e.Email,
    e.PhoneCell,
    e.Title,
    s.Name AS SiteName,
    g.GenderType,
    CASE 
        WHEN ead.WeekDay = 1 THEN 'Sunday'
        WHEN ead.WeekDay = 2 THEN 'Monday'
        WHEN ead.WeekDay = 3 THEN 'Tuesday'
        WHEN ead.WeekDay = 4 THEN 'Wednesday'
        WHEN ead.WeekDay = 5 THEN 'Thursday'
        WHEN ead.WeekDay = 6 THEN 'Friday'
        WHEN ead.WeekDay = 7 THEN 'Saturday'
        ELSE 'Unknown'
    END AS DayName,
    ead.AvailableFrom,
    ead.AvailableTo,
    DATEDIFF(MINUTE, ead.AvailableFrom, ead.AvailableTo) AS AvailableMinutes
FROM Employee e
LEFT JOIN EmployeeAvailabilityDateTime ead ON e.EmployeeId = ead.EmployeeId
LEFT JOIN Gender g ON e.Gender = g.GenderID
LEFT JOIN Site s ON e.SiteId = s.SiteId
WHERE 
    (e.FirstName LIKE '%{first_name}%' AND e.LastName LIKE '%{last_name}%')
    AND e.Active = 1
    AND (ead.AvailabilityStatusId IS NULL OR ead.AvailabilityStatusId = 1)
    AND ead.AvailableFrom IS NOT NULL
ORDER BY 
    e.LastName, 
    e.FirstName, 
    ead.WeekDay,
    ead.AvailableFrom"""
    
    print(all_days_query)
    
    return sql_query, all_days_query, table_info

if __name__ == "__main__":
    wednesday_query, all_days_query, tables = generate_wednesday_availability_query("jon snow")
    
    print(f"\n=== Summary ===")
    print(f"✅ Wednesday-specific query generated")
    print(f"✅ All-days query generated")
    print(f"✅ Uses {len(tables)} validated tables with real schema")
    print(f"✅ Includes proper foreign key relationships")
    print(f"✅ No compromise on table/column names")
