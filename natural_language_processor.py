"""
Natural Language Query Processor for Healthcare Chatbot
Converts natural language to SQL queries and executes them
Enhanced with Ollama LLM for intelligent query processing
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from healthcare_database_manager_sqlserver import HealthcareDatabaseManager

# Import model configuration and LLM
from model_config import CHAT_MODEL, get_chat_model_config

try:
    from langchain_community.chat_models import ChatOllama
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LLM_AVAILABLE = True
except ImportError:
    print("Warning: LangChain not available for Natural Language Processor")
    ChatOllama = None
    LLM_AVAILABLE = False

class HealthcareQueryProcessor:
    """Processes natural language queries and converts them to SQL"""
    
    def __init__(self, db_manager: HealthcareDatabaseManager):
        self.db_manager = db_manager
        self.day_mappings = {
            'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4,
            'friday': 5, 'saturday': 6, 'sunday': 7,
            'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6, 'sun': 7
        }
        
        # Initialize LLM if available
        self.llm_available = False
        self.chat_model = None
        
        if LLM_AVAILABLE:
            try:
                self.chat_model = ChatOllama(model=CHAT_MODEL, temperature=0.1)
                self.llm_available = True
                print(f"✅ Natural Language Processor: Using LLM {CHAT_MODEL}")
            except Exception as e:
                print(f"⚠️ Natural Language Processor: LLM not available: {e}")
        else:
            print("ℹ️ Natural Language Processor: Using rule-based processing")
    
    def classify_intent(self, user_query: str) -> Dict:
        """Classify the intent of a user query using LLM or rule-based approach"""
        
        if self.llm_available and self.chat_model:
            try:
                return self._classify_intent_with_llm(user_query)
            except Exception as e:
                print(f"⚠️ LLM intent classification failed: {e}")
        
        # Fallback to rule-based classification
        return self._classify_intent_rule_based(user_query)
    
    def _classify_intent_with_llm(self, user_query: str) -> Dict:
        """Classify intent using LLM"""
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an intent classifier for a healthcare appointment booking system. 
            
Classify the user's query into one of these intents:
- availability: Checking when someone is available, free time, schedule
- appointment: Booking, scheduling, or managing appointments  
- data_retrieval: General data queries, searching for information
- general: Other queries

Return a JSON object with:
- intent: one of the above categories
- confidence: float between 0.0 and 1.0
- reasoning: brief explanation

Examples:
- "Check John's availability this Wednesday" -> {"intent": "availability", "confidence": 0.9, "reasoning": "asking about availability on specific day"}
- "Book an appointment with Dr. Smith" -> {"intent": "appointment", "confidence": 0.95, "reasoning": "explicit appointment booking request"}
- "Show me all therapists" -> {"intent": "data_retrieval", "confidence": 0.8, "reasoning": "requesting data about providers"}

User query: {query}"""),
            ("human", "{query}")
        ])
        
        chain = prompt_template | self.chat_model | StrOutputParser()
        
        result = chain.invoke({"query": user_query})
        
        try:
            # Try to parse JSON response
            import json
            result_data = json.loads(result)
            return result_data
        except:
            # If JSON parsing fails, fallback to rule-based
            return self._classify_intent_rule_based(user_query)
    
    def _classify_intent_rule_based(self, user_query: str) -> Dict:
        """Rule-based intent classification (fallback)"""
        query_lower = user_query.lower()
        
        # Availability patterns
        if any(pattern in query_lower for pattern in ['available', 'availability', 'free', 'schedule', 'when']):
            return {"intent": "availability", "confidence": 0.7, "reasoning": "contains availability keywords"}
        
        # Appointment patterns  
        if any(pattern in query_lower for pattern in ['book', 'schedule', 'appointment', 'reserve']):
            return {"intent": "appointment", "confidence": 0.7, "reasoning": "contains appointment keywords"}
        
        # Data retrieval patterns
        if any(pattern in query_lower for pattern in ['show', 'list', 'find', 'search', 'get']):
            return {"intent": "data_retrieval", "confidence": 0.6, "reasoning": "contains data retrieval keywords"}
        
        return {"intent": "general", "confidence": 0.5, "reasoning": "no specific pattern matched"}

    def process_query(self, user_query: str) -> Dict:
        """Process natural language query and return results"""
        try:
            # Analyze the query to determine intent and extract entities
            query_analysis = self._analyze_query(user_query)
            
            if not query_analysis['intent']:
                return {
                    'success': False,
                    'message': "I couldn't understand your request. Please try rephrasing.",
                    'suggestions': [
                        "Check availability of John this Wednesday",
                        "Find appointments for Sarah next Monday",
                        "Show me John's schedule today",
                        "What appointments does Dr. Smith have tomorrow?"
                    ]
                }
            
            # Generate SQL query based on intent
            sql_query = self._generate_sql_query(query_analysis)
            
            if not sql_query:
                return {
                    'success': False,
                    'message': "I couldn't generate a query for your request.",
                    'analysis': query_analysis
                }
            
            # Execute the query
            results = self.db_manager.execute_query(sql_query)
            
            # Format the response
            response = self._format_response(query_analysis, results, sql_query)
            
            return {
                'success': True,
                'message': response['message'],
                'results': results,
                'sql_query': sql_query,
                'analysis': query_analysis,
                'formatted_results': response['formatted_results']
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"An error occurred while processing your query: {str(e)}",
                'error': str(e)
            }
    
    def _analyze_query(self, query: str) -> Dict:
        """Analyze natural language query to extract intent and entities"""
        query_lower = query.lower().strip()
        
        analysis = {
            'intent': None,
            'person_name': None,
            'date': None,
            'query_type': None,
            'original_query': query
        }
        
        # Intent detection patterns
        availability_patterns = [
            r'check.*availability',
            r'available.*when',
            r'free.*time',
            r'schedule.*available',
            r'what.*available'
        ]
        
        appointment_patterns = [
            r'appointments.*for',
            r'schedule.*for',
            r'meetings.*with',
            r'bookings.*for',
            r'find.*appointments'
        ]
        
        schedule_patterns = [
            r'show.*schedule',
            r'what.*schedule',
            r'schedule.*today',
            r'calendar.*for'
        ]
        
        # Check for availability queries
        if any(re.search(pattern, query_lower) for pattern in availability_patterns):
            analysis['intent'] = 'check_availability'
            analysis['query_type'] = 'availability'
        
        # Check for appointment queries
        elif any(re.search(pattern, query_lower) for pattern in appointment_patterns):
            analysis['intent'] = 'find_appointments'
            analysis['query_type'] = 'appointments'
        
        # Check for schedule queries
        elif any(re.search(pattern, query_lower) for pattern in schedule_patterns):
            analysis['intent'] = 'show_schedule'
            analysis['query_type'] = 'schedule'
        
        # Extract person name
        analysis['person_name'] = self._extract_person_name(query_lower)
        
        # Extract date
        analysis['date'] = self._extract_date(query_lower)
        
        return analysis
    
    def _extract_person_name(self, query: str) -> Optional[str]:
        """Extract person name from query"""
        # Common patterns for names in queries
        name_patterns = [
            r'(?:of|for)\s+([a-zA-Z]+)(?:\s+this|\s+next|\s+today|\s+tomorrow|$)',  # "of John this"
            r'(?:dr\.?|doctor)\s+([a-zA-Z]+)',  # "Dr. Smith" or "Doctor Smith"
            r'([a-zA-Z]+)\'s\s+',  # "John's schedule"
            r'\b([A-Z][a-z]+)\b(?=\s+(?:this|next|today|tomorrow))',  # "John this Wednesday"
            r'(?:availability|schedule|appointments).*?(?:of|for)\s+([a-zA-Z]+)',  # "availability of John"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common words that aren't names
                if name.lower() not in ['check', 'show', 'find', 'what', 'when', 'this', 'next', 'today', 'tomorrow', 'availability', 'schedule', 'appointments', 'me', 'the', 'my']:
                    return name.title()
        
        return None
    
    def _extract_date(self, query: str) -> Optional[datetime]:
        """Extract date from query"""
        today = datetime.now().date()
        
        # Handle relative dates
        if 'today' in query:
            return datetime.combine(today, datetime.min.time())
        elif 'tomorrow' in query:
            return datetime.combine(today + timedelta(days=1), datetime.min.time())
        elif 'yesterday' in query:
            return datetime.combine(today - timedelta(days=1), datetime.min.time())
        
        # Handle "this" + day of week
        this_match = re.search(r'this\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)', query)
        if this_match:
            day_name = this_match.group(1).lower()
            target_day = self.day_mappings[day_name]
            current_day = today.weekday()
            
            # Calculate days until target day this week
            days_ahead = target_day - current_day
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            target_date = today + timedelta(days=days_ahead)
            return datetime.combine(target_date, datetime.min.time())
        
        # Handle "next" + day of week
        next_match = re.search(r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)', query)
        if next_match:
            day_name = next_match.group(1).lower()
            target_day = self.day_mappings[day_name]
            current_day = today.weekday()
            
            # Calculate days until target day next week
            days_ahead = target_day - current_day + 7
            target_date = today + timedelta(days=days_ahead)
            return datetime.combine(target_date, datetime.min.time())
        
        # Handle specific date formats (you can extend this)
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',  # MM/DD/YYYY or MM/DD/YY
            r'(\d{1,2})-(\d{1,2})-(\d{2,4})',  # MM-DD-YYYY or MM-DD-YY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, query)
            if match:
                try:
                    month, day, year = match.groups()
                    if len(year) == 2:
                        year = '20' + year
                    return datetime(int(year), int(month), int(day))
                except ValueError:
                    continue
        
        return None
    
    def _generate_sql_query(self, analysis: Dict) -> Optional[str]:
        """Generate SQL query based on analysis"""
        intent = analysis['intent']
        person_name = analysis['person_name']
        date = analysis['date']
        
        if not person_name:
            return None
        
        # Base query components
        if intent == 'check_availability':
            return self._generate_availability_query(person_name, date)
        elif intent == 'find_appointments':
            return self._generate_appointments_query(person_name, date)
        elif intent == 'show_schedule':
            return self._generate_schedule_query(person_name, date)
        
        return None
    
    def _generate_availability_query(self, person_name: str, date: Optional[datetime]) -> str:
        """Generate SQL query to check availability"""
        date_condition = ""
        if date:
            date_str = date.strftime('%Y-%m-%d')
            date_condition = f"AND CAST(a.ScheduledDate AS DATE) = '{date_str}'"
        
        query = f"""
            WITH EmployeeSearch AS (
                SELECT e.EmployeeId, e.FirstName, e.LastName, e.Email,
                       r.Name as RoleName, s.Name as SiteName
                FROM Employee e
                LEFT JOIN Role r ON e.RoleId = r.RoleId
                LEFT JOIN Site s ON e.SiteId = s.SiteId
                WHERE e.IsActive = 1
                AND (
                    LOWER(e.FirstName) LIKE '%{person_name.lower()}%'
                    OR LOWER(e.LastName) LIKE '%{person_name.lower()}%'
                    OR SOUNDEX(e.FirstName) = SOUNDEX('{person_name}')
                    OR SOUNDEX(e.LastName) = SOUNDEX('{person_name}')
                )
            ),
            ExistingAppointments AS (
                SELECT es.EmployeeId, es.FirstName, es.LastName, es.RoleName, es.SiteName,
                       a.AppointmentId, a.ScheduledDate, a.ScheduledMinutes,
                       p.FirstName + ' ' + p.LastName as PatientName,
                       st.Name as ServiceTypeName
                FROM EmployeeSearch es
                LEFT JOIN Appointment a ON es.EmployeeId = a.EmployeeId
                    AND a.StatusId IN (1, 2) -- Active/Scheduled
                    {date_condition}
                LEFT JOIN Patient p ON a.PatientId = p.PatientId
                LEFT JOIN AuthDetail ad ON a.AuthDetailId = ad.AuthDetailId
                LEFT JOIN ServiceType st ON ad.ServiceTypeId = st.ServiceTypeId
            )
            SELECT 
                EmployeeId,
                FirstName + ' ' + LastName as EmployeeName,
                RoleName,
                SiteName,
                CASE 
                    WHEN AppointmentId IS NULL THEN 'Available'
                    ELSE 'Busy - ' + PatientName + ' (' + ServiceTypeName + ')'
                END as AvailabilityStatus,
                ScheduledDate,
                ScheduledMinutes
            FROM ExistingAppointments
            ORDER BY EmployeeId, ScheduledDate
        """
        
        return query
    
    def _generate_appointments_query(self, person_name: str, date: Optional[datetime]) -> str:
        """Generate SQL query to find appointments"""
        date_condition = ""
        if date:
            date_str = date.strftime('%Y-%m-%d')
            date_condition = f"AND CAST(a.ScheduledDate AS DATE) = '{date_str}'"
        
        query = f"""
            SELECT 
                a.AppointmentId,
                a.ScheduledDate,
                a.ScheduledMinutes,
                p.FirstName + ' ' + p.LastName as PatientName,
                e.FirstName + ' ' + e.LastName as ProviderName,
                st.Name as ServiceTypeName,
                l.Name as LocationName,
                stat.Name as AppointmentStatus
            FROM Appointment a
            INNER JOIN Patient p ON a.PatientId = p.PatientId
            INNER JOIN Employee e ON a.EmployeeId = e.EmployeeId
            LEFT JOIN AuthDetail ad ON a.AuthDetailId = ad.AuthDetailId
            LEFT JOIN ServiceType st ON ad.ServiceTypeId = st.ServiceTypeId
            LEFT JOIN Location l ON a.LocationId = l.LocationId
            LEFT JOIN Status stat ON a.StatusId = stat.StatusId
            WHERE a.IsActive = 1
            AND (
                LOWER(e.FirstName) LIKE '%{person_name.lower()}%'
                OR LOWER(e.LastName) LIKE '%{person_name.lower()}%'
                OR LOWER(p.FirstName) LIKE '%{person_name.lower()}%'
                OR LOWER(p.LastName) LIKE '%{person_name.lower()}%'
                OR SOUNDEX(e.FirstName) = SOUNDEX('{person_name}')
                OR SOUNDEX(e.LastName) = SOUNDEX('{person_name}')
                OR SOUNDEX(p.FirstName) = SOUNDEX('{person_name}')
                OR SOUNDEX(p.LastName) = SOUNDEX('{person_name}')
            )
            {date_condition}
            ORDER BY a.ScheduledDate DESC
        """
        
        return query
    
    def _generate_schedule_query(self, person_name: str, date: Optional[datetime]) -> str:
        """Generate SQL query to show schedule"""
        date_condition = ""
        if date:
            date_str = date.strftime('%Y-%m-%d')
            date_condition = f"AND CAST(a.ScheduledDate AS DATE) = '{date_str}'"
        else:
            # Default to next 7 days if no date specified
            today = datetime.now().strftime('%Y-%m-%d')
            next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            date_condition = f"AND CAST(a.ScheduledDate AS DATE) BETWEEN '{today}' AND '{next_week}'"
        
        query = f"""
            WITH EmployeeMatch AS (
                SELECT EmployeeId, FirstName, LastName, Email, 
                       FirstName + ' ' + LastName as FullName
                FROM Employee
                WHERE IsActive = 1
                AND (
                    LOWER(FirstName) LIKE '%{person_name.lower()}%'
                    OR LOWER(LastName) LIKE '%{person_name.lower()}%'
                    OR SOUNDEX(FirstName) = SOUNDEX('{person_name}')
                    OR SOUNDEX(LastName) = SOUNDEX('{person_name}')
                )
            )
            SELECT 
                em.FullName as ProviderName,
                a.ScheduledDate,
                FORMAT(a.ScheduledDate, 'hh:mm tt') as ScheduledTime,
                a.ScheduledMinutes,
                p.FirstName + ' ' + p.LastName as PatientName,
                st.Name as ServiceTypeName,
                l.Name as LocationName,
                stat.Name as Status
            FROM EmployeeMatch em
            LEFT JOIN Appointment a ON em.EmployeeId = a.EmployeeId
                AND a.StatusId IN (1, 2, 3) -- Active, Scheduled, Completed
                {date_condition}
            LEFT JOIN Patient p ON a.PatientId = p.PatientId
            LEFT JOIN AuthDetail ad ON a.AuthDetailId = ad.AuthDetailId
            LEFT JOIN ServiceType st ON ad.ServiceTypeId = st.ServiceTypeId
            LEFT JOIN Location l ON a.LocationId = l.LocationId
            LEFT JOIN Status stat ON a.StatusId = stat.StatusId
            ORDER BY em.FullName, a.ScheduledDate
        """
        
        return query
    
    def _format_response(self, analysis: Dict, results: List[Dict], sql_query: str) -> Dict:
        """Format the response based on query type and results"""
        intent = analysis['intent']
        person_name = analysis['person_name']
        date = analysis['date']
        
        if not results:
            return {
                'message': f"No {intent.replace('_', ' ')} found for '{person_name}'" + 
                          (f" on {date.strftime('%A, %B %d, %Y')}" if date else ""),
                'formatted_results': []
            }
        
        if intent == 'check_availability':
            return self._format_availability_response(person_name, date, results)
        elif intent == 'find_appointments':
            return self._format_appointments_response(person_name, date, results)
        elif intent == 'show_schedule':
            return self._format_schedule_response(person_name, date, results)
        
        return {
            'message': f"Found {len(results)} results for your query.",
            'formatted_results': results
        }
    
    def _format_availability_response(self, person_name: str, date: Optional[datetime], results: List[Dict]) -> Dict:
        """Format availability check response"""
        available_slots = [r for r in results if 'Available' in r.get('AvailabilityStatus', '')]
        busy_slots = [r for r in results if 'Busy' in r.get('AvailabilityStatus', '')]
        
        date_str = date.strftime('%A, %B %d, %Y') if date else "the requested time"
        
        message_parts = []
        if available_slots:
            message_parts.append(f"✅ {person_name} is available on {date_str}")
            if len(available_slots) > 1:
                message_parts.append(f"Found {len(available_slots)} available providers matching '{person_name}'")
        
        if busy_slots:
            message_parts.append(f"⏰ Some time slots are busy:")
            for slot in busy_slots[:3]:  # Show first 3 busy slots
                time_info = slot.get('ScheduledDate', 'Unknown time')
                status = slot.get('AvailabilityStatus', 'Busy')
                message_parts.append(f"  • {time_info}: {status}")
        
        if not available_slots and not busy_slots:
            message_parts.append(f"No availability information found for '{person_name}' on {date_str}")
        
        return {
            'message': '\n'.join(message_parts),
            'formatted_results': results
        }
    
    def _format_appointments_response(self, person_name: str, date: Optional[datetime], results: List[Dict]) -> Dict:
        """Format appointments response"""
        date_str = date.strftime('%A, %B %d, %Y') if date else "the requested period"
        
        message_parts = [f"📅 Found {len(results)} appointment(s) for '{person_name}' on {date_str}:"]
        
        for i, appt in enumerate(results[:5], 1):  # Show first 5 appointments
            patient = appt.get('PatientName', 'Unknown Patient')
            provider = appt.get('ProviderName', 'Unknown Provider')
            service = appt.get('ServiceTypeName', 'Unknown Service')
            location = appt.get('LocationName', 'Unknown Location')
            scheduled = appt.get('ScheduledDate', 'Unknown Time')
            status = appt.get('AppointmentStatus', 'Unknown Status')
            
            message_parts.append(
                f"{i}. {scheduled} - {patient} with {provider}\n"
                f"   Service: {service} | Location: {location} | Status: {status}"
            )
        
        if len(results) > 5:
            message_parts.append(f"... and {len(results) - 5} more appointments")
        
        return {
            'message': '\n'.join(message_parts),
            'formatted_results': results
        }
    
    def _format_schedule_response(self, person_name: str, date: Optional[datetime], results: List[Dict]) -> Dict:
        """Format schedule response"""
        date_str = date.strftime('%A, %B %d, %Y') if date else "the next 7 days"
        
        # Group by provider
        by_provider = {}
        for result in results:
            provider = result.get('ProviderName', 'Unknown Provider')
            if provider not in by_provider:
                by_provider[provider] = []
            if result.get('ScheduledDate'):  # Only add if there's an actual appointment
                by_provider[provider].append(result)
        
        message_parts = [f"📋 Schedule for '{person_name}' on {date_str}:"]
        
        for provider, appointments in by_provider.items():
            if appointments:
                message_parts.append(f"\n👨‍⚕️ {provider}:")
                for appt in appointments:
                    time_info = appt.get('ScheduledTime', 'Unknown time')
                    patient = appt.get('PatientName', 'Unknown Patient')
                    service = appt.get('ServiceTypeName', 'Unknown Service')
                    location = appt.get('LocationName', 'Unknown Location')
                    
                    message_parts.append(f"  • {time_info} - {patient} ({service}) at {location}")
            else:
                message_parts.append(f"\n👨‍⚕️ {provider}: No appointments scheduled")
        
        return {
            'message': '\n'.join(message_parts),
            'formatted_results': results
        }
