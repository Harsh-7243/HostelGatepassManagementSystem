# Add this at the top with other imports
import logging
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Update your login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            password = request.form.get('password')
            user_type = request.form.get('user_type')
            
            logger.info(f"Login attempt - User ID: {user_id}, Type: {user_type}")
            
            if not user_id or not password:
                flash('Please enter both user ID and password', 'error')
                return redirect(url_for('login'))
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Check user type and table
            if user_type == 'student':
                cur.execute('SELECT * FROM students WHERE student_id = %s', (user_id,))
            elif user_type == 'warden':
                cur.execute('SELECT * FROM wardens WHERE warden_id = %s', (user_id,))
            elif user_type == 'parent':
                cur.execute('SELECT * FROM parents WHERE parent_id = %s', (user_id,))
            elif user_type == 'security':
                cur.execute('SELECT * FROM security_guards WHERE guard_id = %s', (user_id,))
            
            user = cur.fetchone()
            conn.close()
            
            if user is None:
                logger.warning(f"User not found: {user_id}")
                flash('Invalid user ID or password', 'error')
                return redirect(url_for('login'))
            
            # Verify password
            if not check_password_hash(user['password_hash'], password):
                logger.warning(f"Invalid password for user: {user_id}")
                flash('Invalid user ID or password', 'error')
                return redirect(url_for('login'))
            
            # Login successful
            session['user_id'] = user_id
            session['user_type'] = user_type
            logger.info(f"User {user_id} logged in successfully")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)
            flash('An error occurred during login. Please try again.', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os

# Load environment variables for Azure deployment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not available, continue without it

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore

def get_db_connection():
    # Use SQLite for easier development setup
    db_path = os.environ.get('DATABASE_PATH', 'gatepass.db')
    conn = sqlite3.connect(db_path)
    # Don't use row_factory here to maintain compatibility with existing index-based access
    return conn

class User(UserMixin):
    def __init__(self, user_id, name, role):
        self.id = user_id
        self.name = name
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    role = session.get('user_role')
    if not role:
        return None
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if role == 'student':
        cur.execute('SELECT student_id, name FROM students WHERE student_id = ?', (user_id,))
    elif role == 'parent':
        cur.execute('SELECT parent_id, name FROM parents WHERE parent_id = ?', (user_id,))
    elif role == 'warden':
        cur.execute('SELECT warden_id, name FROM wardens WHERE warden_id = ?', (user_id,))
    elif role == 'security':
        cur.execute('SELECT guard_id, name FROM security_guards WHERE guard_id = ?', (user_id,))
    else:
        return None
    
    user_data = cur.fetchone()
    cur.close()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], role)
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif current_user.role == 'parent':
            return redirect(url_for('parent_dashboard'))
        elif current_user.role == 'warden':
            return redirect(url_for('warden_dashboard'))
        elif current_user.role == 'security':
            return redirect(url_for('security_dashboard'))
    return redirect(url_for('login'))

@app.route('/health')
def health_check():
    """Health check endpoint for Azure deployment verification"""
    return "Hostel Gatepass System deployed on Azure ✅"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        role = request.form['role']
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if role == 'student':
            cur.execute('SELECT student_id, name, password_hash FROM students WHERE student_id = ?', (user_id,))
        elif role == 'parent':
            cur.execute('SELECT parent_id, name, password_hash FROM parents WHERE parent_id = ?', (user_id,))
        elif role == 'warden':
            cur.execute('SELECT warden_id, name, password_hash FROM wardens WHERE warden_id = ?', (user_id,))
        elif role == 'security':
            cur.execute('SELECT guard_id, name, password_hash FROM security_guards WHERE guard_id = ?', (user_id,))
        else:
            flash('Invalid role selected')
            return redirect(url_for('login'))
        
        user_data = cur.fetchone()
        cur.close()
        conn.close()
        
        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], role)
            session['user_role'] = role
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_role', None)
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    # Import registration function
    from user_registration import register_new_user
    
    # Get common fields
    user_type = request.form.get('user_type')
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    
    print(f"Registration attempt: {user_type}, {name}, {email}")  # Debug log
    
    # Prepare kwargs for role-specific fields
    kwargs = {}
    
    if user_type == 'student':
        kwargs['parent_id'] = request.form.get('parent_id') or None
        kwargs['hostel_block'] = request.form.get('hostel_block')
        kwargs['room_number'] = request.form.get('room_number')
        kwargs['course'] = request.form.get('course')
        kwargs['year_of_study'] = request.form.get('year_of_study') or None
    
    elif user_type == 'parent':
        kwargs['student_id'] = request.form.get('student_id') or None
        kwargs['relationship'] = request.form.get('relationship')
        kwargs['address'] = request.form.get('address')
    
    elif user_type == 'warden':
        kwargs['designation'] = request.form.get('designation')
        kwargs['hostel_block'] = request.form.get('warden_hostel_block')
    
    elif user_type == 'security':
        kwargs['shift'] = request.form.get('shift')
        kwargs['gate_assigned'] = request.form.get('gate_assigned')
    
    # Register the user
    try:
        result = register_new_user(user_type, name, email, phone, password, **kwargs)
        
        if result['success']:
            flash(f"Registration successful! Your User ID is: {result['proposed_user_id']}", 'success')
            return render_template('register_success.html', 
                                 user_id=result['proposed_user_id'])
        else:
            flash(result['error'], 'danger')
            return redirect(url_for('login'))
    except Exception as e:
        flash(f'Registration error: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/student/dashboard')
