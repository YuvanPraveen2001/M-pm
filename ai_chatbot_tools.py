"""
AI Chatbot Tools Registry and Management System
This module implements the tool collection and registration system
as outlined in the healthcare booking application roadmap.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
import re
from datetime import datetime, date, timedelta
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Defines the types of tools available in the system"""
    DATABASE_QUERY = "database_query"
    ENDPOINT = "endpoint"
    VALIDATION = "validation"
    BOOKING = "booking"
    AVAILABILITY = "availability"
    SEARCH = "search"


class ParameterType(Enum):
    """Defines parameter types for validation"""
    STRING = "string"
    INTEGER = "integer" 
    DATE = "date"
    TIME = "time"
    BOOLEAN = "boolean"
    EMAIL = "email"
    PHONE = "phone"
    ENUM = "enum"


@dataclass
class ParameterDefinition:
    """Defines a parameter for a tool"""
    name: str
    parameter_type: ParameterType
    required: bool = True
    description: str = ""
    allowed_values: Optional[List[str]] = None
    validation_pattern: Optional[str] = None
    default_value: Optional[Any] = None


@dataclass
class ToolDefinition:
    """Defines a tool in the system"""
    name: str
    tool_type: ToolType
    description: str
    purpose: str
    parameters: List[ParameterDefinition]
    usage_rules: List[str]
    dependencies: List[str] = None
    sql_template: Optional[str] = None
    endpoint_url: Optional[str] = None
    business_rules: List[str] = None


