# Healthcare AI Chatbot - Project Structure

## 📁 Project Overview
This is a production-ready healthcare appointment booking system with AI chatbot capabilities, natural language query processing, and comprehensive database integration.

## 🗂️ Directory Structure

```
M-pm/
├── 📄 README.md                           # Main project documentation
├── 📄 DEPLOYMENT_GUIDE.md                 # Production deployment guide
├── 📄 requirements.txt                    # Python dependencies
├── 📄 .env.development                    # Development environment config
├── 📄 .env.production                     # Production environment config
├── 📄 .env                               # Active environment config (copy from above)
│
├── 🗄️ Database Setup
│   ├── 📄 setup_database.py              # Basic SQLite database setup
│   ├── 📄 setup_chatbot_database.py      # Healthcare chatbot database setup
│   ├── 📄 chatbot_schema.sql             # SQL Server healthcare schema
│   ├── 📄 sample.db                      # SQLite sample database
│   └── 📄 chatbot.db                     # Healthcare chatbot database
│
├── 🤖 AI/ML Components
│   ├── 📄 ai_chatbot_tools.py            # Tool registry and validation system
│   ├── 📄 natural_language_processor.py  # NLP query processor (user-modified)
│   ├── 📄 quadrant_rag_system.py         # RAG system with Qdrant DB
│   ├── 📄 healthcare_database_manager.py # SQLite database manager
│   ├── 📄 healthcare_database_manager_sqlserver.py # SQL Server manager
│   └── 📄 index_schema.py                # Database schema indexing
│
├── 🌐 Web Applications
│   └── app/
│       ├── 📄 app.py                     # Original prototype app
│       ├── 📄 healthcare_chatbot_app.py  # Advanced chatbot app
│       ├── 📄 production_healthcare_app.py # Production-ready app
│       └── 📄 schema_utils.py            # Database schema utilities
│
├── 🎨 Templates
│   └── templates/
│       ├── 📄 index.html                 # Basic query interface
│       ├── 📄 result.html                # Query results display
│       ├── 📄 healthcare_chatbot.html    # Main chatbot interface
│       └── 📄 healthcare_admin.html      # Admin dashboard
│
├── 🧪 Testing
│   └── 📄 test_natural_language_queries.py # NLP testing suite
│
├── 🗃️ Vector Database
│   └── chroma_db/                        # ChromaDB vector store
│       ├── 📄 chroma.sqlite3
│       └── 📄 chroma copy.sqlite3
│
└── 🐍 Python Environment
    └── venv/                             # Virtual environment
```

## 🔧 Core Components

### 1. **AI Chatbot Tools** (`ai_chatbot_tools.py`)
- **Tool Registry System**: Manages all available tools and endpoints
- **Validation Layer**: Ensures proper parameter collection and validation
- **Business Rules Engine**: Applies healthcare-specific business logic
- **Tool Types**: Database queries, API endpoints, appointment booking

### 2. **Natural Language Processor** (`natural_language_processor.py`) ⭐ *User Modified*
- **Intent Detection**: Identifies user intent (availability, appointments, schedule)
- **Entity Extraction**: Extracts person names, dates, and context
- **Query Generation**: Converts natural language to SQL
- **Response Formatting**: Human-friendly result presentation

### 3. **RAG System** (`quadrant_rag_system.py`)
- **Qdrant Integration**: Vector database for semantic search
- **Embedding Models**: `nomic-embed-text` for document embeddings
- **Chat Models**: `phi3:mini` for conversation generation
- **Context Management**: Maintains conversation history and context

### 4. **Database Managers**
- **SQLite Manager**: Local development and testing
- **SQL Server Manager**: Production healthcare database
- **Schema Utilities**: Database schema introspection and indexing

### 5. **Web Applications**
- **Prototype App**: Basic query interface (`app/app.py`)
- **Advanced Chatbot**: Multi-step booking workflow (`healthcare_chatbot_app.py`)
- **Production App**: Enterprise-ready with security, logging, monitoring

## 🚀 Usage Scenarios

### 1. **Appointment Booking**
```
User: "I need to book an appointment with Dr. Smith next Tuesday"
System: Tool selection → Parameter gathering → Validation → Booking execution
```

### 2. **Availability Checking**
```
User: "Check availability of John this Wednesday"
System: NLP analysis → SQL generation → Database query → Formatted response
```

### 3. **Provider Search**
```
User: "Find therapists in zip code 12345 who speak Spanish"
System: Filter application → Database search → Results ranking → Presentation
```

### 4. **Schedule Management**
```
User: "Show me Sarah's schedule for next week"
System: Date parsing → Employee lookup → Schedule retrieval → Calendar format
```

## 🛡️ Security Features

- **Environment-based Configuration**: Separate dev/prod configs
- **SQL Injection Prevention**: Parameterized queries and validation
- **CORS Protection**: Controlled cross-origin requests
- **Session Management**: Secure session handling
- **Audit Logging**: Comprehensive activity tracking
- **Error Handling**: Secure error responses without data leakage

## 🔄 Development Workflow

### 1. **Tool Registration**
```python
registry = HealthcareToolsRegistry()
registry.register_tool("check_availability", tool_config)
```

### 2. **Query Processing**
```python
processor = HealthcareQueryProcessor(db_manager)
result = processor.process_query("Check John's availability tomorrow")
```

### 3. **RAG Integration**
```python
chatbot = EnhancedHealthcareChatbot()
response = chatbot.process_message("Book appointment with Dr. Smith")
```

## 📊 Database Schema

The system supports multiple database configurations:

- **Development**: SQLite with sample data
- **Production**: SQL Server with full healthcare schema
- **Testing**: In-memory databases for unit tests

Key tables:
- `Employee` - Healthcare providers
- `Patient` - Patient information
- `Appointment` - Scheduled appointments
- `EmployeeAvailabilityDateTime` - Provider availability
- `Auth` / `AuthDetail` - Authorization and service details

## 🔌 Integration Points

### External APIs
- **OpenAI API**: Enhanced NLP capabilities (optional)
- **Twilio**: SMS notifications (optional)
- **Email Services**: Appointment confirmations

### Local AI Models
- **Ollama**: Local model serving
- **Embedding Models**: Text vectorization
- **Chat Models**: Conversation generation

## 📈 Performance Considerations

- **Vector Database**: Qdrant for fast semantic search
- **Connection Pooling**: Database connection optimization
- **Caching**: Frequently accessed data caching
- **Async Processing**: Background task handling

## 🧪 Testing Strategy

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **NLP Tests**: Natural language query validation
- **Database Tests**: SQL query accuracy verification

## 🚀 Deployment Options

1. **Development**: Local Flask server with SQLite
2. **Staging**: Containerized deployment with test database
3. **Production**: Load-balanced deployment with SQL Server
4. **Cloud**: AWS/Azure deployment with managed services

---

## 📞 Quick Start

1. **Setup Environment**:
   ```bash
   cp .env.development .env
   pip install -r requirements.txt
   ```

2. **Initialize Database**:
   ```bash
   python setup_chatbot_database.py
   ```

3. **Start Application**:
   ```bash
   python app/production_healthcare_app.py
   ```

4. **Test Chatbot**:
   Navigate to `http://localhost:5001` and try:
   - "Check availability of John this Wednesday"
   - "Show me appointments for Sarah tomorrow"
   - "Find therapists in my area"
