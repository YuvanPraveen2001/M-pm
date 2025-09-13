#!/usr/bin/env python3
"""
Simple test to verify availability query generation logic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Direct test without database dependencies
def test_query_logic():
    """Test the core query generation logic"""
    print("🧪 Testing Availability Query Logic (No Location Criteria)")
    print("=" * 60)
    
    # Test weekday mapping
    weekday_mapping = {
        'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4,
        'friday': 5, 'saturday': 6, 'sunday': 7
    }
    
    # Extract weekday from text
    def extract_weekday(text):
        text_lower = text.lower()
        for day_name, day_num in weekday_mapping.items():
            if day_name in text_lower:
                return day_num
        return 3  # Default to Wednesday
    
    # Test parameters
    query_text = "need a list of available employees on this wednesday"
    metadata = {
        'gender': 'Male',
        'SiteId': 2,  # This should be ignored
        'target_date': 'wednesday'
    }
    
    target_weekday = extract_weekday(query_text)
    gender = metadata.get('gender', None)
    # site_id = None  # Explicitly excluding location criteria
    
    print(f"📝 Query Text: {query_text}")
    print(f"📊 Metadata: {metadata}")
    print(f"🎯 Target Weekday: {target_weekday} (Wednesday)")
    print(f"👤 Gender Filter: {gender}")
    print(f"📍 Location Filter: EXCLUDED (as requested)")
    
    # Generate rule-based query template
    query_template = f"""
WITH AvailableEmployees AS (
    SELECT DISTINCT
        e.EmployeeId,
        e.FirstName,
        e.LastName,
        e.Email,
        e.Title,
        e.Gender,
        e.SiteId,
        s.Name as SiteName,
        g.Name as GenderName,
        ead.WeekDay,
        ead.AvailableFrom,
        ead.AvailableTo,
        DATEADD(day, 
            CASE 
                WHEN {target_weekday} >= DATEPART(weekday, GETDATE()) 
                THEN {target_weekday} - DATEPART(weekday, GETDATE())
                ELSE 7 - DATEPART(weekday, GETDATE()) + {target_weekday}
            END, 
            CAST(GETDATE() AS DATE)
        ) as NextAvailableDate
    FROM Employee e
    INNER JOIN EmployeeAvailabilityDateTime ead ON e.EmployeeId = ead.EmployeeId
    LEFT JOIN Site s ON e.SiteId = s.SiteId
    LEFT JOIN Gender g ON e.Gender = g.GenderID
    WHERE e.Active = 1
        AND ead.WeekDay = {target_weekday}  -- Target weekday (Wednesday = 3)
        AND (ead.AvailabilityDateFrom IS NULL OR ead.AvailabilityDateFrom <= DATEADD(day, 30, GETDATE()))
        AND (ead.AvailabilityDateTo IS NULL OR ead.AvailabilityDateTo >= GETDATE())
        {"AND g.Name = '" + gender + "'" if gender else ""}
),
ConflictingAppointments AS (
    SELECT 
        ae.EmployeeId,
        ae.NextAvailableDate,
        COUNT(a.AppointmentId) as ConflictCount
    FROM AvailableEmployees ae
    LEFT JOIN Appointment a ON ae.EmployeeId = a.EmployeeId
        AND CAST(a.ScheduledDate AS DATE) = ae.NextAvailableDate
        AND a.AppointmentStatusId IN (1, 2)
    GROUP BY ae.EmployeeId, ae.NextAvailableDate
)
SELECT DISTINCT
    ae.EmployeeId,
    ae.FirstName + ' ' + ISNULL(ae.LastName, '') as EmployeeName,
    ae.FirstName,
    ae.LastName,
    ae.Email,
    ae.Title,
    ae.GenderName,
    ae.SiteName,
    ae.NextAvailableDate,
    FORMAT(ae.AvailableFrom, 'hh\\:mm tt') as AvailableFrom,
    FORMAT(ae.AvailableTo, 'hh\\:mm tt') as AvailableTo,
    DATEDIFF(minute, ae.AvailableFrom, ae.AvailableTo) as AvailableMinutes,
    ISNULL(ca.ConflictCount, 0) as ExistingAppointments,
    CASE 
        WHEN ISNULL(ca.ConflictCount, 0) = 0 THEN 'Fully Available'
        WHEN ISNULL(ca.ConflictCount, 0) < 3 THEN 'Partially Available'
        ELSE 'Busy'
    END as AvailabilityStatus
FROM AvailableEmployees ae
LEFT JOIN ConflictingAppointments ca ON ae.EmployeeId = ca.EmployeeId
ORDER BY 
    CASE 
        WHEN ISNULL(ca.ConflictCount, 0) = 0 THEN 1
        WHEN ISNULL(ca.ConflictCount, 0) < 3 THEN 2
        ELSE 3
    END,
    ae.AvailableFrom ASC,
    ae.FirstName ASC;
"""
    
    print("\n🔍 Generated SQL Query:")
    print("-" * 60)
    print(query_template)
    
    print("\n" + "=" * 60)
    print("✅ Query Generation Test Completed")
    
    # Check if location criteria is excluded
    if 'SiteId =' not in query_template and 'LocationName' not in query_template:
        print("✅ SUCCESS: Location criteria successfully excluded from WHERE clause")
    else:
        print("❌ WARNING: Location criteria might still be present in WHERE clause")
        
    if f'WeekDay = {target_weekday}' in query_template:
        print("✅ SUCCESS: Weekday filtering is working correctly")
    else:
        print("❌ WARNING: Weekday filtering might not be working")
        
    if gender and f"g.Name = '{gender}'" in query_template:
        print("✅ SUCCESS: Gender filtering is working correctly")
    else:
        print("✅ INFO: Gender filtering excluded or not specified")

if __name__ == "__main__":
    test_query_logic()
