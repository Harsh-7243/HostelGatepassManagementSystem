from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import os
from datetime import datetime

# Create Flask app with correct paths for Vercel
app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'vercel-demo-secret-key')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory database for Vercel demo (since SQLite doesn't work on serverless)
# In production, you'd use PostgreSQL, MySQL, or MongoDB
DEMO_USERS = {
    'students': {
        'STU001': {'name': 'Amit Kumar', 'password_hash': generate_password_hash('college123'), 'email': 'amit@college.edu'},
        'STU002': {'name': 'Priya Sharma', 'password_hash': generate_password_hash('college123'), 'email': 'priya@college.edu'},
    },
    'parents': {
        'PAR001': {'name': 'Rajesh Kumar', 'password_hash': generate_password_hash('college123'), 'email': 'rajesh@email.com'},
        'PAR002': {'name': 'Sunita Sharma', 'password_hash': generate_password_hash('college123'), 'email': 'sunita@email.com'},
    },
    'wardens': {
        'WAR001': {'name': 'Dr. Ramesh Verma', 'password_hash': generate_password_hash('college123'), 'email': 'ramesh@college.edu'},
    },
    'security_guards': {
        'SEC001': {'name': 'Ravi Shankar', 'password_hash': generate_password_hash('college123'), 'email': 'ravi@college.edu'},
    }
}

# In-memory storage for demo
PENDING_REGISTRATIONS = []
GATEPASS_REQUESTS = []

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
    
    # Find user in demo data
    for role_key, users in DEMO_USERS.items():
        if user_id in users:
            return User(user_id, users[user_id]['name'], role)
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
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        role = request.form.get('role')
        
        print(f"Login attempt: {user_id}, {role}")  # Debug log
        
        # Map role to database table
        role_map = {
            'student': 'students',
            'parent': 'parents', 
            'warden': 'wardens',
            'security': 'security_guards'
        }
        
        table = role_map.get(role)
        if table and user_id in DEMO_USERS[table]:
            user_data = DEMO_USERS[table][user_id]
            if check_password_hash(user_data['password_hash'], password):
                user = User(user_id, user_data['name'], role)
                session['user_role'] = role
                login_user(user)
                return redirect(url_for('index'))
        
        flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_role', None)
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    try:
        # Get form data
        user_type = request.form.get('user_type')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Generate demo user ID
        prefix_map = {'student': 'STU', 'parent': 'PAR', 'warden': 'WAR', 'security': 'SEC'}
        prefix = prefix_map.get(user_type, 'USR')
        
        # Find next available ID
        existing_ids = []
        for users in DEMO_USERS.values():
            existing_ids.extend([uid for uid in users.keys() if uid.startswith(prefix)])
        
        next_num = len([uid for uid in existing_ids if uid.startswith(prefix)]) + 1
        new_user_id = f"{prefix}{next_num:03d}"
        
        # Add to pending registrations
        registration = {
            'registration_id': len(PENDING_REGISTRATIONS) + 1,
            'user_type': user_type,
            'proposed_user_id': new_user_id,
            'name': name,
            'email': email,
            'phone': phone,
            'password_hash': generate_password_hash(password),
            'status': 'pending',
            'submitted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add role-specific fields
        if user_type == 'student':
            registration.update({
                'parent_id': request.form.get('parent_id'),
                'hostel_block': request.form.get('hostel_block'),
                'room_number': request.form.get('room_number'),
                'course': request.form.get('course'),
                'year_of_study': request.form.get('year_of_study')
            })
        
        PENDING_REGISTRATIONS.append(registration)
        
        flash(f"Registration successful! Your User ID is: {new_user_id}. Awaiting admin approval.", 'success')
        return render_template('register_success.html', user_id=new_user_id)
        
    except Exception as e:
        flash(f'Registration error: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Demo data for student dashboard
    demo_requests = [
        (1, 'Home Visit', '2024-01-15 10:00', 48, 'Mumbai', 'Family Function', 'Approved', 'Approved', 'Pending'),
        (2, 'Medical', '2024-01-20 14:00', 4, 'City Hospital', 'Health Checkup', 'Approved', 'Open', 'Pending')
    ]
    
    return render_template('student_dashboard.html', 
                         requests=demo_requests,
                         current_filter='all',
                         counts={'all': 2, 'pending': 1, 'approved': 1})

@app.route('/parent/dashboard')
@login_required  
def parent_dashboard():
    if current_user.role != 'parent':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Demo data
    demo_requests = []
    return render_template('parent_dashboard.html',
                         requests=demo_requests,
                         current_filter='all', 
                         counts={'all': 0, 'pending': 0, 'approved': 0})

@app.route('/warden/dashboard')
@login_required
def warden_dashboard():
    if current_user.role != 'warden':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Demo data
    demo_requests = []
    pending_count = len(PENDING_REGISTRATIONS)
    
    return render_template('warden_dashboard.html',
                         requests=demo_requests,
                         current_filter='all',
                         counts={'all': 0, 'pending': 0, 'history': 0},
                         pending_count=pending_count)

@app.route('/warden/pending-registrations')
@login_required
def pending_registrations():
    if current_user.role != 'warden':
        flash('Access denied')
        return redirect(url_for('index'))
    
    return render_template('pending_registrations.html', registrations=PENDING_REGISTRATIONS)

@app.route('/warden/approve-registration/<int:registration_id>', methods=['POST'])
@login_required
def approve_registration(registration_id):
    if current_user.role != 'warden':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Find and approve registration
    for reg in PENDING_REGISTRATIONS:
        if reg['registration_id'] == registration_id:
            # Add to demo users
            role_map = {
                'student': 'students',
                'parent': 'parents',
                'warden': 'wardens', 
                'security': 'security_guards'
            }
            
            table = role_map.get(reg['user_type'])
            if table:
                DEMO_USERS[table][reg['proposed_user_id']] = {
                    'name': reg['name'],
                    'password_hash': reg['password_hash'],
                    'email': reg['email']
                }
                
                reg['status'] = 'approved'
                flash(f"Registration approved! User {reg['proposed_user_id']} can now login.", 'success')
                break
    
    return redirect(url_for('pending_registrations'))

@app.route('/security/dashboard')
@login_required
def security_dashboard():
    if current_user.role != 'security':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Demo data
    demo_requests = []
    return render_template('security_dashboard.html',
                         requests=demo_requests,
                         current_filter='all',
                         counts={'all': 0, 'checkout': 0, 'checkin': 0, 'completed': 0})

# Health check for Vercel
@app.route('/api/health')
def health():
    return {'status': 'ok', 'message': 'Hostel Gatepass System is running on Vercel!'}

# Vercel serverless handler
def handler(event, context):
    from werkzeug.serving import make_server
    from werkzeug.wrappers import Request, Response
    import io
    
    # Create a WSGI environ from the Vercel event
    environ = {
        'REQUEST_METHOD': event.get('httpMethod', 'GET'),
        'PATH_INFO': event.get('path', '/'),
        'QUERY_STRING': event.get('queryStringParameters') or '',
        'CONTENT_TYPE': event.get('headers', {}).get('content-type', ''),
        'CONTENT_LENGTH': str(len(event.get('body', ''))),
        'wsgi.input': io.BytesIO((event.get('body') or '').encode()),
        'wsgi.errors': io.StringIO(),
        'wsgi.version': (1, 0),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
        'wsgi.url_scheme': 'https',
        'SERVER_NAME': event.get('headers', {}).get('host', 'localhost'),
        'SERVER_PORT': '443',
        'HTTP_HOST': event.get('headers', {}).get('host', 'localhost'),
    }
    
    # Add all headers to environ
    for key, value in event.get('headers', {}).items():
        key = 'HTTP_' + key.upper().replace('-', '_')
        environ[key] = value
    
    response_data = []
    
    def start_response(status, headers, exc_info=None):
        response_data.extend([status, headers])
    
    # Call the Flask app
    try:
        app_response = app(environ, start_response)
        body = b''.join(app_response)
        
        return {
            'statusCode': int(response_data[0].split()[0]) if response_data else 200,
            'headers': dict(response_data[1]) if len(response_data) > 1 else {},
            'body': body.decode('utf-8'),
            'isBase64Encoded': False
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': f'{{"error": "Internal server error: {str(e)}"}}',
            'isBase64Encoded': False
        }

# For local development
if __name__ == '__main__':
    app.run(debug=True)
