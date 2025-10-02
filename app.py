from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

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
        cur.execute('SELECT student_id, name FROM students WHERE student_id = %s', (user_id,))
    elif role == 'parent':
        cur.execute('SELECT parent_id, name FROM parents WHERE parent_id = %s', (user_id,))
    elif role == 'warden':
        cur.execute('SELECT warden_id, name FROM wardens WHERE warden_id = %s', (user_id,))
    elif role == 'security':
        cur.execute('SELECT guard_id, name FROM security_guards WHERE guard_id = %s', (user_id,))
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        role = request.form['role']
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if role == 'student':
            cur.execute('SELECT student_id, name, password_hash FROM students WHERE student_id = %s', (user_id,))
        elif role == 'parent':
            cur.execute('SELECT parent_id, name, password_hash FROM parents WHERE parent_id = %s', (user_id,))
        elif role == 'warden':
            cur.execute('SELECT warden_id, name, password_hash FROM wardens WHERE warden_id = %s', (user_id,))
        elif role == 'security':
            cur.execute('SELECT guard_id, name, password_hash FROM security_guards WHERE guard_id = %s', (user_id,))
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

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT request_id, date_time_out, duration_hours, destination, purpose, 
               parent_approval_status, created_at, expiry_timestamp, warden_status, security_guard_status
        FROM gatepass_requests
        WHERE student_id = %s
        ORDER BY created_at DESC
    ''', (current_user.id,))
    
    requests = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('student_dashboard.html', requests=requests)

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
        
        created_at = datetime.now()
        expiry_timestamp = created_at + timedelta(hours=1)
        
        cur.execute('''
            INSERT INTO gatepass_requests 
            (student_id, parent_email, date_time_out, duration_hours, destination, purpose, created_at, expiry_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING request_id
        ''', (current_user.id, parent_email, date_time_out, duration_hours, destination, purpose, created_at, expiry_timestamp))
        
        request_result = cur.fetchone()
        request_id = request_result[0] if request_result else None
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"Notification sent to Parent (Email: {parent_email}) with approval link: /parent/approve/{request_id} and rejection link: /parent/reject/{request_id}")
        
        flash('Gatepass request submitted successfully!')
        return redirect(url_for('student_dashboard'))
    
    return render_template('apply_gatepass.html')

@app.route('/parent/dashboard')
@login_required
def parent_dashboard():
    if current_user.role != 'parent':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT email FROM parents WHERE parent_id = %s', (current_user.id,))
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
        WHERE parent_email = %s 
        AND parent_approval_status = 'Pending'
        AND created_at + INTERVAL '1 hour' < %s
    ''', (parent_email, now))
    
    cur.execute('''
        SELECT r.request_id, s.name, s.student_id, r.date_time_out, r.duration_hours, 
               r.destination, r.purpose, r.parent_approval_status, r.created_at, r.expiry_timestamp
        FROM gatepass_requests r
        JOIN students s ON r.student_id = s.student_id
        WHERE r.parent_email = %s
        ORDER BY r.created_at DESC
    ''', (parent_email,))
    
    requests = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    
    return render_template('parent_dashboard.html', requests=requests)

@app.route('/parent/approve/<int:request_id>')
@login_required
def approve_request(request_id):
    if current_user.role != 'parent':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT email FROM parents WHERE parent_id = %s', (current_user.id,))
    parent_result = cur.fetchone()
    parent_email = parent_result[0] if parent_result else None
    
    cur.execute('''
        UPDATE gatepass_requests
        SET parent_approval_status = 'Approved', parent_approval_timestamp = %s
        WHERE request_id = %s AND parent_email = %s AND parent_approval_status = 'Pending'
    ''', (datetime.now(), request_id, parent_email))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Request approved successfully!')
    return redirect(url_for('parent_dashboard'))

@app.route('/parent/reject/<int:request_id>')
@login_required
def reject_request(request_id):
    if current_user.role != 'parent':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT email FROM parents WHERE parent_id = %s', (current_user.id,))
    parent_result = cur.fetchone()
    parent_email = parent_result[0] if parent_result else None
    
    cur.execute('''
        UPDATE gatepass_requests
        SET parent_approval_status = 'Rejected', parent_approval_timestamp = %s
        WHERE request_id = %s AND parent_email = %s AND parent_approval_status = 'Pending'
    ''', (datetime.now(), request_id, parent_email))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Request rejected successfully!')
    return redirect(url_for('parent_dashboard'))

@app.route('/warden/dashboard')
@login_required
def warden_dashboard():
    if current_user.role != 'warden':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT r.request_id, s.name, s.student_id, r.date_time_out, r.duration_hours, 
               r.destination, r.purpose, r.parent_approval_status, r.warden_status, r.security_guard_status
        FROM gatepass_requests r
        JOIN students s ON r.student_id = s.student_id
        WHERE r.parent_approval_status = 'Approved'
        ORDER BY r.date_time_out DESC
    ''', ())
    
    requests = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('warden_dashboard.html', requests=requests)

@app.route('/warden/close/<int:request_id>')
@login_required
def close_request(request_id):
    if current_user.role != 'warden':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        UPDATE gatepass_requests
        SET warden_status = 'Closed'
        WHERE request_id = %s
    ''', (request_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Request closed successfully!')
    return redirect(url_for('warden_dashboard'))

@app.route('/security/dashboard')
@login_required
def security_dashboard():
    if current_user.role != 'security':
        flash('Access denied')
        return redirect(url_for('index'))
    
    return render_template('security_dashboard.html')

@app.route('/security/search', methods=['POST'])
@login_required
def security_search():
    if current_user.role != 'security':
        flash('Access denied')
        return redirect(url_for('index'))
    
    student_id = request.form['student_id']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT name FROM students WHERE student_id = %s', (student_id,))
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
        WHERE student_id = %s AND parent_approval_status = 'Approved'
        ORDER BY date_time_out DESC
    ''', (student_id,))
    
    requests = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('security_dashboard.html', student_id=student_id, student_name=student[0], requests=requests)

@app.route('/security/checkout/<int:request_id>')
@login_required
def checkout_student(request_id):
    if current_user.role != 'security':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        UPDATE gatepass_requests
        SET security_guard_status = 'Out'
        WHERE request_id = %s
    ''', (request_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Student checked out successfully!')
    return redirect(url_for('security_dashboard'))

@app.route('/security/checkin/<int:request_id>')
@login_required
def checkin_student(request_id):
    if current_user.role != 'security':
        flash('Access denied')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        UPDATE gatepass_requests
        SET security_guard_status = 'In'
        WHERE request_id = %s
    ''', (request_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Student checked in successfully!')
    return redirect(url_for('security_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
