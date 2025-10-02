import psycopg2
import os
from werkzeug.security import generate_password_hash

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def init_database():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('DROP TABLE IF EXISTS gatepass_requests CASCADE')
    cur.execute('DROP TABLE IF EXISTS student_parent_links CASCADE')
    cur.execute('DROP TABLE IF EXISTS students CASCADE')
    cur.execute('DROP TABLE IF EXISTS parents CASCADE')
    cur.execute('DROP TABLE IF EXISTS wardens CASCADE')
    cur.execute('DROP TABLE IF EXISTS security_guards CASCADE')
    
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
            request_id SERIAL PRIMARY KEY,
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
    
    password_hash = generate_password_hash('password123')
    
    cur.execute('''
        INSERT INTO students (student_id, name, password_hash, email, phone) VALUES
        ('STU001', 'John Doe', %s, 'john@example.com', '1234567890'),
        ('STU002', 'Jane Smith', %s, 'jane@example.com', '0987654321')
    ''', (password_hash, password_hash))
    
    cur.execute('''
        INSERT INTO parents (parent_id, name, password_hash, email, phone) VALUES
        ('PAR001', 'Robert Doe', %s, 'robert@example.com', '1111111111'),
        ('PAR002', 'Mary Smith', %s, 'mary@example.com', '2222222222')
    ''', (password_hash, password_hash))
    
    cur.execute('''
        INSERT INTO wardens (warden_id, name, password_hash, email) VALUES
        ('WAR001', 'Dr. Williams', %s, 'williams@example.com')
    ''', (password_hash,))
    
    cur.execute('''
        INSERT INTO security_guards (guard_id, name, password_hash, shift) VALUES
        ('SEC001', 'Guard Anderson', %s, 'Day'),
        ('SEC002', 'Guard Brown', %s, 'Night')
    ''', (password_hash, password_hash))
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
