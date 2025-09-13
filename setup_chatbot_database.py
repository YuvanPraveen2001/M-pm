import sqlite3
from datetime import datetime, date, time, timedelta
import json

def setup_chatbot_database():
    """Setup the enhanced database for the therapist booking chatbot"""
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()

    # Read and execute the schema
    with open('chatbot_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    # Execute schema (split by semicolon to handle multiple statements)
    statements = schema_sql.split(';')
    for statement in statements:
        if statement.strip():
            cursor.execute(statement)

    # Clear existing data
    tables = ['appointments', 'appointment_slots', 'therapist_specializations', 
              'chat_messages', 'chat_sessions', 'patients', 'therapists', 'specializations']
    for table in tables:
        cursor.execute(f'DELETE FROM {table}')

    # Insert sample specializations
    specializations = [
        (1, 'Anxiety and Stress', 'Specialized in treating anxiety disorders and stress management'),
        (2, 'Depression', 'Expert in depression therapy and mood disorders'),
        (3, 'Relationship Counseling', 'Couples and relationship therapy'),
        (4, 'Trauma and PTSD', 'Trauma-informed therapy and PTSD treatment'),
        (5, 'Addiction Recovery', 'Substance abuse and addiction counseling'),
        (6, 'Child Psychology', 'Specialized in child and adolescent therapy'),
        (7, 'Family Therapy', 'Family systems and dynamics therapy'),
        (8, 'Cognitive Behavioral Therapy', 'CBT specialist for various mental health conditions'),
        (9, 'Mindfulness and Meditation', 'Mindfulness-based therapeutic approaches'),
        (10, 'Career Counseling', 'Professional and career development therapy')
    ]
    cursor.executemany('INSERT INTO specializations VALUES (?, ?, ?)', specializations)

    # Insert sample therapists
    therapists = [
        (1, 'Dr. Sarah Johnson', 'Anxiety and Stress', 8, 4.8, '+1-555-0101', 'sarah.johnson@therapy.com', 
         'Dr. Johnson specializes in anxiety disorders with over 8 years of experience using CBT techniques.', 150.0, 1, datetime.now()),
        (2, 'Dr. Michael Chen', 'Depression', 12, 4.9, '+1-555-0102', 'michael.chen@therapy.com',
         'Experienced psychiatrist specializing in depression and mood disorders.', 180.0, 1, datetime.now()),
        (3, 'Dr. Emily Rodriguez', 'Relationship Counseling', 10, 4.7, '+1-555-0103', 'emily.rodriguez@therapy.com',
         'Licensed marriage and family therapist with expertise in relationship dynamics.', 160.0, 1, datetime.now()),
        (4, 'Dr. David Thompson', 'Trauma and PTSD', 15, 4.9, '+1-555-0104', 'david.thompson@therapy.com',
         'Trauma specialist with extensive experience in PTSD treatment and recovery.', 200.0, 1, datetime.now()),
        (5, 'Dr. Lisa Wong', 'Child Psychology', 9, 4.6, '+1-555-0105', 'lisa.wong@therapy.com',
         'Child psychologist specializing in developmental and behavioral issues.', 140.0, 1, datetime.now()),
        (6, 'Dr. Robert Kim', 'Addiction Recovery', 11, 4.8, '+1-555-0106', 'robert.kim@therapy.com',
         'Addiction counselor with expertise in substance abuse recovery programs.', 170.0, 1, datetime.now())
    ]
    cursor.executemany('INSERT INTO therapists VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', therapists)

    # Insert sample patients
    patients = [
        (1, 'John Smith', 'john.smith@email.com', '+1-555-1001', '1985-03-15', 'Male', 'Jane Smith +1-555-1002', 'Blue Cross Blue Shield', datetime.now()),
        (2, 'Maria Garcia', 'maria.garcia@email.com', '+1-555-1003', '1990-07-22', 'Female', 'Carlos Garcia +1-555-1004', 'Aetna', datetime.now()),
        (3, 'Alex Johnson', 'alex.johnson@email.com', '+1-555-1005', '1988-11-08', 'Non-binary', 'Sam Johnson +1-555-1006', 'Cigna', datetime.now())
    ]
    cursor.executemany('INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', patients)

    # Create available appointment slots for the next 30 days
    today = date.today()
    therapist_ids = [1, 2, 3, 4, 5, 6]
    time_slots = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00']
    
    slot_id = 1
    for days_ahead in range(30):  # Next 30 days
        slot_date = today + timedelta(days=days_ahead)
        # Skip weekends
        if slot_date.weekday() < 5:  # Monday = 0, Friday = 4
            for therapist_id in therapist_ids:
                for time_slot in time_slots:
                    cursor.execute('''
                        INSERT INTO appointment_slots 
                        (id, therapist_id, slot_date, slot_time, duration_minutes, is_available, session_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (slot_id, therapist_id, slot_date.isoformat(), time_slot, 60, 1, 'individual'))
                    slot_id += 1

    # Insert some sample appointments (booked slots)
    sample_appointments = [
        (1, 1, 1, 1, (today + timedelta(days=2)).isoformat(), '10:00', 60, 'individual', 'scheduled', 'Initial consultation for anxiety', datetime.now()),
        (2, 2, 2, 15, (today + timedelta(days=3)).isoformat(), '14:00', 60, 'individual', 'scheduled', 'Follow-up session for depression', datetime.now())
    ]
    cursor.executemany('INSERT INTO appointments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', sample_appointments)

    # Mark those slots as unavailable
    cursor.execute('UPDATE appointment_slots SET is_available = 0 WHERE id IN (1, 15)')

    # Insert therapist specializations
    therapist_specs = [
        (1, 1), (1, 8), (1, 9),  # Dr. Johnson: Anxiety, CBT, Mindfulness
        (2, 2), (2, 8),          # Dr. Chen: Depression, CBT
        (3, 3), (3, 7),          # Dr. Rodriguez: Relationship, Family
        (4, 4), (4, 8),          # Dr. Thompson: Trauma, CBT
        (5, 6), (5, 7),          # Dr. Wong: Child, Family
        (6, 5), (6, 8)           # Dr. Kim: Addiction, CBT
    ]
    cursor.executemany('INSERT INTO therapist_specializations VALUES (?, ?)', therapist_specs)

    conn.commit()
    conn.close()
    print("Chatbot database `chatbot.db` created and populated successfully!")
    print("Database includes:")
    print("- 6 therapists with different specializations")
    print("- Sample patients and appointment data")
    print("- Available appointment slots for the next 30 days")
    print("- Conversation tracking tables for chatbot functionality")

if __name__ == '__main__':
    setup_chatbot_database()
