"""
Enhanced SQL generation for specific availability queries
Handles complex employee availability queries with metadata filtering
Uses Ollama LLM for intelligent query generation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re

# Import model configuration and LLM
from model_config import CHAT_MODEL, get_chat_model_config

try:
    from langchain_community.chat_models import ChatOllama
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LLM_AVAILABLE = True
except ImportError:
    print("Warning: LangChain not available, using rule-based SQL generation")
    ChatOllama = None
    LLM_AVAILABLE = False


class AvailabilityQueryGenerator:
    """Generate SQL queries for employee availability based on complex criteria"""
    
    def __init__(self):
        """Initialize the availability query generator"""
        self.weekday_mapping = {
            'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4,
            'friday': 5, 'saturday': 6, 'sunday': 7
        }
        
        # Initialize LLM if available
        self.llm_available = False
        self.chat_model = None
        
        if LLM_AVAILABLE:
            try:
                self.chat_model = ChatOllama(model=CHAT_MODEL, temperature=0.1)
                self.llm_available = True
                print(f"✅ Availability Query Generator: Using LLM {CHAT_MODEL}")
            except Exception as e:
                print(f"⚠️ Availability Query Generator: LLM not available, using rule-based generation: {e}")
        else:
            print("ℹ️ Availability Query Generator: Using rule-based SQL generation")
    
    def generate_availability_query(self, query_text: str, metadata: Dict[str, Any]) -> str:
        """
        Generate SQL query for employee availability based on user request and metadata
        
        Args:
            query_text: Natural language request (e.g., "need a list of available employees on this wednesday")
            metadata: Dict containing filters like gender, site_id, today's date
            
        Returns:
            SQL query string
        """
        
        # Try LLM-based generation first if available
        if self.llm_available and self.chat_model:
            try:
                return self._generate_with_llm(query_text, metadata)
            except Exception as e:
                print(f"⚠️ LLM generation failed, falling back to rule-based: {e}")
        
        # Fallback to rule-based generation
        return self._generate_rule_based(query_text, metadata)
    
    def _generate_with_llm(self, query_text: str, metadata: Dict[str, Any]) -> str:
        """Generate SQL using LLM with healthcare schema knowledge"""
        
        # Prepare context
        schema_context = """
Healthcare Database Schema for Employee Availability:

Table: Employee
- EmployeeId (int, PRIMARY KEY)
- FirstName (varchar)
- LastName (varchar) 
- EmployeeName (computed: FirstName + ' ' + LastName)
- Title (varchar)
- Gender (varchar)
- SiteId (int, FOREIGN KEY to Location)

Table: Location
- LocationId (int, PRIMARY KEY)
- SiteId (int)
- LocationName (varchar)
- Address (varchar)

Table: Appointment (for checking existing bookings)
- AppointmentId (int, PRIMARY KEY)
- PatientId (int, FOREIGN KEY)
- EmployeeId (int, FOREIGN KEY to Employee)
- AppointmentDate (date)
- AppointmentTime (time)
- Duration (int, minutes)
- Status (varchar)

Common patterns:
- Filter by Gender: WHERE e.Gender = 'Male' or 'Female'
- Filter by Site: WHERE e.SiteId = [number]
- Date filtering: Use DATEPART(WEEKDAY, date) for weekdays (1=Sunday, 2=Monday, ..., 4=Wednesday)
- Availability check: LEFT JOIN with Appointment to find free slots
"""
        
        # Format metadata for prompt (excluding location criteria as requested)
        filters_text = []
        if metadata.get('gender'):
            filters_text.append(f"Gender: {metadata['gender']}")
        # Removing location/site filtering as requested
        # if metadata.get('site_id') or metadata.get('SiteId'):
        #     site_id = metadata.get('site_id') or metadata.get('SiteId')
        #     filters_text.append(f"Site ID: {site_id}")
        if metadata.get('target_date'):
            filters_text.append(f"Target date: {metadata['target_date']}")
        
        filters_str = ", ".join(filters_text) if filters_text else "No specific filters"
        
        # Create prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", f"""You are a SQL expert for a healthcare database. Generate a precise SQL query to find available employees based on the user request and filters.

{schema_context}

Requirements:
1. Return employee information including name, title, gender
2. Apply the specified filters (exclude location/site criteria for now)
3. Use proper JOIN syntax with EmployeeAvailabilityDateTime for availability
4. Format results clearly with availability status
5. Return only the SQL query without explanations
6. Use table aliases (e for Employee, ead for EmployeeAvailabilityDateTime, g for Gender)
7. Focus on weekday availability matching and appointment conflicts