class HealthcareToolsRegistry:
    """
    Central registry for all healthcare booking tools
    Implements Step 1: Tool Collection & Registration
    """
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.register_healthcare_tools()
    
    def register_tool(self, tool: ToolDefinition):
        """Register a new tool in the system"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} ({tool.tool_type.value})")
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[ToolDefinition]:
        """Get all tools of a specific type"""
        return [tool for tool in self.tools.values() if tool.tool_type == tool_type]
    
    def register_healthcare_tools(self):
        """Register all healthcare-specific tools"""
        
        # 1. APPOINTMENT BOOKING TOOLS
        self.register_tool(ToolDefinition(
            name="book_appointment",
            tool_type=ToolType.BOOKING,
            description="Books an appointment with a therapist",
            purpose="Allow patients to book appointments with available therapists",
            parameters=[
                ParameterDefinition("patient_id", ParameterType.INTEGER, True, "Patient ID"),
                ParameterDefinition("employee_id", ParameterType.INTEGER, True, "Therapist/Employee ID"),
                ParameterDefinition("appointment_date", ParameterType.DATE, True, "Appointment date"),
                ParameterDefinition("appointment_time", ParameterType.TIME, True, "Appointment time"),
                ParameterDefinition("duration_minutes", ParameterType.INTEGER, False, "Duration in minutes", default_value=60),
                ParameterDefinition("service_type_id", ParameterType.INTEGER, True, "Service type ID"),
                ParameterDefinition("location_id", ParameterType.INTEGER, True, "Location ID"),
                ParameterDefinition("notes", ParameterType.STRING, False, "Additional notes")
            ],
            usage_rules=[
                "Patient must exist in system",
                "Therapist must be available at requested time",
                "Appointment time must be in the future",
                "Duration must be between 30-120 minutes"
            ],
            dependencies=["check_availability", "validate_patient", "validate_therapist"],
            business_rules=[
                "No double booking allowed",
                "Minimum 24 hours advance booking required",
                "Maximum 3 months in advance booking allowed"
            ]
        ))
        
        # 2. AVAILABILITY CHECKING TOOLS
        self.register_tool(ToolDefinition(
            name="check_availability",
            tool_type=ToolType.AVAILABILITY,
            description="Checks therapist availability for specific dates/times",
            purpose="Verify if a therapist is available for appointment booking",
            parameters=[
                ParameterDefinition("employee_id", ParameterType.INTEGER, False, "Specific therapist ID"),
                ParameterDefinition("start_date", ParameterType.DATE, True, "Start date to check"),
                ParameterDefinition("end_date", ParameterType.DATE, False, "End date to check"),
                ParameterDefinition("time_from", ParameterType.TIME, False, "Start time preference"),
                ParameterDefinition("time_to", ParameterType.TIME, False, "End time preference"),
                ParameterDefinition("duration_minutes", ParameterType.INTEGER, False, "Required duration", default_value=60)
            ],
            sql_template="""
            SELECT e.EmployeeId, e.FirstName, e.LastName, 
                   ead.AvailableFrom, ead.AvailableTo, ead.WeekDay
            FROM Employee e
            JOIN EmployeeAvailabilityDateTime ead ON e.EmployeeId = ead.EmployeeId
            WHERE ead.AvailabilityStatusId = 2 
            AND (e.EmployeeId = ? OR ? IS NULL)
            AND ead.WeekDay = DATEPART(WEEKDAY, ?)
            AND NOT EXISTS (
                SELECT 1 FROM Appointment a 
                WHERE a.EmployeeId = e.EmployeeId 
                AND CAST(a.ScheduledDate AS DATE) = ?
                AND a.AppointmentStatusId IN (1, 2)
            )
            """,
            usage_rules=[
                "If no employee_id provided, check all available therapists",
                "Consider employee availability windows",
                "Exclude already booked time slots"
            ]
        ))
        
        # 3. EMPLOYEE SEARCH TOOLS
        self.register_tool(ToolDefinition(
            name="find_employees_by_criteria",
            tool_type=ToolType.SEARCH,
            description="Finds employees/therapists based on various criteria",
            purpose="Search for therapists using filters like zone, gender, degree, zip code, language",
            parameters=[
                ParameterDefinition("zone_id", ParameterType.INTEGER, False, "Zone/area ID"),
                ParameterDefinition("gender", ParameterType.ENUM, False, "Gender preference", 
                                  allowed_values=["Male", "Female", "Non-binary"]),
                ParameterDefinition("min_degree_level", ParameterType.STRING, False, "Minimum degree level"),
                ParameterDefinition("zip_code", ParameterType.STRING, False, "Zip code area"),
                ParameterDefinition("language_id", ParameterType.INTEGER, False, "Preferred language ID"),
                ParameterDefinition("specialization", ParameterType.STRING, False, "Treatment specialization"),
                ParameterDefinition("treatment_type_id", ParameterType.INTEGER, False, "Treatment type ID"),
                ParameterDefinition("max_distance", ParameterType.INTEGER, False, "Maximum distance in miles")
            ],
            sql_template="""
            SELECT DISTINCT e.EmployeeId, e.FirstName, e.LastName, e.Gender,
                   e.HighestDegree, e.ServiceAreaZip, z.ZoneName,
                   tt.TreatmentTypeDesc, e.Email, e.PhoneCell
            FROM Employee e
            LEFT JOIN EmployeeZoneMapping ezm ON e.EmployeeId = ezm.EmployeeId
            LEFT JOIN Zone z ON ezm.ZoneId = z.ZoneId
            LEFT JOIN EmployeeTreatmentTypeMapping ettm ON e.EmployeeId = ettm.EmployeeId
            LEFT JOIN TreatmentType tt ON ettm.TreatmentTypeId = tt.TreatmentTypeid
            LEFT JOIN EmployeeLanguageMapping elm ON e.EmployeeId = elm.EmployeeId
            WHERE e.Active = 1
            AND (ezm.ZoneId = ? OR ? IS NULL)
            AND (e.Gender = (SELECT GenderID FROM Gender WHERE GenderType = ?) OR ? IS NULL)
            AND (e.ServiceAreaZip = ? OR ? IS NULL)
            AND (elm.LanguageID = ? OR ? IS NULL)
            AND (ettm.TreatmentTypeId = ? OR ? IS NULL)
            """,
            usage_rules=[
                "All criteria are optional (OR logic)",
                "Results should be sorted by proximity if location provided",
                "Only return active employees",
                "Limit results to 50 for performance"
            ]
        ))
        
        # 4. EMPLOYEE SUGGESTION TOOLS
        self.register_tool(ToolDefinition(
            name="suggest_suitable_therapists",
            tool_type=ToolType.SEARCH,
            description="Suggests therapists based on patient needs and business rules",
            purpose="Provide intelligent therapist recommendations based on multiple factors",
            parameters=[
                ParameterDefinition("patient_id", ParameterType.INTEGER, True, "Patient ID"),
                ParameterDefinition("treatment_type", ParameterType.STRING, False, "Preferred treatment type"),
                ParameterDefinition("preferred_gender", ParameterType.ENUM, False, "Preferred gender", 
                                  allowed_values=["Male", "Female", "No preference"]),
                ParameterDefinition("location_preference", ParameterType.STRING, False, "Location preference"),
                ParameterDefinition("language_preference", ParameterType.INTEGER, False, "Language preference ID"),
                ParameterDefinition("availability_date", ParameterType.DATE, False, "Preferred availability date")
            ],
            sql_template="""
            SELECT e.EmployeeId, e.FirstName, e.LastName, 
                   AVG(rating.score) as avg_rating,
                   COUNT(DISTINCT a.AppointmentId) as total_appointments,
                   tt.TreatmentTypeDesc,
                   CASE WHEN ezm.ZoneId = pzm.ZoneId THEN 'Same Zone' ELSE 'Different Zone' END as location_match
            FROM Employee e
            JOIN EmployeeTreatmentTypeMapping ettm ON e.EmployeeId = ettm.EmployeeId
            JOIN TreatmentType tt ON ettm.TreatmentTypeId = tt.TreatmentTypeid
            LEFT JOIN EmployeeZoneMapping ezm ON e.EmployeeId = ezm.EmployeeId
            LEFT JOIN PatientZoneMapping pzm ON pzm.PatientId = ?
            LEFT JOIN Appointment a ON e.EmployeeId = a.EmployeeId
            LEFT JOIN (SELECT EmployeeId, 4.5 as score FROM Employee) rating ON e.EmployeeId = rating.EmployeeId
            WHERE e.Active = 1
            AND (e.Gender = (SELECT GenderID FROM Gender WHERE GenderType = ?) OR ? IS NULL)
            GROUP BY e.EmployeeId, e.FirstName, e.LastName, tt.TreatmentTypeDesc, ezm.ZoneId, pzm.ZoneId
            ORDER BY avg_rating DESC, location_match ASC, total_appointments DESC
            """,
            usage_rules=[
                "Consider patient location and therapist zones",
                "Prioritize highly rated therapists",
                "Consider therapist availability",
                "Respect patient preferences"
            ],
            business_rules=[
                "Same zone therapists get priority",
                "Higher rated therapists appear first",
                "Consider therapist workload balance"
            ]
        ))
        
        # 5. VALIDATION TOOLS
        self.register_tool(ToolDefinition(
            name="validate_patient",
            tool_type=ToolType.VALIDATION,
            description="Validates patient information and eligibility",
            purpose="Ensure patient exists and is eligible for booking",
            parameters=[
                ParameterDefinition("patient_id", ParameterType.INTEGER, True, "Patient ID to validate")
            ],
            sql_template="""
            SELECT PatientId, FirstName, LastName, IsActive, Email
            FROM Patient 
            WHERE PatientId = ? AND IsActive = 1
            """,
            usage_rules=[
                "Patient must exist and be active",
                "Return patient details for confirmation"
            ]
        ))
        
        self.register_tool(ToolDefinition(
            name="validate_therapist",
            tool_type=ToolType.VALIDATION,
            description="Validates therapist information and availability",
            purpose="Ensure therapist exists and is available for booking",
            parameters=[
                ParameterDefinition("employee_id", ParameterType.INTEGER, True, "Employee/Therapist ID to validate")
            ],
            sql_template="""
            SELECT e.EmployeeId, e.FirstName, e.LastName, e.Active, e.Email,
                   COUNT(DISTINCT ettm.TreatmentTypeId) as specializations
            FROM Employee e
            LEFT JOIN EmployeeTreatmentTypeMapping ettm ON e.EmployeeId = ettm.EmployeeId
            WHERE e.EmployeeId = ? AND e.Active = 1
            GROUP BY e.EmployeeId, e.FirstName, e.LastName, e.Active, e.Email
            """,
            usage_rules=[
                "Therapist must exist and be active",
                "Include specialization count",
                "Return therapist details for confirmation"
            ]
        ))
        
        # 6. APPOINTMENT MANAGEMENT TOOLS
        self.register_tool(ToolDefinition(
            name="get_patient_appointments",
            tool_type=ToolType.DATABASE_QUERY,
            description="Retrieves patient's appointment history and upcoming appointments",
            purpose="Show patient their appointment information",
            parameters=[
                ParameterDefinition("patient_id", ParameterType.INTEGER, True, "Patient ID"),
                ParameterDefinition("include_past", ParameterType.BOOLEAN, False, "Include past appointments", default_value=False),
                ParameterDefinition("limit", ParameterType.INTEGER, False, "Maximum number of results", default_value=10)
            ],
            sql_template="""
            SELECT a.AppointmentId, a.ScheduledDate, a.ScheduledMinutes,
                   e.FirstName + ' ' + e.LastName as TherapistName,
                   st.ServiceTypeDesc, ast.AppointmentStatusDesc,
                   l.Name as LocationName, a.Notes
            FROM Appointment a
            JOIN Employee e ON a.EmployeeId = e.EmployeeId
            JOIN ServiceType st ON a.ServiceTypeId = st.ServiceTypeId
            JOIN AppointmentStatus ast ON a.AppointmentStatusId = ast.AppointmentStatusId
            JOIN Location l ON a.LocationId = l.LocationId
            WHERE a.PatientId = ?
            AND (? = 1 OR a.ScheduledDate >= GETDATE())
            ORDER BY a.ScheduledDate DESC
            OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """,
            usage_rules=[
                "Always require patient_id",
                "By default only show future appointments",
                "Limit results for performance"
            ]
        ))
        
        logger.info(f"Registered {len(self.tools)} healthcare tools")
    
    def list_available_tools(self) -> Dict[str, str]:
        """Return a summary of all available tools"""
        return {name: tool.description for name, tool in self.tools.items()}


class ParameterValidator:
    """
    Validates parameters according to their definitions
    Implements part of Step 3: Validation Layer
    """
    
    @staticmethod
    def validate_parameter(value: Any, param_def: ParameterDefinition) -> tuple[bool, str]:
        """Validate a single parameter"""
        if value is None or value == "":
            if param_def.required:
                return False, f"Parameter '{param_def.name}' is required"
            else:
                return True, ""
        
        # Type-specific validation
        if param_def.parameter_type == ParameterType.INTEGER:
            try:
                int(value)
            except (ValueError, TypeError):
                return False, f"Parameter '{param_def.name}' must be an integer"
        
        elif param_def.parameter_type == ParameterType.DATE:
            try:
                if isinstance(value, str):
                    datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return False, f"Parameter '{param_def.name}' must be a valid date (YYYY-MM-DD)"
        
        elif param_def.parameter_type == ParameterType.TIME:
            try:
                if isinstance(value, str):
                    datetime.strptime(value, '%H:%M')
            except ValueError:
                return False, f"Parameter '{param_def.name}' must be a valid time (HH:MM)"
        
        elif param_def.parameter_type == ParameterType.EMAIL:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(value)):
                return False, f"Parameter '{param_def.name}' must be a valid email"
        
        elif param_def.parameter_type == ParameterType.PHONE:
            if not re.match(r'^[\+]?[1-9][\d]{0,15}$', str(value).replace('-', '').replace(' ', '').replace('(', '').replace(')', '')):
                return False, f"Parameter '{param_def.name}' must be a valid phone number"
        
        elif param_def.parameter_type == ParameterType.ENUM:
            if param_def.allowed_values and str(value) not in param_def.allowed_values:
                return False, f"Parameter '{param_def.name}' must be one of: {', '.join(param_def.allowed_values)}"
        
        # Pattern validation
        if param_def.validation_pattern and not re.match(param_def.validation_pattern, str(value)):
            return False, f"Parameter '{param_def.name}' does not match required pattern"
        
        return True, ""
    
    @staticmethod
    def validate_parameters(parameters: Dict[str, Any], tool_def: ToolDefinition) -> tuple[bool, List[str]]:
        """Validate all parameters for a tool"""
        errors = []
        
        for param_def in tool_def.parameters:
            value = parameters.get(param_def.name)
            is_valid, error = ParameterValidator.validate_parameter(value, param_def)
            if not is_valid:
                errors.append(error)
        
        return len(errors) == 0, errors


# Example usage and testing
if __name__ == "__main__":
    # Initialize the registry
    registry = HealthcareToolsRegistry()
    
    # List all available tools
    print("Available Tools:")
    for name, description in registry.list_available_tools().items():
        print(f"- {name}: {description}")
    
    # Test parameter validation
    book_appointment_tool = registry.get_tool("book_appointment")
    if book_appointment_tool:
        test_params = {
            "patient_id": 123,
            "employee_id": 456,
            "appointment_date": "2025-09-15",
            "appointment_time": "14:30",
            "service_type_id": 1,
            "location_id": 1
        }
        
        validator = ParameterValidator()
        is_valid, errors = validator.validate_parameters(test_params, book_appointment_tool)
        print(f"\nValidation Result: {'PASS' if is_valid else 'FAIL'}")
        if errors:
            for error in errors:
                print(f"- {error}")