@app.route('/student/dashboard/<filter_type>')
@login_required
def student_dashboard(filter_type='all'):
    if current_user.role != 'student':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Build query based on filter type
    base_query = '''
        SELECT request_id, date_time_out, duration_hours, destination, purpose, 
               parent_approval_status, created_at, expiry_timestamp, warden_status, security_guard_status
        FROM gatepass_requests
        WHERE student_id = ?
    '''
    
    if filter_type == 'pending':
        base_query += " AND parent_approval_status = 'Pending'"
    elif filter_type == 'history':
        base_query += " AND parent_approval_status IN ('Approved', 'Rejected', 'Expired')"
    # 'all' shows everything (no additional filter)
    
    base_query += " ORDER BY created_at DESC"
    
    cur.execute(base_query, (current_user.id,))
    raw_requests = cur.fetchall()
    
    # Format the requests to handle datetime properly
    requests = []
    for req in raw_requests:
        formatted_req = list(req)
        # Format the date_time_out (index 1) if it exists
        if req[1]:
            try:
                if isinstance(req[1], str):
                    dt = datetime.fromisoformat(req[1].replace('Z', '+00:00'))
                else:
                    dt = req[1]
                formatted_req[1] = dt.strftime('%d %b, %I:%M %p')
            except:
                formatted_req[1] = str(req[1])
        requests.append(tuple(formatted_req))
    
    # Get counts for each filter
    cur.execute("SELECT COUNT(*) FROM gatepass_requests WHERE student_id = ?", (current_user.id,))
    all_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM gatepass_requests WHERE student_id = ? AND parent_approval_status = 'Pending'", (current_user.id,))
    pending_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM gatepass_requests WHERE student_id = ? AND parent_approval_status IN ('Approved', 'Rejected', 'Expired')", (current_user.id,))
    history_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return render_template('student_dashboard.html', 
                         requests=requests, 
                         current_filter=filter_type,
                         counts={
                             'all': all_count,
                             'pending': pending_count,
                             'history': history_count
                         })

