# 🗄️ External SQL Server Setup Guide

## Quick Setup Steps

### 1. Update your .env file with your SQL Server details:

```bash
# Copy the example and edit with your details
cp .env.example .env
```

Then edit `.env` with your actual SQL Server information:

```properties
# Your SQL Server details
SQL_SERVER=your-sql-server-hostname-or-ip
SQL_DATABASE=your-database-name  
SQL_USERNAME=your-username
SQL_PASSWORD=your-password
SQL_DRIVER=ODBC Driver 18 for SQL Server

# Connection timeout settings
SQL_CONNECTION_TIMEOUT=30
SQL_COMMAND_TIMEOUT=30
```

### 2. Common SQL Server Connection Examples:

**Local SQL Server:**
```properties
SQL_SERVER=localhost
SQL_DATABASE=HealthcareDB
SQL_USERNAME=sa
SQL_PASSWORD=YourPassword123!
```

**Remote SQL Server:**
```properties
SQL_SERVER=192.168.1.100
SQL_DATABASE=HealthcareDB
SQL_USERNAME=healthcare_user
SQL_PASSWORD=SecurePassword123!
```

**Azure SQL Database:**
```properties
SQL_SERVER=yourserver.database.windows.net
SQL_DATABASE=healthcare-db
SQL_USERNAME=admin@yourserver
SQL_PASSWORD=AzurePassword123!
```

**SQL Server with custom port:**
```properties
SQL_SERVER=yourserver.com,1433
SQL_DATABASE=HealthcareDB
SQL_USERNAME=healthcare_user
SQL_PASSWORD=YourPassword123!
```

### 3. Test the connection:

After updating your .env file, restart the application and visit:
```
http://localhost:5001/api/test-db
```

This will show you if the connection is working.

### 4. Common Connection Issues & Solutions:

**❌ "Login timeout expired"**
- Check if SQL Server is running
- Verify firewall settings (port 1433)
- Confirm server hostname/IP is correct
- Test network connectivity: `telnet your-server 1433`

**❌ "Login failed"**
- Verify username and password
- Check if SQL Server authentication is enabled
- Ensure user has database access permissions

**❌ "Cannot open database"**
- Verify database name is correct
- Check if user has access to the specific database
- Confirm database exists

**❌ "SSL Provider: No credentials are available"**
- Add `TrustServerCertificate=yes` (already included)
- Or configure proper SSL certificates

### 5. Required Database Tables:

Your SQL Server database should have these tables:
- `Patients` (with PatientId, FirstName, LastName, etc.)
- `Employees` (with EmployeeId, EmployeeName, etc.)
- `Appointments` (appointment data)
- `ChatSessions` (optional, for conversation logging)
- `ChatMessages` (optional, for message logging)

### 6. Firewall Configuration:

If connecting to a remote SQL Server, ensure these ports are open:
- **Port 1433**: Default SQL Server port
- **Port 1434**: SQL Server Browser (for named instances)

### 7. Enable SQL Server Authentication:

If using username/password (not Windows Auth):
1. Open SQL Server Management Studio
2. Right-click server → Properties → Security
3. Select "SQL Server and Windows Authentication mode"
4. Restart SQL Server service

## Troubleshooting Commands:

**Test connection from terminal:**
```bash
# Test if the server is reachable
ping your-sql-server-hostname

# Test if SQL Server port is open
telnet your-sql-server-hostname 1433
```

**Check ODBC drivers:**
```bash
# List available ODBC drivers
odbcinst -q -d
```

**Test from Python:**
```python
import pyodbc
conn_str = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=your-server;DATABASE=your-db;UID=user;PWD=pass;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
print("Connection successful!")
```

## Need Help?

1. **Check the application logs** - they'll show detailed connection errors
2. **Visit `/api/test-db`** - for connection testing
3. **Enable debug logging** - set `LOG_LEVEL=DEBUG` in .env
4. **Check SQL Server logs** - for server-side issues

The application will now work even if the database connection fails initially - it will just skip the database logging and focus on the chatbot functionality.
