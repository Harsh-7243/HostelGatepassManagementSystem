import os
import sys
import logging
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Get a database connection based on the environment.
    Automatically detects if we're using PostgreSQL or SQLite.
    """
    try:
        # Check for PostgreSQL connection string (from Render)
        if 'DATABASE_URL' in os.environ:
            import psycopg2
            result = urlparse(os.environ['DATABASE_URL'])
            conn = psycopg2.connect(
                database=result.path[1:],  # Remove leading '/'
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port
            )
            logger.info("Connected to PostgreSQL database")
            return conn
        else:
            # Fall back to SQLite for local development
            import sqlite3
            db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database at {db_path}")
            return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def init_db():
    """Initialize the database with required tables."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if we're using PostgreSQL
        is_postgres = 'postgresql' in os.environ.get('DATABASE_URL', '')
        
        # Drop existing tables (uncomment only for development)
        # drop_tables(cur, is_postgres)
        
        # Create tables
        create_tables(cur, is_postgres)
        
        # Add initial data
        add_initial_data(cur, is_postgres)
        
        conn.commit()
        logger.info("✅ Database initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def drop_tables(cur, is_postgres):
    """Drop all tables (for development only)."""
    tables = [
        'gatepass_requests', 'student_parent_links', 
        'pending_registrations', 'students', 
        'parents', 'wardens', 'security_guards'
    ]
    for table in tables:
        try:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            logger.info(f"Dropped table: {table}")
        except Exception as e:
            logger.warning(f"Could not drop table {table}: {e}")

def create_tables(cur, is_postgres):
    """Create all required tables."""
    # Students table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            hostel VARCHAR(50),
            room_number VARCHAR(20),
            phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''' if is_postgres else '''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            hostel TEXT,
            room_number TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Parents table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS parents (
            parent_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''' if is_postgres else '''
        CREATE TABLE IF NOT EXISTS parents (
            parent_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Wardens table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS wardens (
            warden_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            hostel_assigned VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''' if is_postgres else '''
        CREATE TABLE IF NOT EXISTS wardens (
            warden_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            hostel_assigned TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Security Guards table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS security_guards (
            guard_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            shift_timings TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''' if is_postgres else '''
        CREATE TABLE IF NOT EXISTS security_guards (
            guard_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            shift_timings TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Gatepass Requests table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS gatepass_requests (
            request_id SERIAL PRIMARY KEY,
            student_id VARCHAR(50) REFERENCES students(student_id),
            parent_id VARCHAR(50) REFERENCES parents(parent_id),
            departure_time TIMESTAMP NOT NULL,
            expected_return_time TIMESTAMP NOT NULL,
            destination TEXT NOT NULL,
            reason TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            approved_by_warden BOOLEAN DEFAULT FALSE,
            approved_by_parent BOOLEAN DEFAULT FALSE,
            warden_remarks TEXT,
            parent_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''' if is_postgres else '''
        CREATE TABLE IF NOT EXISTS gatepass_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            parent_id TEXT,
            departure_time TIMESTAMP NOT NULL,
            expected_return_time TIMESTAMP NOT NULL,
            destination TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            approved_by_warden BOOLEAN DEFAULT 0,
            approved_by_parent BOOLEAN DEFAULT 0,
            warden_remarks TEXT,
            parent_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (parent_id) REFERENCES parents(parent_id)
        )
    ''')

    # Student-Parent Links table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS student_parent_links (
            student_id VARCHAR(50) REFERENCES students(student_id),
            parent_id VARCHAR(50) REFERENCES parents(parent_id),
            relationship VARCHAR(50),
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (student_id, parent_id)
        )
    ''' if is_postgres else '''
        CREATE TABLE IF NOT EXISTS student_parent_links (
            student_id TEXT,
            parent_id TEXT,
            relationship TEXT,
            is_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (student_id, parent_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (parent_id) REFERENCES parents(parent_id)
        )
    ''')

    # Pending Registrations table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pending_registrations (
            registration_id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            user_type VARCHAR(20) NOT NULL,  # 'student', 'parent', 'warden', 'security'
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            verification_token VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''' if is_postgres else '''
        CREATE TABLE IF NOT EXISTS pending_registrations (
            registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            user_type TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            verification_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')

    logger.info("✅ Database tables created successfully")

def add_initial_data(cur, is_postgres):
    """Add initial data to the database."""
    # Only add initial data if tables are empty
    cur.execute("SELECT COUNT(*) FROM students")
    if cur.fetchone()[0] == 0:
        logger.info("Adding initial data...")
        
        # Add a sample warden
        cur.execute('''
            INSERT INTO wardens (warden_id, name, password_hash, email, phone, hostel_assigned)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''' if is_postgres else '''
            INSERT INTO wardens (warden_id, name, password_hash, email, phone, hostel_assigned)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('WARDEN001', 'Admin Warden', 
              'pbkdf2:sha256:260000$abc123$def456...',  # Replace with hashed password
              'warden@example.com', '9876543210', 'Boys Hostel A'))

        logger.info("Added initial data successfully")

if __name__ == '__main__':
    logger.info("Starting database initialization...")
    init_db()
    logger.info("✅ Database initialization complete!")