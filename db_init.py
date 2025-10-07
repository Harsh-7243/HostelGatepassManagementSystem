import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

def get_db_connection():
    # Use SQLite for easier development setup
    db_path = os.environ.get('DATABASE_PATH', 'gatepass.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_database():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Drop tables in correct order (respecting foreign key constraints)
    cur.execute('DROP TABLE IF EXISTS activity_logs')
    cur.execute('DROP TABLE IF EXISTS user_sessions')
    cur.execute('DROP TABLE IF EXISTS gatepass_requests')
    cur.execute('DROP TABLE IF EXISTS student_parent_links')
    cur.execute('DROP TABLE IF EXISTS pending_registrations')
    cur.execute('DROP TABLE IF EXISTS students')
    cur.execute('DROP TABLE IF EXISTS parents')
    cur.execute('DROP TABLE IF EXISTS wardens')
    cur.execute('DROP TABLE IF EXISTS security_guards')
    
    # Students Table - Enhanced with additional fields
    cur.execute('''
        CREATE TABLE students (
            student_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(20),
            hostel_block VARCHAR(50),
            room_number VARCHAR(20),
            course VARCHAR(100),
            year_of_study INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Parents Table - Enhanced with additional fields
    cur.execute('''
        CREATE TABLE parents (
            parent_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(20) NOT NULL,
            relationship VARCHAR(50),
            address TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Wardens Table - Enhanced with additional fields
    cur.execute('''
        CREATE TABLE wardens (
            warden_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(20),
            hostel_block VARCHAR(50),
            designation VARCHAR(100),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Security Guards Table - Enhanced with additional fields
    cur.execute('''
        CREATE TABLE security_guards (
            guard_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            email VARCHAR(100) UNIQUE,
            phone VARCHAR(20),
            shift VARCHAR(50),
            gate_assigned VARCHAR(50),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
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
    
    # Insert 5 students with Indian names and additional details
    cur.execute('''
        INSERT INTO students (student_id, name, password_hash, email, phone, hostel_block, room_number, course, year_of_study) VALUES
        ('STU001', 'Arjun Kumar', ?, 'arjun.kumar@student.edu', '9876543210', 'Block A', 'A-101', 'Computer Science', 2),
        ('STU002', 'Priya Sharma', ?, 'priya.sharma@student.edu', '9876543211', 'Block B', 'B-205', 'Electronics', 3),
        ('STU003', 'Rohit Patel', ?, 'rohit.patel@student.edu', '9876543212', 'Block A', 'A-304', 'Mechanical', 1),
        ('STU004', 'Sneha Gupta', ?, 'sneha.gupta@student.edu', '9876543213', 'Block C', 'C-102', 'Civil Engineering', 2),
        ('STU005', 'Vikram Singh', ?, 'vikram.singh@student.edu', '9876543214', 'Block A', 'A-210', 'Information Technology', 4)
    ''', (password_hash, password_hash, password_hash, password_hash, password_hash))
    
    # Insert 5 parents with Indian names and additional details
    cur.execute('''
        INSERT INTO parents (parent_id, name, password_hash, email, phone, relationship, address) VALUES
        ('PAR001', 'Rajesh Kumar', ?, 'rajesh.kumar@gmail.com', '9876543220', 'Father', 'Mumbai, Maharashtra'),
        ('PAR002', 'Sunita Sharma', ?, 'sunita.sharma@gmail.com', '9876543221', 'Mother', 'Delhi, NCR'),
        ('PAR003', 'Mahesh Patel', ?, 'mahesh.patel@gmail.com', '9876543222', 'Father', 'Ahmedabad, Gujarat'),
        ('PAR004', 'Kavita Gupta', ?, 'kavita.gupta@gmail.com', '9876543223', 'Mother', 'Lucknow, UP'),
        ('PAR005', 'Suresh Singh', ?, 'suresh.singh@gmail.com', '9876543224', 'Father', 'Jaipur, Rajasthan')
    ''', (password_hash, password_hash, password_hash, password_hash, password_hash))
    
    # Insert wardens with Indian names and additional details
    cur.execute('''
        INSERT INTO wardens (warden_id, name, password_hash, email, phone, hostel_block, designation) VALUES
        ('WAR001', 'Dr. Ramesh Verma', ?, 'ramesh.verma@college.edu', '9876543230', 'Block A', 'Chief Warden'),
        ('WAR002', 'Prof. Meera Joshi', ?, 'meera.joshi@college.edu', '9876543231', 'Block B', 'Assistant Warden')
    ''', (password_hash, password_hash))
    
    # Insert security guards with Indian names and additional details
    cur.execute('''
        INSERT INTO security_guards (guard_id, name, password_hash, email, phone, shift, gate_assigned) VALUES
        ('SEC001', 'Ravi Shankar', ?, 'ravi.shankar@college.edu', '9876543240', 'Day', 'Main Gate'),
        ('SEC002', 'Mohan Lal', ?, 'mohan.lal@college.edu', '9876543241', 'Night', 'Main Gate'),
        ('SEC003', 'Deepak Kumar', ?, 'deepak.kumar@college.edu', '9876543242', 'Evening', 'Side Gate')
    ''', (password_hash, password_hash, password_hash))
    
    # Student-Parent Relationship Table
    cur.execute('''
        CREATE TABLE student_parent_links (
            student_id VARCHAR(50) REFERENCES students(student_id),
            parent_id VARCHAR(50) REFERENCES parents(parent_id),
            linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (student_id, parent_id)
        )
    ''')
    
    # Pending Registrations Table - For new user sign-ups
    cur.execute('''
        CREATE TABLE pending_registrations (
            registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type VARCHAR(20) NOT NULL CHECK(user_type IN ('student', 'parent', 'warden', 'security')),
            proposed_user_id VARCHAR(50) NOT NULL,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            password_hash VARCHAR(200) NOT NULL,
            
            -- Student-specific fields
            parent_id VARCHAR(50),
            hostel_block VARCHAR(50),
            room_number VARCHAR(20),
            course VARCHAR(100),
            year_of_study INTEGER,
            
            -- Parent-specific fields
            student_id VARCHAR(50),
            relationship VARCHAR(50),
            address TEXT,
            
            -- Warden-specific fields
            designation VARCHAR(100),
            
            -- Security-specific fields
            shift VARCHAR(50),
            gate_assigned VARCHAR(50),
            
            -- Registration metadata
            status VARCHAR(20) DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by VARCHAR(50),
            rejection_reason TEXT,
            verification_token VARCHAR(100) UNIQUE,
            
            UNIQUE(user_type, proposed_user_id),
            UNIQUE(user_type, email)
        )
    ''')
    
    # User Sessions Table - For managing active sessions
    cur.execute('''
        CREATE TABLE user_sessions (
            session_id VARCHAR(100) PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            user_type VARCHAR(20) NOT NULL CHECK(user_type IN ('student', 'parent', 'warden', 'security')),
            ip_address VARCHAR(50),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Activity Logs Table - For audit trail
    cur.execute('''
        CREATE TABLE activity_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(50),
            user_type VARCHAR(20) CHECK(user_type IN ('student', 'parent', 'warden', 'security', 'system')),
            action VARCHAR(100) NOT NULL,
            description TEXT,
            ip_address VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
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
