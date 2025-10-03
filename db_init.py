import sqlite3
import os
from werkzeug.security import generate_password_hash

def get_db_connection():
    # Use SQLite for easier development setup
    db_path = os.environ.get('DATABASE_PATH', 'gatepass.db')
    return sqlite3.connect(db_path)

def init_database():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('DROP TABLE IF EXISTS gatepass_requests')
    cur.execute('DROP TABLE IF EXISTS student_parent_links')
    cur.execute('DROP TABLE IF EXISTS students')
    cur.execute('DROP TABLE IF EXISTS parents')
    cur.execute('DROP TABLE IF EXISTS wardens')
    cur.execute('DROP TABLE IF EXISTS security_guards')
    
    cur.execute('''
        CREATE TABLE students (
            student_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE parents (
            parent_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE wardens (
            warden_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            email VARCHAR(100)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE security_guards (
            guard_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            shift VARCHAR(50)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE gatepass_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(50) REFERENCES students(student_id),
            parent_email VARCHAR(100) NOT NULL,
            date_time_out TIMESTAMP NOT NULL,
            duration_hours INTEGER NOT NULL,
            destination VARCHAR(200) NOT NULL,
            purpose TEXT NOT NULL,
            parent_approval_status VARCHAR(20) DEFAULT 'Pending',
            parent_approval_timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expiry_timestamp TIMESTAMP,
            warden_status VARCHAR(20) DEFAULT 'Open',
            security_guard_status VARCHAR(20) DEFAULT 'Pending'
        )
    ''')
    
    password_hash = generate_password_hash('college123')
    
    # Insert 5 students with Indian names
    cur.execute('''
        INSERT INTO students (student_id, name, password_hash, email, phone) VALUES
        ('STU001', 'Arjun Kumar', ?, 'arjun.kumar@student.edu', '9876543210'),
        ('STU002', 'Priya Sharma', ?, 'priya.sharma@student.edu', '9876543211'),
        ('STU003', 'Rohit Patel', ?, 'rohit.patel@student.edu', '9876543212'),
        ('STU004', 'Sneha Gupta', ?, 'sneha.gupta@student.edu', '9876543213'),
        ('STU005', 'Vikram Singh', ?, 'vikram.singh@student.edu', '9876543214')
    ''', (password_hash, password_hash, password_hash, password_hash, password_hash))
    
    # Insert 5 parents with Indian names
    cur.execute('''
        INSERT INTO parents (parent_id, name, password_hash, email, phone) VALUES
        ('PAR001', 'Rajesh Kumar', ?, 'rajesh.kumar@gmail.com', '9876543220'),
        ('PAR002', 'Sunita Sharma', ?, 'sunita.sharma@gmail.com', '9876543221'),
        ('PAR003', 'Mahesh Patel', ?, 'mahesh.patel@gmail.com', '9876543222'),
        ('PAR004', 'Kavita Gupta', ?, 'kavita.gupta@gmail.com', '9876543223'),
        ('PAR005', 'Suresh Singh', ?, 'suresh.singh@gmail.com', '9876543224')
    ''', (password_hash, password_hash, password_hash, password_hash, password_hash))
    
    # Insert wardens with Indian names
    cur.execute('''
        INSERT INTO wardens (warden_id, name, password_hash, email) VALUES
        ('WAR001', 'Dr. Ramesh Verma', ?, 'ramesh.verma@college.edu'),
        ('WAR002', 'Prof. Meera Joshi', ?, 'meera.joshi@college.edu')
    ''', (password_hash, password_hash))
    
    # Insert security guards with Indian names
    cur.execute('''
        INSERT INTO security_guards (guard_id, name, password_hash, shift) VALUES
        ('SEC001', 'Ravi Shankar', ?, 'Day'),
        ('SEC002', 'Mohan Lal', ?, 'Night'),
        ('SEC003', 'Deepak Kumar', ?, 'Evening')
    ''', (password_hash, password_hash, password_hash))
    
    # Create student-parent relationship table
    cur.execute('''
        CREATE TABLE student_parent_links (
            student_id VARCHAR(50) REFERENCES students(student_id),
            parent_id VARCHAR(50) REFERENCES parents(parent_id),
            PRIMARY KEY (student_id, parent_id)
        )
    ''')
    
    # Insert student-parent relationships
    cur.execute('''
        INSERT INTO student_parent_links (student_id, parent_id) VALUES
        ('STU001', 'PAR001'),
        ('STU002', 'PAR002'),
        ('STU003', 'PAR003'),
        ('STU004', 'PAR004'),
        ('STU005', 'PAR005')
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
