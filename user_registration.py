"""
User Registration Module for Hostel Gatepass Management System
Handles new user sign-ups and credential management
"""

import sqlite3
import secrets
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

def get_db_connection():
    # Use SQLite for easier development setup - same as app.py
    db_path = os.environ.get('DATABASE_PATH', 'gatepass.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def generate_user_id(user_type):
    """Generate a unique user ID based on user type"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    prefix_map = {
        'student': 'STU',
        'parent': 'PAR',
        'warden': 'WAR',
        'security': 'SEC'
    }
    
    prefix = prefix_map.get(user_type)
    if not prefix:
        raise ValueError(f"Invalid user type: {user_type}")
    
    # Get the highest existing ID for this user type
    table_map = {
        'student': 'students',
        'parent': 'parents',
        'warden': 'wardens',
        'security': 'security_guards'
    }
    
    table = table_map[user_type]
    id_column = 'student_id' if user_type == 'student' else \
                'parent_id' if user_type == 'parent' else \
                'warden_id' if user_type == 'warden' else 'guard_id'
    
    cur.execute(f"SELECT {id_column} FROM {table} ORDER BY {id_column} DESC LIMIT 1")
    result = cur.fetchone()
    
    if result:
        last_id = result[0]
        number = int(last_id.replace(prefix, '')) + 1
    else:
        number = 1
    
    conn.close()
    return f"{prefix}{number:03d}"


def generate_verification_token():
    """Generate a random verification token"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))


def register_new_user(user_type, name, email, phone, password, **kwargs):
    """
    Register a new user (creates a pending registration)
    
    Args:
        user_type: 'student', 'parent', 'warden', or 'security'
        name: Full name of the user
        email: Email address
        phone: Phone number
        password: Plain text password (will be hashed)
        **kwargs: Additional user-type specific fields
        
    Returns:
        dict: Registration details including proposed_user_id and verification_token
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check if email already exists in any table
        for table, email_col in [
            ('students', 'email'),
            ('parents', 'email'),
            ('wardens', 'email'),
            ('security_guards', 'email')
        ]:
            cur.execute(f"SELECT {email_col} FROM {table} WHERE {email_col} = ?", (email,))
            if cur.fetchone():
                return {'success': False, 'error': 'Email already registered'}
        
        # Check if email exists in pending registrations
        cur.execute("SELECT email FROM pending_registrations WHERE email = ? AND status = 'pending'", (email,))
        if cur.fetchone():
            return {'success': False, 'error': 'Registration already pending for this email'}
        
        # Generate user ID and verification token
        proposed_user_id = generate_user_id(user_type)
        verification_token = generate_verification_token()
        password_hash = generate_password_hash(password)
        
        # Prepare base fields
        fields = {
            'user_type': user_type,
            'proposed_user_id': proposed_user_id,
            'name': name,
            'email': email,
            'phone': phone,
            'password_hash': password_hash,
            'verification_token': verification_token
        }
        
        # Add user-type specific fields
        if user_type == 'student':
            fields.update({
                'parent_id': kwargs.get('parent_id'),
                'hostel_block': kwargs.get('hostel_block'),
                'room_number': kwargs.get('room_number'),
                'course': kwargs.get('course'),
                'year_of_study': kwargs.get('year_of_study')
            })
        elif user_type == 'parent':
            fields.update({
                'student_id': kwargs.get('student_id'),
                'relationship': kwargs.get('relationship'),
                'address': kwargs.get('address')
            })
        elif user_type == 'warden':
            fields.update({
                'designation': kwargs.get('designation'),
                'hostel_block': kwargs.get('hostel_block')
            })
        elif user_type == 'security':
            fields.update({
                'shift': kwargs.get('shift'),
                'gate_assigned': kwargs.get('gate_assigned')
            })
        
        # Build dynamic INSERT query
        columns = ', '.join(fields.keys())
        placeholders = ', '.join(['?' for _ in fields])
        values = tuple(fields.values())
        
        cur.execute(f"""
            INSERT INTO pending_registrations ({columns})
            VALUES ({placeholders})
        """, values)
        
        conn.commit()
        registration_id = cur.lastrowid
        
        return {
            'success': True,
            'registration_id': registration_id,
            'proposed_user_id': proposed_user_id,
            'verification_token': verification_token,
            'message': 'Registration submitted successfully. Awaiting admin approval.'
        }
        
    except sqlite3.IntegrityError as e:
        return {'success': False, 'error': f'Database error: {str(e)}'}
    finally:
        conn.close()


def approve_registration(registration_id, reviewed_by):
    """
    Approve a pending registration and create the actual user account
    
    Args:
        registration_id: ID of the pending registration
        reviewed_by: User ID of the admin/warden approving the registration
        
    Returns:
        dict: Success status and message
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get pending registration details
        cur.execute("""
            SELECT * FROM pending_registrations 
            WHERE registration_id = ? AND status = 'pending'
        """, (registration_id,))
        
        registration = cur.fetchone()
        if not registration:
            return {'success': False, 'error': 'Registration not found or already processed'}
        
        # Convert to dict for easier access
        reg_dict = dict(registration)
        user_type = reg_dict['user_type']
        
        # Insert into appropriate user table
        if user_type == 'student':
            cur.execute("""
                INSERT INTO students (student_id, name, password_hash, email, phone, 
                                     hostel_block, room_number, course, year_of_study)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reg_dict['proposed_user_id'], reg_dict['name'], reg_dict['password_hash'],
                reg_dict['email'], reg_dict['phone'], reg_dict['hostel_block'],
                reg_dict['room_number'], reg_dict['course'], reg_dict['year_of_study']
            ))
            
            # Link with parent if parent_id provided
            if reg_dict.get('parent_id'):
                cur.execute("""
                    INSERT INTO student_parent_links (student_id, parent_id)
                    VALUES (?, ?)
                """, (reg_dict['proposed_user_id'], reg_dict['parent_id']))
                
        elif user_type == 'parent':
            cur.execute("""
                INSERT INTO parents (parent_id, name, password_hash, email, phone, 
                                    relationship, address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                reg_dict['proposed_user_id'], reg_dict['name'], reg_dict['password_hash'],
                reg_dict['email'], reg_dict['phone'], reg_dict['relationship'],
                reg_dict['address']
            ))
            
            # Link with student if student_id provided
            if reg_dict.get('student_id'):
                cur.execute("""
                    INSERT INTO student_parent_links (student_id, parent_id)
                    VALUES (?, ?)
                """, (reg_dict['student_id'], reg_dict['proposed_user_id']))
                
        elif user_type == 'warden':
            cur.execute("""
                INSERT INTO wardens (warden_id, name, password_hash, email, phone,
                                    hostel_block, designation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                reg_dict['proposed_user_id'], reg_dict['name'], reg_dict['password_hash'],
                reg_dict['email'], reg_dict['phone'], reg_dict['hostel_block'],
                reg_dict['designation']
            ))
            
        elif user_type == 'security':
            cur.execute("""
                INSERT INTO security_guards (guard_id, name, password_hash, email, phone,
                                            shift, gate_assigned)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                reg_dict['proposed_user_id'], reg_dict['name'], reg_dict['password_hash'],
                reg_dict['email'], reg_dict['phone'], reg_dict['shift'],
                reg_dict['gate_assigned']
            ))
        
        # Update registration status
        cur.execute("""
            UPDATE pending_registrations 
            SET status = 'approved', reviewed_at = ?, reviewed_by = ?
            WHERE registration_id = ?
        """, (datetime.now(), reviewed_by, registration_id))
        
        # Log the activity
        cur.execute("""
            INSERT INTO activity_logs (user_id, user_type, action, description)
            VALUES (?, 'system', 'registration_approved', ?)
        """, (reviewed_by, f"Approved registration for {reg_dict['name']} ({reg_dict['proposed_user_id']})"))
        
        conn.commit()
        
        return {
            'success': True,
            'user_id': reg_dict['proposed_user_id'],
            'message': f"Registration approved. User ID: {reg_dict['proposed_user_id']}"
        }
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return {'success': False, 'error': f'Database error: {str(e)}'}
    finally:
        conn.close()