@app.route('/student/apply', methods=['GET', 'POST'])
@login_required
def apply_gatepass():
    if current_user.role != 'student':
        flash('Access denied')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        date_time_out = request.form['date_time_out']
        duration_hours = int(request.form['duration_hours'])
        destination = request.form['destination']
        purpose = request.form['purpose']
        parent_email = request.form['parent_email']
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Validate that the parent email exists in the parents table
        cur.execute('SELECT parent_id, name FROM parents WHERE email = ?', (parent_email,))
        parent = cur.fetchone()
        
        if not parent:
            flash('Error: Parent email not found in the system. Please contact administration to register the parent.')
            cur.close()
            conn.close()
            return render_template('apply_gatepass.html')
        
        created_at = datetime.now()
        expiry_timestamp = created_at + timedelta(hours=1)
        
        cur.execute('''
            INSERT INTO gatepass_requests 
            (student_id, parent_email, date_time_out, duration_hours, destination, purpose, created_at, expiry_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_user.id, parent_email, date_time_out, duration_hours, destination, purpose, created_at, expiry_timestamp))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash(f'Gatepass request submitted successfully! Notification sent to {parent[1]} ({parent_email})')
        return redirect(url_for('student_dashboard'))
    
    # Get the parent email for the logged-in student
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get parent info for current student
    cur.execute('''
        SELECT p.email, p.name 
        FROM parents p 
        JOIN student_parent_links spl ON p.parent_id = spl.parent_id 
        WHERE spl.student_id = ?
    ''', (current_user.id,))
    
    student_parent = cur.fetchone()
    parent_email = student_parent[0] if student_parent else ''
    parent_name = student_parent[1] if student_parent else ''
    
    cur.close()
    conn.close()
    
    return render_template('apply_gatepass.html', 
                         parent_email=parent_email, 
                         parent_name=parent_name)

@app.route('/parent/dashboard')
@app.route('/parent/dashboard/<filter_type>')
@login_required
def parent_dashboard(filter_type='all'):
    if current_user.role != 'parent':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT email FROM parents WHERE parent_id = ?', (current_user.id,))
    parent_result = cur.fetchone()
    if not parent_result:
        flash('Parent email not found')
        cur.close()
        conn.close()
        return redirect(url_for('login'))
    
    parent_email = parent_result[0]
    now = datetime.now()
    
    cur.execute('''
        UPDATE gatepass_requests
        SET parent_approval_status = 'Expired'
        WHERE parent_email = ? 
        AND parent_approval_status = 'Pending'
        AND datetime(created_at, '+1 hour') < ?
    ''', (parent_email, now))
    
    # Build query based on filter type
    base_query = '''
        SELECT r.request_id, s.name, s.student_id, r.date_time_out, r.duration_hours, 
               r.destination, r.purpose, r.parent_approval_status, r.created_at, r.expiry_timestamp
        FROM gatepass_requests r
        JOIN students s ON r.student_id = s.student_id
        WHERE r.parent_email = ?
    '''
    
    if filter_type == 'pending':
        base_query += " AND r.parent_approval_status = 'Pending'"
    elif filter_type == 'history':
        base_query += " AND r.parent_approval_status IN ('Approved', 'Rejected', 'Expired')"
    # 'all' shows everything (no additional filter)
    
    base_query += " ORDER BY r.created_at DESC"
    
    cur.execute(base_query, (parent_email,))
    raw_requests = cur.fetchall()
    
    # Format the requests to handle datetime properly
    requests = []
    for req in raw_requests:
        formatted_req = list(req)
        # Format the date_time_out (index 3) if it exists
        if req[3]:
            try:
                if isinstance(req[3], str):
                    dt = datetime.fromisoformat(req[3].replace('Z', '+00:00'))
                else:
                    dt = req[3]
                formatted_req[3] = dt.strftime('%d %b, %I:%M %p')
            except:
                formatted_req[3] = str(req[3])
        requests.append(tuple(formatted_req))
    
    # Get counts for each filter
    cur.execute("SELECT COUNT(*) FROM gatepass_requests WHERE parent_email = ?", (parent_email,))
    all_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM gatepass_requests WHERE parent_email = ? AND parent_approval_status = 'Pending'", (parent_email,))
    pending_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM gatepass_requests WHERE parent_email = ? AND parent_approval_status IN ('Approved', 'Rejected', 'Expired')", (parent_email,))
    history_count = cur.fetchone()[0]
    
    conn.commit()
    cur.close()
    conn.close()
    
    return render_template('parent_dashboard.html', 
                         requests=requests, 
                         current_filter=filter_type,
                         counts={
                             'all': all_count,
                             'pending': pending_count,
                             'history': history_count
                         })

@app.route('/parent/approve/<int:request_id>')
@app.route('/parent/approve/<int:request_id>/<filter_type>')
@login_required
def approve_request(request_id, filter_type='all'):
    if current_user.role != 'parent':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT email FROM parents WHERE parent_id = ?', (current_user.id,))
    parent_result = cur.fetchone()
    parent_email = parent_result[0] if parent_result else None
    
    cur.execute('''
        UPDATE gatepass_requests
        SET parent_approval_status = 'Approved', parent_approval_timestamp = ?
        WHERE request_id = ? AND parent_email = ? AND parent_approval_status = 'Pending'
    ''', (datetime.now(), request_id, parent_email))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Request approved successfully!')
    return redirect(url_for('parent_dashboard', filter_type=filter_type))

@app.route('/parent/reject/<int:request_id>')
@app.route('/parent/reject/<int:request_id>/<filter_type>')
@login_required
def reject_request(request_id, filter_type='all'):
    if current_user.role != 'parent':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT email FROM parents WHERE parent_id = ?', (current_user.id,))
    parent_result = cur.fetchone()
    parent_email = parent_result[0] if parent_result else None
    
    cur.execute('''
        UPDATE gatepass_requests
        SET parent_approval_status = 'Rejected', parent_approval_timestamp = ?
        WHERE request_id = ? AND parent_email = ? AND parent_approval_status = 'Pending'
    ''', (datetime.now(), request_id, parent_email))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Request rejected successfully!')
    return redirect(url_for('parent_dashboard', filter_type=filter_type))

@app.route('/warden/dashboard')
@app.route('/warden/dashboard/<filter_type>')
@login_required
def warden_dashboard(filter_type='all'):
    if current_user.role != 'warden':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Build query based on filter type
    base_query = '''
        SELECT r.request_id, s.name, s.student_id, r.date_time_out, r.duration_hours, 
               r.destination, r.purpose, r.parent_approval_status, r.warden_status, r.security_guard_status
        FROM gatepass_requests r
        JOIN students s ON r.student_id = s.student_id
        WHERE r.parent_approval_status = 'Approved'
    '''
    
    if filter_type == 'pending':
        base_query += " AND r.warden_status = 'Open'"
    elif filter_type == 'history':
        base_query += " AND r.warden_status = 'Closed'"
    # 'all' shows everything (no additional filter for approved requests)
    
    base_query += " ORDER BY r.date_time_out DESC"
    
    cur.execute(base_query, ())
    raw_requests = cur.fetchall()
    
    # Format the requests to handle datetime properly
    requests = []
    for req in raw_requests:
        formatted_req = list(req)
        # Format the date_time_out (index 3) if it exists
        if req[3]:
            try:
                if isinstance(req[3], str):
                    dt = datetime.fromisoformat(req[3].replace('Z', '+00:00'))
                else:
                    dt = req[3]
                formatted_req[3] = dt.strftime('%d %b, %I:%M %p')
            except:
                formatted_req[3] = str(req[3])
        requests.append(tuple(formatted_req))
    
    # Get counts for each filter
    cur.execute("SELECT COUNT(*) FROM gatepass_requests WHERE parent_approval_status = 'Approved'", ())
    all_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM gatepass_requests WHERE parent_approval_status = 'Approved' AND warden_status = 'Open'", ())
    pending_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM gatepass_requests WHERE parent_approval_status = 'Approved' AND warden_status = 'Closed'", ())
    history_count = cur.fetchone()[0]
    
    # Get pending registrations count
    cur.execute("SELECT COUNT(*) FROM pending_registrations WHERE status = 'pending'", ())
    pending_reg_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return render_template('warden_dashboard.html', 
                         requests=requests, 
                         current_filter=filter_type,
                         counts={
                             'all': all_count,
                             'pending': pending_count,
                             'history': history_count
                         },
                         pending_count=pending_reg_count)

@app.route('/warden/close/<int:request_id>')
@app.route('/warden/close/<int:request_id>/<filter_type>')
@login_required
def close_request(request_id, filter_type='all'):
    if current_user.role != 'warden':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        UPDATE gatepass_requests
        SET warden_status = 'Closed'
        WHERE request_id = ?
    ''', (request_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Request closed successfully!')
    return redirect(url_for('warden_dashboard', filter_type=filter_type))

@app.route('/warden/pending-registrations')
@login_required
def pending_registrations():
    if current_user.role != 'warden':
        flash('Access denied')
        return redirect(url_for('index'))
    
    from user_registration import get_pending_registrations
    registrations = get_pending_registrations()
    
    return render_template('pending_registrations.html', registrations=registrations)

@app.route('/warden/approve-registration/<int:registration_id>', methods=['POST'])
@login_required
def approve_registration(registration_id):
    if current_user.role != 'warden':
        flash('Access denied')
        return redirect(url_for('index'))
    
    from user_registration import approve_registration as approve_reg
    result = approve_reg(registration_id, current_user.id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'danger')
    
    return redirect(url_for('pending_registrations'))

@app.route('/warden/reject-registration/<int:registration_id>', methods=['POST'])
@login_required
def reject_registration(registration_id):
    if current_user.role != 'warden':
        flash('Access denied')
        return redirect(url_for('index'))
    
    from user_registration import reject_registration as reject_reg
    reason = request.form.get('reason', 'No reason provided')
    result = reject_reg(registration_id, current_user.id, reason)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'danger')
    
    return redirect(url_for('pending_registrations'))

@app.route('/security/dashboard')
@app.route('/security/dashboard/<filter_type>')
@login_required
def security_dashboard(filter_type='all'):
    if current_user.role != 'security':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Build query based on filter type
    base_query = '''
        SELECT r.request_id, s.name, s.student_id, r.date_time_out, r.duration_hours, 
               r.destination, r.purpose, r.parent_approval_status, r.warden_status, r.security_guard_status
        FROM gatepass_requests r
        JOIN students s ON r.student_id = s.student_id
        WHERE r.parent_approval_status = 'Approved'
    '''
    
    if filter_type == 'checkout':
        base_query += " AND r.security_guard_status = 'Pending'"
    elif filter_type == 'checkin':
        base_query += " AND r.security_guard_status = 'Out'"
    elif filter_type == 'completed':
        base_query += " AND r.security_guard_status = 'In'"
    # 'all' shows everything (no additional filter)
    
    base_query += " ORDER BY r.date_time_out DESC"
    
    cur.execute(base_query, ())
    raw_requests = cur.fetchall()
    
    # Format the requests to handle datetime properly
    requests = []
    for req in raw_requests:
        formatted_req = list(req)
        # Format the date_time_out (index 3) if it exists
        if req[3]:
            try:
                if isinstance(req[3], str):
                    dt = datetime.fromisoformat(req[3].replace('Z', '+00:00'))
                else:
                    dt = req[3]
                formatted_req[3] = dt.strftime('%d %b, %I:%M %p')
            except:
                formatted_req[3] = str(req[3])
        requests.append(tuple(formatted_req))
    
    # Get counts for each filter
    cur.execute("SELECT COUNT(*) FROM gatepass_requests r WHERE r.parent_approval_status = 'Approved'", ())
    all_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM gatepass_requests r WHERE r.parent_approval_status = 'Approved' AND r.security_guard_status = 'Pending'", ())
    checkout_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM gatepass_requests r WHERE r.parent_approval_status = 'Approved' AND r.security_guard_status = 'Out'", ())
    checkin_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM gatepass_requests r WHERE r.parent_approval_status = 'Approved' AND r.security_guard_status = 'In'", ())
    completed_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return render_template('security_dashboard.html', 
                         requests=requests, 
                         current_filter=filter_type,
                         counts={
                             'all': all_count,
                             'checkout': checkout_count,
                             'checkin': checkin_count,
                             'completed': completed_count
                         })

@app.route('/security/search', methods=['POST'])
@login_required
def security_search():
    if current_user.role != 'security':
        flash('Access denied')
        return redirect(url_for('index'))
    
    student_id = request.form['student_id']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT name FROM students WHERE student_id = ?', (student_id,))
    student = cur.fetchone()
    
    if not student:
        flash('Student not found')
        cur.close()
        conn.close()
        return redirect(url_for('security_dashboard'))
    
    cur.execute('''
        SELECT request_id, date_time_out, duration_hours, destination, purpose, 
               parent_approval_status, warden_status, security_guard_status
        FROM gatepass_requests
        WHERE student_id = ? AND parent_approval_status = 'Approved'
        ORDER BY date_time_out DESC
    ''', (student_id,))
    
    raw_requests = cur.fetchall()
    
    # Format the requests to handle datetime properly
    requests = []
    for req in raw_requests:
        formatted_req = list(req)
        # Format the date_time_out (index 1) if it exists
        if req[1]:
            try:
                if isinstance(req[1], str):
                    dt = datetime.fromisoformat(req[1].replace('Z', '+00:00'))
                else:
                    dt = req[1]
                formatted_req[1] = dt.strftime('%d %b, %I:%M %p')
            except:
                formatted_req[1] = str(req[1])
        requests.append(tuple(formatted_req))
    
    cur.close()
    conn.close()
    
    return render_template('security_dashboard.html', student_id=student_id, student_name=student[0], requests=requests)

@app.route('/security/checkout/<int:request_id>')
@app.route('/security/checkout/<int:request_id>/<filter_type>')
@login_required
def checkout_student(request_id, filter_type='all'):
    if current_user.role != 'security':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        UPDATE gatepass_requests
        SET security_guard_status = 'Out'
        WHERE request_id = ?
    ''', (request_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Student checked out successfully!')
    return redirect(url_for('security_dashboard', filter_type=filter_type))

@app.route('/security/checkin/<int:request_id>')
@app.route('/security/checkin/<int:request_id>/<filter_type>')
@login_required
def checkin_student(request_id, filter_type='all'):
    if current_user.role != 'security':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        UPDATE gatepass_requests
        SET security_guard_status = 'In'
        WHERE request_id = ?
    ''', (request_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Student checked in successfully!')
    return redirect(url_for('security_dashboard', filter_type=filter_type))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
