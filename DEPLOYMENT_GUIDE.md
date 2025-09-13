# Healthcare Appointment Booking System - Deployment Guide

## Overview
This guide covers the deployment of a production-ready healthcare appointment booking system with natural language query processing and SQL Server integration.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask App     │    │   SQL Server    │
│   (Browser)     │◄──►│   (Python)      │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   File System   │
                       │   (Logs/Cache)  │
                       └─────────────────┘
```

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+), Windows Server 2019+, or macOS
- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: 10GB+ available space
- **Network**: Outbound HTTPS access for dependencies

### Dependencies
- SQL Server 2017+ (local or remote)
- ODBC Driver 18 for SQL Server
- Python packages (see requirements.txt)

## 🚀 Installation

### 1. Clone and Setup
```bash
git clone <your-repository>
cd M-pm
```

### 2. Create Virtual Environment
```bash
python3 -m venv healthcare_env
source healthcare_env/bin/activate  # Linux/macOS
# Or on Windows:
# healthcare_env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
# Run the database setup script
python setup_database.py
```

### 5. Environment Configuration
```bash
# Copy the appropriate environment file
cp .env.development .env  # For development
# OR
cp .env.production .env   # For production

# Edit .env with your specific settings
nano .env
```

## 🔧 Configuration

### Required Environment Variables

#### Database Configuration
```bash
SQL_SERVER=your-sql-server-hostname
SQL_DATABASE=AIStagingDB_20250811
SQL_USERNAME=your-username
SQL_PASSWORD=your-password
SQL_DRIVER=ODBC Driver 18 for SQL Server
```

#### Application Settings
```bash
SECRET_KEY=your-super-secret-key-min-32-chars
FLASK_ENV=production
FLASK_DEBUG=False
HOST=0.0.0.0
PORT=5001
```

### Database Schema
The application expects the following main tables:
- `Patients`: Patient information
- `Therapists`: Healthcare provider information
- `Appointments`: Appointment scheduling
- `AvailableSlots`: Provider availability

## 🏃‍♂️ Running the Application

### Development Mode
```bash
python app/production_healthcare_app.py
```

### Production Mode (with Gunicorn)
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5001 --workers 4 app.production_healthcare_app:app
```

### Production Mode (with systemd)
Create a systemd service file:

```bash
sudo nano /etc/systemd/system/healthcare-app.service
```

```ini
[Unit]
Description=Healthcare Appointment Booking System
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/app/healthcare_env/bin
ExecStart=/path/to/your/app/healthcare_env/bin/gunicorn --bind 0.0.0.0:5001 --workers 4 app.production_healthcare_app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable healthcare-app
sudo systemctl start healthcare-app
sudo systemctl status healthcare-app
```

## 🔐 Security Configuration

### SSL/TLS Setup (Nginx Reverse Proxy)
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 80/tcp    # HTTP (for redirects)
sudo ufw enable
```

## 📊 Monitoring and Logging

### Log Files
- Application logs: `/var/log/healthcare-app/app.log`
- Audit logs: `/var/log/healthcare-app/audit.log`
- Error logs: Check systemd journal with `journalctl -u healthcare-app`

### Health Checks
The application provides health check endpoints:
- **GET** `/health` - Basic health check
- **GET** `/health/database` - Database connectivity check

### Monitoring Setup
```bash
# Monitor application logs
tail -f /var/log/healthcare-app/app.log

# Monitor system service
journalctl -u healthcare-app -f
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Integration Tests
```bash
# Test database connectivity
python -c "from healthcare_database_manager_sqlserver import HealthcareDatabaseManager; db = HealthcareDatabaseManager(); print('Database connection:', db.test_connection())"

# Test API endpoints
curl -X GET http://localhost:5001/health
curl -X GET http://localhost:5001/health/database
```

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Basic load test
ab -n 1000 -c 10 http://localhost:5001/health
```

## 🔄 Backup and Maintenance

### Database Backups
```bash
# Create backup script
cat > backup_database.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
sqlcmd -S your-server -d AIStagingDB_20250811 -Q "BACKUP DATABASE AIStagingDB_20250811 TO DISK = '/backups/healthcare_$DATE.bak'"
EOF

chmod +x backup_database.sh

# Schedule with crontab
crontab -e
# Add: 0 2 * * * /path/to/backup_database.sh
```

### Application Updates
```bash
# Stop service
sudo systemctl stop healthcare-app

# Update code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if any)
python setup_database.py

# Start service
sudo systemctl start healthcare-app
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check SQL Server connectivity
telnet your-sql-server 1433

# Verify ODBC driver
odbcinst -q -d
```

#### Permission Issues
```bash
# Fix log directory permissions
sudo mkdir -p /var/log/healthcare-app
sudo chown www-data:www-data /var/log/healthcare-app
sudo chmod 755 /var/log/healthcare-app
```

#### Memory Issues
```bash
# Monitor memory usage
htop
free -h

# Adjust Gunicorn workers if needed
# Reduce worker count in systemd service file
```

### Debug Mode
To enable debug mode temporarily:
```bash
export FLASK_DEBUG=True
export LOG_LEVEL=DEBUG
python app/production_healthcare_app.py
```

## 📞 Support and Maintenance

### Key Endpoints
- **Chat Interface**: `/` (GET)
- **Chat API**: `/chat` (POST)
- **Natural Language Query**: `/query` (POST)
- **Appointment Booking**: `/book_appointment` (POST)
- **Admin Dashboard**: `/admin` (GET)
- **Health Check**: `/health` (GET)

### Performance Tuning
- Adjust Gunicorn worker count based on CPU cores
- Configure database connection pooling
- Implement Redis for session storage (for multi-server deployments)
- Enable application-level caching for frequently accessed data

### Security Best Practices
- Regularly update dependencies
- Monitor access logs for suspicious activity
- Implement rate limiting for API endpoints
- Use strong, unique passwords for all accounts
- Enable audit logging for all patient data access

## 📈 Scaling Considerations

For high-traffic deployments:
1. **Load Balancer**: Use Nginx or HAProxy
2. **Database**: Consider read replicas
3. **Caching**: Implement Redis/Memcached
4. **Monitoring**: Use Prometheus + Grafana
5. **Container Deployment**: Consider Docker + Kubernetes

---

## 📚 Additional Resources

- [Flask Production Deployment Guide](https://flask.palletsprojects.com/en/2.0.x/deploying/)
- [SQL Server Security Best Practices](https://docs.microsoft.com/en-us/sql/relational-databases/security/security-center-for-sql-server-database-engine-and-azure-sql-database)
- [HIPAA Compliance Guidelines](https://www.hhs.gov/hipaa/for-professionals/security/index.html)

---

**Note**: This is a healthcare application. Ensure compliance with relevant healthcare regulations (HIPAA, GDPR, etc.) in your jurisdiction before deploying to production.
