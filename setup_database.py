import sqlite3

def setup_database():
    conn = sqlite3.connect('sample.db')
    cursor = conn.cursor()

    # Create departments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
    ''')

    # Create employees table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        salary REAL,
        gender TEXT,
        department_id INTEGER,
        FOREIGN KEY (department_id) REFERENCES departments (id)
    )
    ''')

    # Clear existing data
    cursor.execute('DELETE FROM employees')
    cursor.execute('DELETE FROM departments')

    # Insert sample departments
    departments = [
        (1, 'Engineering'),
        (2, 'Human Resources'),
        (3, 'Sales'),
        (4, 'Marketing')
    ]
    cursor.executemany('INSERT INTO departments VALUES (?, ?)', departments)

    # Insert sample employees
    employees = [
        (1, 'John Doe', 70000, 'Male', 1),
        (2, 'Jane Smith', 80000, 'Female', 1),
        (3, 'Peter Jones', 50000, 'Male', 3),
        (4, 'Mary Williams', 55000, 'Female', 3),
        (5, 'David Brown', 60000, 'Male', 2),
        (6, 'Susan Davis', 65000, 'Female', 4),
        (7, 'Michael Miller', 90000, 'Male', 1),
        (8, 'Linda Wilson', 75000, 'Female', 4),
        (9, 'Robert Moore', 45000, 'Male', 3),
        (10, 'Karen Taylor', 85000, 'Female', 2)
    ]
    cursor.executemany('INSERT INTO employees VALUES (?, ?, ?, ?, ?)', employees)

    conn.commit()
    conn.close()
    print("Database `sample.db` created and populated successfully.")

if __name__ == '__main__':
    setup_database()
