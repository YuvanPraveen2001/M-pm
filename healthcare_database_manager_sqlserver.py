"""
Healthcare Database Manager for SQL Server
Handles operations for the real SQL Server healthcare management database
"""

import pyodbc
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import uuid
import os
import time
import functools
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def retry_db_operation(max_retries=3, delay=1, backoff=2):
    """
    Decorator for database operations with exponential backoff retry logic
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except pyodbc.Error as e:
                    retries += 1
                    error_code = str(e)
                    
                    # Check if it's a retryable error
                    retryable_errors = [
                        "42S02",  # Invalid object name
                        "08001",  # Connection timeout
                        "08S01",  # Communication link failure
                        "40001",  # Deadlock
                        "Connection refused",
                        "timeout"
                    ]
                    
                    is_retryable = any(err in error_code for err in retryable_errors)
                    
                    if retries >= max_retries or not is_retryable:
                        logger.error(f"Database operation failed after {retries} retries: {str(e)}")
                        raise
                    
                    logger.warning(f"Database operation failed (attempt {retries}/{max_retries}): {str(e)}")
                    logger.info(f"Retrying in {current_delay} seconds...")
                    time.sleep(current_delay)
                    current_delay *= backoff
                
                except Exception as e:
                    # For non-database errors, don't retry
                    logger.error(f"Non-retryable error in database operation: {str(e)}")
                    raise
            
            return None
        return wrapper
    return decorator

class HealthcareDatabaseManager:
    """Manages database operations for the healthcare booking chatbot"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or self._build_connection_string()
        print(f"🔍 DEBUG: Database manager initialized")
        print(f"🔍 DEBUG: Connection string: {self._mask_connection_string()}")
    
    def _build_connection_string(self) -> str:
        """Build SQL Server connection string from environment variables"""
        server = os.getenv('SQL_SERVER', 'localhost')
        database = os.getenv('SQL_DATABASE', 'AIStagingDB_20250811')
        username = os.getenv('SQL_USERNAME', '')
        password = os.getenv('SQL_PASSWORD', '')
        driver = os.getenv('SQL_DRIVER', 'ODBC Driver 18 for SQL Server')
        connection_timeout = os.getenv('SQL_CONNECTION_TIMEOUT', '30')
        command_timeout = os.getenv('SQL_COMMAND_TIMEOUT', '30')
        
        print(f"🔍 DEBUG: Building connection string for server: {server}, database: {database}")
        
        if username and password:
            connection_string = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;Connection Timeout={connection_timeout};Command Timeout={command_timeout};"
        else:
            # Use Windows Authentication
            connection_string = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;Connection Timeout={connection_timeout};Command Timeout={command_timeout};"
        
        return connection_string
    
    def _mask_connection_string(self) -> str:
        """Return a masked version of the connection string for logging"""
        masked = self.connection_string
        # Hide password
        if 'PWD=' in masked:
            start = masked.find('PWD=') + 4
            end = masked.find(';', start)
            if end == -1:
                end = len(masked)
            masked = masked[:start] + '***' + masked[end:]
        return masked
    
    def get_connection(self):
        """Get SQL Server database connection with enhanced error handling"""
        try:
            print("🔍 DEBUG: Attempting to connect to SQL Server...")
            connection = pyodbc.connect(self.connection_string)
            print("✅ DEBUG: Successfully connected to SQL Server")
            return connection
        except pyodbc.OperationalError as e:
            print(f"❌ ERROR: SQL Server connection failed: {str(e)}")
            if 'Login timeout expired' in str(e):
                print("💡 HINT: This usually means:")
                print("   1. SQL Server is not running or not accessible")
                print("   2. Firewall is blocking the connection")
                print("   3. Wrong server name/IP address")
                print("   4. Network connectivity issues")
            elif 'Login failed' in str(e):
                print("💡 HINT: Check your username and password in .env file")
            raise
        except Exception as e:
            print(f"❌ ERROR: Unexpected database connection error: {str(e)}")
            raise
    
    def search_patient_by_name(self, patient_name: str) -> List[Dict]:
        """Search for patients using fuzzy name matching with phonetic similarity"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # SQL Server-compatible patient search query with phonetic matching
            query = """
                WITH NameParts AS ( 
                    SELECT value AS Part, ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS PartNumber 
                    FROM STRING_SPLIT(?, ' ')
                    WHERE LEN(TRIM(value)) > 0
                ) 
                SELECT TOP 10
                    p.PatientId, 
                    p.FirstName, 
                    p.MiddleName, 
                    p.LastName,
                    p.DOB,
                    p.Email,
                    s.Name as SiteName,
                    -- Exact match score
                    CASE 
                        WHEN LOWER(TRIM(CONCAT(ISNULL(p.FirstName, ''), ' ', ISNULL(p.MiddleName, ''), ' ', ISNULL(p.LastName, '')))) = LOWER(TRIM(?)) THEN 100
                        WHEN LOWER(TRIM(CONCAT(ISNULL(p.FirstName, ''), ' ', ISNULL(p.LastName, '')))) = LOWER(TRIM(?)) THEN 95
                        ELSE 0 
                    END +
                    -- First name similarity using SOUNDEX
                    CASE 
                        WHEN LOWER(p.FirstName) = LOWER((SELECT Part FROM NameParts WHERE PartNumber = 1)) THEN 40
                        WHEN SOUNDEX(p.FirstName) = SOUNDEX((SELECT Part FROM NameParts WHERE PartNumber = 1)) THEN 30
                        WHEN LOWER(p.FirstName) LIKE LOWER((SELECT Part + '%' FROM NameParts WHERE PartNumber = 1)) THEN 25
                        ELSE 0 
                    END +
                    -- Last name similarity using SOUNDEX
                    CASE 
                        WHEN LOWER(p.LastName) = LOWER((SELECT Part FROM NameParts WHERE PartNumber = (SELECT MAX(PartNumber) FROM NameParts))) THEN 40
                        WHEN SOUNDEX(p.LastName) = SOUNDEX((SELECT Part FROM NameParts WHERE PartNumber = (SELECT MAX(PartNumber) FROM NameParts))) THEN 30
                        WHEN LOWER(p.LastName) LIKE LOWER((SELECT Part + '%' FROM NameParts WHERE PartNumber = (SELECT MAX(PartNumber) FROM NameParts))) THEN 25
                        ELSE 0 
                    END AS MatchScore
                FROM Patient p
                LEFT JOIN Site s ON p.SiteId = s.SiteId
                WHERE p.IsActive = 1
                AND (
                    SOUNDEX(p.FirstName) = SOUNDEX((SELECT Part FROM NameParts WHERE PartNumber = 1))
                    OR SOUNDEX(p.LastName) = SOUNDEX((SELECT Part FROM NameParts WHERE PartNumber = (SELECT MAX(PartNumber) FROM NameParts)))
                    OR LOWER(p.FirstName) LIKE '%' + LOWER((SELECT Part FROM NameParts WHERE PartNumber = 1)) + '%'
                    OR LOWER(p.LastName) LIKE '%' + LOWER((SELECT Part FROM NameParts WHERE PartNumber = (SELECT MAX(PartNumber) FROM NameParts))) + '%'
                )
                ORDER BY MatchScore DESC
            """
            
            cursor.execute(query, (patient_name, patient_name, patient_name))
            
            # Convert to list of dictionaries
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    @retry_db_operation(max_retries=3, delay=2)
    def search_employee_by_name(self, employee_name: str) -> List[Dict]:
        """Search for employees (providers) by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                WITH NameParts AS ( 
                    SELECT value AS Part, ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS PartNumber 
                    FROM STRING_SPLIT(?, ' ')
                    WHERE LEN(TRIM(value)) > 0
                ) 
                SELECT TOP 10
                    e.EmployeeId,
                    e.FirstName,
                    e.MiddleName,
                    e.LastName,
                    e.Email,
                    e.Title as RoleName,
                    s.Name as SiteName,
                    -- Exact match score
                    CASE 
                        WHEN LOWER(TRIM(CONCAT(ISNULL(e.FirstName, ''), ' ', ISNULL(e.MiddleName, ''), ' ', ISNULL(e.LastName, '')))) = LOWER(TRIM(?)) THEN 100
                        WHEN LOWER(TRIM(CONCAT(ISNULL(e.FirstName, ''), ' ', ISNULL(e.LastName, '')))) = LOWER(TRIM(?)) THEN 95
                        ELSE 0 
                    END +
                    -- First name similarity
                    CASE 
                        WHEN LOWER(e.FirstName) = LOWER((SELECT Part FROM NameParts WHERE PartNumber = 1)) THEN 40
                        WHEN SOUNDEX(e.FirstName) = SOUNDEX((SELECT Part FROM NameParts WHERE PartNumber = 1)) THEN 30
                        WHEN LOWER(e.FirstName) LIKE LOWER((SELECT Part + '%' FROM NameParts WHERE PartNumber = 1)) THEN 25
                        ELSE 0 
                    END +
                    -- Last name similarity
                    CASE 
                        WHEN LOWER(e.LastName) = LOWER((SELECT Part FROM NameParts WHERE PartNumber = (SELECT MAX(PartNumber) FROM NameParts))) THEN 40
                        WHEN SOUNDEX(e.LastName) = SOUNDEX((SELECT Part FROM NameParts WHERE PartNumber = (SELECT MAX(PartNumber) FROM NameParts))) THEN 30
                        WHEN LOWER(e.LastName) LIKE LOWER((SELECT Part + '%' FROM NameParts WHERE PartNumber = (SELECT MAX(PartNumber) FROM NameParts))) THEN 25
                        ELSE 0 
                    END AS MatchScore
                FROM Employee e
                LEFT JOIN Site s ON e.SiteId = s.SiteId
                WHERE e.IsActive = 1
                AND (
                    SOUNDEX(e.FirstName) = SOUNDEX((SELECT Part FROM NameParts WHERE PartNumber = 1))
                    OR SOUNDEX(e.LastName) = SOUNDEX((SELECT Part FROM NameParts WHERE PartNumber = (SELECT MAX(PartNumber) FROM NameParts)))
                    OR LOWER(e.FirstName) LIKE '%' + LOWER((SELECT Part FROM NameParts WHERE PartNumber = 1)) + '%'
                    OR LOWER(e.LastName) LIKE '%' + LOWER((SELECT Part FROM NameParts WHERE PartNumber = (SELECT MAX(PartNumber) FROM NameParts))) + '%'
                )
                ORDER BY MatchScore DESC
            """
            
            cursor.execute(query, (employee_name, employee_name, employee_name))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def get_patient_authorizations(self, patient_id: int) -> List[Dict]:
        """Get all active authorizations for a patient"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT TOP 20
                    a.AuthId,
                    a.PatientId,
                    a.AuthNumber,
                    a.AuthDate,
                    a.AuthEndDate,
                    a.StatusId,
                    st.Name as StatusName,
                    p.Name as PayorName,
                    a.Notes
                FROM Auth a
                LEFT JOIN Status st ON a.StatusId = st.StatusId
                LEFT JOIN Payor p ON a.PayorId = p.PayorId
                WHERE a.PatientId = ?
                AND a.IsActive = 1
                AND (a.AuthEndDate IS NULL OR a.AuthEndDate >= GETDATE())
                ORDER BY a.AuthDate DESC
            """
            
            cursor.execute(query, (patient_id,))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def get_auth_details(self, auth_id: int) -> List[Dict]:
        """Get authorization details including service types and coverage"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    ad.AuthDetailId,
                    ad.AuthId,
                    ad.ServiceTypeId,
                    st.Name as ServiceTypeName,
                    ad.AuthorizedUnits,
                    ad.UsedUnits,
                    ad.RemainingUnits,
                    ad.UnitType,
                    ad.TreatmentTypeId,
                    tt.Name as TreatmentTypeName
                FROM AuthDetail ad
                LEFT JOIN ServiceType st ON ad.ServiceTypeId = st.ServiceTypeId
                LEFT JOIN TreatmentType tt ON ad.TreatmentTypeId = tt.TreatmentTypeId
                WHERE ad.AuthId = ?
                AND ad.IsActive = 1
                ORDER BY st.Name
            """
            
            cursor.execute(query, (auth_id,))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def get_patient_locations(self, patient_id: int) -> List[Dict]:
        """Get available locations for a patient based on their authorizations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT
                    l.LocationId,
                    l.Name as LocationName,
                    l.Address,
                    l.City,
                    l.State,
                    l.ZipCode,
                    s.Name as SiteName
                FROM Location l
                LEFT JOIN Site s ON l.SiteId = s.SiteId
                WHERE l.IsActive = 1
                AND EXISTS (
                    SELECT 1 FROM Auth a 
                    WHERE a.PatientId = ? 
                    AND a.IsActive = 1
                    AND (a.AuthEndDate IS NULL OR a.AuthEndDate >= GETDATE())
                )
                ORDER BY l.Name
            """
            
            cursor.execute(query, (patient_id,))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def check_employee_eligibility(self, employee_id: int, service_type_id: int, 
                                 location_id: int, treatment_type_id: int) -> Dict:
        """Check if employee is eligible to provide service at location"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    e.EmployeeId,
                    e.FirstName,
                    e.LastName,
                    CASE 
                        WHEN esl.EmployeeId IS NOT NULL THEN 1 
                        ELSE 0 
                    END as LocationEligible,
                    CASE 
                        WHEN est.EmployeeId IS NOT NULL THEN 1 
                        ELSE 0 
                    END as ServiceEligible,
                    CASE 
                        WHEN ett.EmployeeId IS NOT NULL THEN 1 
                        ELSE 0 
                    END as TreatmentEligible
                FROM Employee e
                LEFT JOIN EmployeeServiceLocation esl ON e.EmployeeId = esl.EmployeeId 
                    AND esl.LocationId = ? AND esl.IsActive = 1
                LEFT JOIN EmployeeServiceType est ON e.EmployeeId = est.EmployeeId 
                    AND est.ServiceTypeId = ? AND est.IsActive = 1
                LEFT JOIN EmployeeTreatmentType ett ON e.EmployeeId = ett.EmployeeId 
                    AND ett.TreatmentTypeId = ? AND ett.IsActive = 1
                WHERE e.EmployeeId = ?
                AND e.IsActive = 1
            """
            
            cursor.execute(query, (location_id, service_type_id, treatment_type_id, employee_id))
            
            row = cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                result = dict(zip(columns, row))
                result['IsEligible'] = (result['LocationEligible'] and 
                                      result['ServiceEligible'] and 
                                      result['TreatmentEligible'])
                return result
            
            return {'IsEligible': False, 'Error': 'Employee not found'}
    
    def suggest_employees(self, service_type_id: int, treatment_type_id: int, 
                         location_id: int, patient_id: int, start_datetime: str) -> List[Dict]:
        """Get employee suggestions based on eligibility and availability"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT TOP 10
                    e.EmployeeId,
                    e.FirstName,
                    e.LastName,
                    e.Email,
                    e.Title as RoleName,
                    s.Name as SiteName,
                    -- Calculate availability score
                    CASE 
                        WHEN NOT EXISTS (
                            SELECT 1 FROM Appointment a2 
                            WHERE a2.EmployeeId = e.EmployeeId 
                            AND a2.ScheduledDate = CAST(? AS DATE)
                            AND a2.StatusId IN (1, 2) -- Active/Scheduled statuses
                        ) THEN 10
                        ELSE 5
                    END as AvailabilityScore,
                    -- Count total appointments for workload assessment
                    (SELECT COUNT(*) FROM Appointment a3 
                     WHERE a3.EmployeeId = e.EmployeeId 
                     AND a3.ScheduledDate >= DATEADD(day, -30, GETDATE())
                     AND a3.StatusId IN (1, 2, 3)) as RecentAppointments
                FROM Employee e
                INNER JOIN EmployeeServiceLocation esl ON e.EmployeeId = esl.EmployeeId 
                    AND esl.LocationId = ? AND esl.IsActive = 1
                INNER JOIN EmployeeServiceType est ON e.EmployeeId = est.EmployeeId 
                    AND est.ServiceTypeId = ? AND est.IsActive = 1
                INNER JOIN EmployeeTreatmentType ett ON e.EmployeeId = ett.EmployeeId 
                    AND ett.TreatmentTypeId = ? AND ett.IsActive = 1
                LEFT JOIN Site s ON e.SiteId = s.SiteId
                WHERE e.IsActive = 1
                ORDER BY AvailabilityScore DESC, RecentAppointments ASC
            """
            
            cursor.execute(query, (start_datetime, location_id, service_type_id, treatment_type_id))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def check_appointment_conflicts(self, employee_id: int, start_datetime: str, 
                                  duration_minutes: int = 60) -> List[Dict]:
        """Check for appointment conflicts for an employee"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    a.AppointmentId,
                    a.ScheduledDate,
                    a.ScheduledMinutes,
                    p.FirstName + ' ' + p.LastName as PatientName,
                    st.Name as ServiceTypeName
                FROM Appointment a
                LEFT JOIN Patient p ON a.PatientId = p.PatientId
                LEFT JOIN AuthDetail ad ON a.AuthDetailId = ad.AuthDetailId
                LEFT JOIN ServiceType st ON ad.ServiceTypeId = st.ServiceTypeId
                WHERE a.EmployeeId = ?
                AND a.ScheduledDate = CAST(? AS DATE)
                AND a.StatusId IN (1, 2) -- Active/Scheduled
                AND (
                    -- Check for time overlap
                    (CAST(? AS TIME) BETWEEN 
                     CAST(DATEADD(minute, 0, CAST(? AS datetime)) AS TIME) AND 
                     CAST(DATEADD(minute, ISNULL(a.ScheduledMinutes, 60), CAST(? AS datetime)) AS TIME))
                    OR
                    (DATEADD(minute, ?, CAST(? AS datetime)) BETWEEN 
                     CAST(? AS datetime) AND 
                     DATEADD(minute, ISNULL(a.ScheduledMinutes, 60), CAST(? AS datetime)))
                )
                ORDER BY a.ScheduledDate
            """
            
            cursor.execute(query, (
                employee_id, start_datetime, start_datetime, start_datetime, start_datetime,
                duration_minutes, start_datetime, start_datetime, start_datetime
            ))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def book_appointment(self, booking_data: Dict) -> Dict:
        """Book a new appointment"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Insert appointment
                query = """
                    INSERT INTO Appointment (
                        PatientId, EmployeeId, AuthId, AuthDetailId, 
                        ServiceTypeId, LocationId, ScheduledDate, ScheduledMinutes,
                        StatusId, Notes, CreatedDate, IsActive
                    ) 
                    OUTPUT INSERTED.AppointmentId
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, GETDATE(), 1)
                """
                
                cursor.execute(query, (
                    booking_data['patient_id'],
                    booking_data['employee_id'],
                    booking_data['auth_id'],
                    booking_data['auth_detail_id'],
                    booking_data['service_type_id'],
                    booking_data['location_id'],
                    booking_data['scheduled_date'],
                    booking_data.get('scheduled_minutes', 60),
                    booking_data.get('notes', '')
                ))
                
                appointment_id = cursor.fetchone()[0]
                conn.commit()
                
                return {
                    'success': True,
                    'appointment_id': appointment_id,
                    'message': f'Appointment successfully booked with ID: {appointment_id}'
                }
                
            except Exception as e:
                conn.rollback()
                return {
                    'success': False,
                    'error': str(e),
                    'message': 'Failed to book appointment'
                }
    
    def create_chat_session(self) -> int:
        """Create a new chat session record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Assuming there's a ChatSession table
            query = """
                INSERT INTO ChatSession (StartTime, IsActive, CreatedDate) 
                OUTPUT INSERTED.SessionId
                VALUES (GETDATE(), 1, GETDATE())
            """
            
            try:
                cursor.execute(query)
                session_id = cursor.fetchone()[0]
                conn.commit()
                return session_id
            except:
                # If ChatSession table doesn't exist, return a dummy ID
                return 1
    
    def save_chat_message(self, session_id: int, sender: str, message: str, 
                         intent: str = None, entities: str = None) -> bool:
        """Save chat message to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Assuming there's a ChatMessage table
            query = """
                INSERT INTO ChatMessage (
                    SessionId, Sender, Message, Intent, Entities, Timestamp, CreatedDate
                ) 
                VALUES (?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """
            
            try:
                cursor.execute(query, (session_id, sender, message, intent, entities))
                conn.commit()
                return True
            except:
                # If table doesn't exist, just return True
                return True
    
    def execute_query(self, query: str) -> List[Dict]:
        """Execute a raw SQL query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