User Request: {{user_request}}
Filters: {{filters}}"""),
            ("human", "{user_request}")
        ])
        
        # Generate SQL
        chain = prompt_template | self.chat_model | StrOutputParser()
        
        sql_query = chain.invoke({
            "user_request": query_text,
            "filters": filters_str
        })
        
        # Clean up the SQL
        sql_query = sql_query.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        return sql_query.strip()
    
    def _generate_rule_based(self, query_text: str, metadata: Dict[str, Any]) -> str:
        """Generate SQL using rule-based approach (fallback)"""
        
        # Parse the request
        target_weekday = self._extract_weekday(query_text)
        date_range_days = 30  # Default 30 days as specified
        
        # Extract metadata (excluding location criteria as requested)
        gender = metadata.get('gender', None)
        # site_id = metadata.get('SiteId', None)  # Commented out - avoiding location criteria
        today_date = metadata.get("today's date", datetime.now().strftime('%Y-%m-%d'))
        
        # Calculate date range
        today = datetime.strptime(today_date, '%Y-%m-%d') if isinstance(today_date, str) else today_date
        end_date = today + timedelta(days=date_range_days)
        
        # Build the query
        query = f"""
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
        -- Calculate next occurrence of target weekday
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
        AND (ead.AvailabilityDateFrom IS NULL OR ead.AvailabilityDateFrom <= DATEADD(day, {date_range_days}, GETDATE()))
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
        AND a.AppointmentStatusId IN (1, 2)  -- Active/Scheduled appointments
        AND (
            (CAST(a.ScheduledDate AS TIME) BETWEEN ae.AvailableFrom AND ae.AvailableTo)
            OR 
            (DATEADD(minute, a.ScheduledMinutes, CAST(a.ScheduledDate AS TIME)) BETWEEN ae.AvailableFrom AND ae.AvailableTo)
        )
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
    END as AvailabilityStatus,
    -- Calculate available time slots
    CASE 
        WHEN ISNULL(ca.ConflictCount, 0) = 0 
        THEN CAST(DATEDIFF(minute, ae.AvailableFrom, ae.AvailableTo) / 60.0 AS DECIMAL(5,2))
        ELSE CAST((DATEDIFF(minute, ae.AvailableFrom, ae.AvailableTo) - (ISNULL(ca.ConflictCount, 0) * 60)) / 60.0 AS DECIMAL(5,2))
    END as AvailableHours
FROM AvailableEmployees ae
LEFT JOIN ConflictingAppointments ca ON ae.EmployeeId = ca.EmployeeId
WHERE ae.NextAvailableDate <= '{end_date.strftime('%Y-%m-%d')}'
ORDER BY 
    CASE 
        WHEN ISNULL(ca.ConflictCount, 0) = 0 THEN 1  -- Fully available first
        WHEN ISNULL(ca.ConflictCount, 0) < 3 THEN 2  -- Partially available second
        ELSE 3  -- Busy last
    END,
    ae.AvailableFrom ASC,
    ae.FirstName ASC;
"""
        
        return query.strip()
    
    def _extract_weekday(self, text: str) -> int:
        """Extract weekday number from text (1=Monday, 7=Sunday)"""
        text_lower = text.lower()
        
        for day_name, day_num in self.weekday_mapping.items():
            if day_name in text_lower:
                return day_num
        
        # Default to Wednesday if not specified
        return 3
    
    def generate_simple_availability_query(self, employee_name: str, target_date: str = None) -> str:
        """Generate a simple availability query for a specific employee"""
        
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        # Calculate weekday for the target date
        target_datetime = datetime.strptime(target_date, '%Y-%m-%d')
        weekday = target_datetime.isoweekday()  # 1=Monday, 7=Sunday
        
        query = f"""
SELECT 
    e.EmployeeId,
    e.FirstName + ' ' + ISNULL(e.LastName, '') as EmployeeName,
    e.Email,
    e.Title,
    ead.WeekDay,
    FORMAT(ead.AvailableFrom, 'hh\\:mm tt') as AvailableFrom,
    FORMAT(ead.AvailableTo, 'hh\\:mm tt') as AvailableTo,
    '{target_date}' as TargetDate,
    -- Check for existing appointments
    (SELECT COUNT(*) 
     FROM Appointment a 
     WHERE a.EmployeeId = e.EmployeeId 
     AND CAST(a.ScheduledDate AS DATE) = '{target_date}'
     AND a.AppointmentStatusId IN (1, 2)
    ) as ExistingAppointments,
    -- Calculate available time slots
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM Appointment a2 
            WHERE a2.EmployeeId = e.EmployeeId 
            AND CAST(a2.ScheduledDate AS DATE) = '{target_date}'
            AND a2.AppointmentStatusId IN (1, 2)
        ) THEN 'Fully Available'
        ELSE 'Partially Available'
    END as AvailabilityStatus
FROM Employee e
INNER JOIN EmployeeAvailabilityDateTime ead ON e.EmployeeId = ead.EmployeeId
WHERE e.Active = 1
    AND ead.WeekDay = {weekday}
    AND (ead.AvailabilityDateFrom IS NULL OR ead.AvailabilityDateFrom <= '{target_date}')
    AND (ead.AvailabilityDateTo IS NULL OR ead.AvailabilityDateTo >= '{target_date}')
    AND (
        LOWER(e.FirstName) LIKE LOWER('%{employee_name}%')
        OR LOWER(e.LastName) LIKE LOWER('%{employee_name}%')
        OR LOWER(CONCAT(e.FirstName, ' ', e.LastName)) LIKE LOWER('%{employee_name}%')
    )
ORDER BY e.FirstName, ead.AvailableFrom;
"""
        
        return query.strip()


# Singleton instance
availability_query_generator = None

def get_availability_query_generator() -> AvailabilityQueryGenerator:
    """Get or create the availability query generator instance"""
    global availability_query_generator
    if availability_query_generator is None:
        availability_query_generator = AvailabilityQueryGenerator()
    return availability_query_generator
