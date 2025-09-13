# Healthcare AI Chatbot System 🏥🤖

A production-ready healthcare appointment booking system with advanced AI chatbot capabilities, natural language query processing, and comprehensive database integration.

## ✨ Key Features

- **🤖 AI-Powered Chatbot**: Natural language understanding for healthcare queries
- **📅 Appointment Management**: Complete booking and scheduling system
- **🔍 Smart Search**: Find providers by specialization, location, availability
- **💬 Natural Language Queries**: "Check John's availability this Wednesday"
- **🗄️ Multi-Database Support**: SQLite (dev) and SQL Server (production)
- **🧠 RAG System**: Qdrant vector database with semantic search
- **🛡️ Enterprise Security**: HIPAA-compliant with audit logging
- **📊 Admin Dashboard**: Provider and appointment management
- **🔧 Tools Architecture**: Modular, extensible tool registry system

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and navigate to project
cd M-pm

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment configuration
cp .env.development .env
# Edit .env with your database credentials
```

### 2. Database Initialization
```bash
# Setup healthcare database with sample data
python setup_chatbot_database.py

# Verify database setup
python -c "from healthcare_database_manager import HealthcareDatabaseManager; print('✅ Database ready!')"
```

### 3. Start the Application
```bash
# Development mode
python app/healthcare_chatbot_app.py

# Production mode
python app/production_healthcare_app.py
```

### 4. Test the Chatbot
Open `http://localhost:5001` and try these queries:
- "Check availability of John this Wednesday"
- "Show me appointments for Sarah tomorrow"
- "Find therapists specializing in anxiety near me"
- "Book an appointment with Dr. Smith next Monday at 2pm"

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │    │   AI Processor  │    │   Tool Registry │
│  (Natural Lang) │───▶│   (NLP + RAG)   │───▶│   (Validation)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Response      │    │   Database      │    │   Tool Execution│
│  (Formatted)    │◀───│   (SQL Server)  │◀───│   (SQL/API)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Core Components

### AI/ML Stack
- **Natural Language Processor**: Intent detection and entity extraction
- **RAG System**: Qdrant vector database with semantic search
- **Local AI Models**: Ollama with `phi3:mini` and `nomic-embed-text`
- **Tool Registry**: Extensible healthcare-specific tools

### Database Layer
- **SQLite**: Development and testing
- **SQL Server**: Production healthcare data
- **Vector DB**: Qdrant for semantic search and embeddings

### Web Framework
- **Flask**: Core web framework with CORS support
- **RESTful APIs**: Comprehensive endpoint architecture
- **Real-time Chat**: WebSocket-ready chat interface
- **Admin Dashboard**: Provider and appointment management

## 📋 Use Cases & Examples

### 1. Availability Checking
```
👤 User: "Is Dr. Johnson available this Friday afternoon?"

🤖 Bot: "✅ Dr. Sarah Johnson is available this Friday, September 15th:
        • 2:00 PM - 3:00 PM (Available)
        • 3:00 PM - 4:00 PM (Available)
        • 4:00 PM - 5:00 PM (Busy - with Patient Smith)"
```

### 2. Appointment Booking
```
👤 User: "Book me with a therapist specializing in anxiety next week"

🤖 Bot: "I found 3 anxiety specialists available next week:
        1. Dr. Sarah Johnson (4.8★) - Mon 10am, Tue 2pm, Wed 9am
        2. Dr. Lisa Wong (4.6★) - Mon 3pm, Thu 11am, Fri 1pm
        
        Which provider and time works best for you?"
```

### 3. Provider Search
```
👤 User: "Find Spanish-speaking therapists in zip code 90210"

🤖 Bot: "Found 4 Spanish-speaking therapists in 90210:
        • Dr. Emily Rodriguez - Relationship Counseling (4.7★)
        • Dr. Maria Santos - Family Therapy (4.9★)
        • Dr. Carlos Martinez - Trauma & PTSD (4.8★)"
```

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
SQL_SERVER=your-sql-server
SQL_DATABASE=AIStagingDB_20250811
SQL_USERNAME=your-username
SQL_PASSWORD=your-password

# AI Models (Local)
EMBED_MODEL=nomic-embed-text
CHAT_MODEL=phi3:mini

# Application Settings
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

### Local AI Setup
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull required models
ollama pull phi3:mini
ollama pull nomic-embed-text

# Start Ollama service
ollama serve
```

## 📊 Database Schema

Key healthcare tables:
- **Employee**: Healthcare providers with specializations
- **Patient**: Patient information and preferences
- **Appointment**: Scheduled appointments and status
- **EmployeeAvailabilityDateTime**: Provider availability slots
- **Auth/AuthDetail**: Insurance authorization and services

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Test natural language queries
python test_natural_language_queries.py

# Test specific components
python -c "
from ai_chatbot_tools import HealthcareToolsRegistry
registry = HealthcareToolsRegistry()
print(f'Loaded {len(registry.list_available_tools())} tools')
"
```

## 🚀 Deployment

### Development
```bash
python app/healthcare_chatbot_app.py
```

### Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5001 --workers 4 app.production_healthcare_app:app
```

### Docker Deployment
```bash
# Build container
docker build -t healthcare-chatbot .

# Run container
docker run -p 5001:5001 -e SQL_SERVER=your-server healthcare-chatbot
```

See `DEPLOYMENT_GUIDE.md` for comprehensive production deployment instructions.

## 🛡️ Security & Compliance

- **HIPAA Compliance**: Audit logging and data encryption
- **SQL Injection Prevention**: Parameterized queries
- **Authentication**: Session-based security
- **CORS Protection**: Configured cross-origin policies
- **Error Handling**: Secure error responses

## 📈 Performance

- **Vector Search**: Sub-100ms semantic search with Qdrant
- **Database Optimization**: Connection pooling and indexing
- **Caching**: Intelligent caching for frequent queries
- **Scalability**: Horizontal scaling support

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- 📧 Email: support@healthcare-chatbot.com
- 📖 Documentation: See `PROJECT_STRUCTURE.md`
- 🐛 Issues: GitHub Issues tab
- 💬 Discussions: GitHub Discussions

---

**⚠️ Healthcare Notice**: This system is designed for appointment scheduling and administrative tasks. It is not intended for medical diagnosis or treatment recommendations. Always consult healthcare professionals for medical advice.