def reject_registration(registration_id, reviewed_by, reason):
    """
    Reject a pending registration
    
    Args:
        registration_id: ID of the pending registration
        reviewed_by: User ID of the admin/warden rejecting the registration
        reason: Reason for rejection
        
    Returns:
        dict: Success status and message
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE pending_registrations 
            SET status = 'rejected', reviewed_at = ?, reviewed_by = ?, rejection_reason = ?
            WHERE registration_id = ? AND status = 'pending'
        """, (datetime.now(), reviewed_by, reason, registration_id))
        
        if cur.rowcount == 0:
            return {'success': False, 'error': 'Registration not found or already processed'}
        
        conn.commit()
        return {'success': True, 'message': 'Registration rejected'}
        
    except sqlite3.Error as e:
        return {'success': False, 'error': f'Database error: {str(e)}'}
    finally:
        conn.close()


def get_pending_registrations(user_type=None):
    """
    Get all pending registrations, optionally filtered by user type
    
    Args:
        user_type: Optional filter for user type
        
    Returns:
        list: List of pending registrations
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    if user_type:
        cur.execute("""
            SELECT * FROM pending_registrations 
            WHERE status = 'pending' AND user_type = ?
            ORDER BY submitted_at DESC
        """, (user_type,))
    else:
        cur.execute("""
            SELECT * FROM pending_registrations 
            WHERE status = 'pending'
            ORDER BY submitted_at DESC
        """)
    
    registrations = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    return registrations


def verify_parent_student_link(parent_id, student_id):
    """
    Verify if a parent-student link exists
    
    Args:
        parent_id: Parent ID
        student_id: Student ID
        
    Returns:
        bool: True if link exists, False otherwise
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * FROM student_parent_links 
        WHERE parent_id = ? AND student_id = ?
    """, (parent_id, student_id))
    
    result = cur.fetchone() is not None
    conn.close()
    
    return result


if __name__ == '__main__':
    # Example usage
    print("User Registration Module")
    print("=" * 50)
    
    # Example: Register a new student
    result = register_new_user(
        user_type='student',
        name='Amit Sharma',
        email='amit.sharma@student.edu',
        phone='9876543250',
        password='password123',
        parent_id='PAR001',
        hostel_block='Block A',
        room_number='A-405',
        course='Computer Science',
        year_of_study=1
    )
    print("\nStudent Registration:", result)
    
    # Example: Register a new parent
    result = register_new_user(
        user_type='parent',
        name='Ramesh Sharma',
        email='ramesh.sharma@gmail.com',
        phone='9876543260',
        password='password123',
        student_id='STU001',
        relationship='Father',
        address='Pune, Maharashtra'
    )
    print("\nParent Registration:", result)
