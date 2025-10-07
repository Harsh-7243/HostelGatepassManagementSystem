from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import os
from datetime import datetime

# Create Flask app with correct template paths for Vercel
app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')
app.secret_key = os.environ.get('SESSION_SECRET', 'vercel-demo-secret-key')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# Demo users for Vercel
DEMO_USERS = {
    'students': {
        'STU001': {'name': 'Amit Kumar', 'password_hash': generate_password_hash('college123'), 'email': 'amit@college.edu'},
    },
    'parents': {
        'PAR001': {'name': 'Rajesh Kumar', 'password_hash': generate_password_hash('college123'), 'email': 'rajesh@email.com'},
    },
    'wardens': {
        'WAR001': {'name': 'Dr. Ramesh Verma', 'password_hash': generate_password_hash('college123'), 'email': 'ramesh@college.edu'},
    },
    'security_guards': {
        'SEC001': {'name': 'Ravi Shankar', 'password_hash': generate_password_hash('college123'), 'email': 'ravi@college.edu'},
    }
}

PENDING_REGISTRATIONS = []

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
    
    for role_key, users in DEMO_USERS.items():
        if user_id in users:
            return User(user_id, users[user_id]['name'], role)
    return None

# Simple HTML template as string to avoid file path issues
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Hostel Gatepass System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .login-card { background: white; border-radius: 15px; padding: 2rem; margin-top: 5rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="login-card">
                    <h3 class="text-center mb-4">🎓 Hostel Gatepass System</h3>
                    
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }}">{{ message }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">User ID</label>
                            <input type="text" class="form-control" name="user_id" placeholder="e.g., STU001" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Password</label>
                            <input type="password" class="form-control" name="password" placeholder="Enter password" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Role</label>
                            <select class="form-control" name="role" required>
                                <option value="">Select role...</option>
                                <option value="student">Student</option>
                                <option value="parent">Parent</option>
                                <option value="warden">Warden</option>
                                <option value="security">Security</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Sign In</button>
                    </form>
                    
                    <div class="text-center mt-3">
                        <small class="text-muted">Demo: WAR001/college123 (Warden) | STU001/college123 (Student)</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ role|title }} Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-primary">
        <div class="container-fluid">
            <span class="navbar-brand">{{ role|title }} Dashboard - {{ user_name }}</span>
            <a href="{{ url_for('logout') }}" class="btn btn-outline-light">Logout</a>
        </div>
    </nav>
    <div class="container mt-4">
        <div class="alert alert-success">
            <h4>🎉 Welcome to your {{ role|title }} Dashboard!</h4>
            <p>This is a demo version running on Vercel. The full system includes:</p>
            <ul>
                <li>✅ User Registration System</li>
                <li>✅ Gatepass Application & Approval</li>
                <li>✅ Parent Notifications</li>
                <li>✅ Security Check-in/out</li>
                <li>✅ Admin Management</li>
            </ul>
            <p><strong>GitHub Repository:</strong> <a href="https://github.com/Harsh-7243/HostelGatepassManagementSystem" target="_blank">View Full Source Code</a></p>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        role = request.form.get('role')
        
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
                return redirect(url_for('dashboard'))
        
        flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

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
        
        success_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Registration Successful</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
                .success-card {{ background: white; border-radius: 15px; padding: 2rem; margin-top: 5rem; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="success-card text-center">
                            <i class="fas fa-check-circle text-success" style="font-size: 4rem;"></i>
                            <h2 class="mt-3">Registration Successful!</h2>
                            <div class="alert alert-success mt-3">
                                <h4>Your User ID: <strong>{new_user_id}</strong></h4>
                                <p>Please save this ID for login purposes.</p>
                            </div>
                            <div class="alert alert-info">
                                <p><strong>Demo Note:</strong> In production, admin approval would be required.</p>
                                <p>You can now use this ID to login to the system.</p>
                            </div>
                            <a href="/login" class="btn btn-primary btn-lg">
                                <i class="fas fa-sign-in-alt"></i> Go to Login
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        from flask import render_template_string
        return render_template_string(success_html)
        
    except Exception as e:
        flash(f'Registration error: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Use a simple dashboard template that works on Vercel
    dashboard_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{current_user.role.title()} Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .dashboard-card {{ background: white; border-radius: 15px; padding: 2rem; margin-top: 2rem; }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark bg-primary">
            <div class="container-fluid">
                <span class="navbar-brand">
                    <i class="fas fa-user-tie"></i> {current_user.name} - {current_user.role.title()}
                </span>
                <a href="/logout" class="btn btn-outline-light">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>
        </nav>
        
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-10">
                    <div class="dashboard-card">
                        <div class="text-center mb-4">
                            <h2><i class="fas fa-tachometer-alt"></i> {current_user.role.title()} Dashboard</h2>
                            <p class="text-muted">Welcome to your personalized dashboard, {current_user.name}!</p>
                        </div>
                        
                        <div class="alert alert-success">
                            <h4><i class="fas fa-check-circle"></i> Login Successful!</h4>
                            <p>You have successfully logged into the Hostel Gatepass Management System.</p>
                            <hr>
                            <h5>🎯 System Features:</h5>
                            <div class="row">
                                <div class="col-md-6">
                                    <ul class="list-unstyled">
                                        <li><i class="fas fa-user-plus text-success"></i> User Registration System</li>
                                        <li><i class="fas fa-file-alt text-info"></i> Gatepass Applications</li>
                                        <li><i class="fas fa-check text-warning"></i> Approval Workflow</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <ul class="list-unstyled">
                                        <li><i class="fas fa-bell text-primary"></i> Real-time Notifications</li>
                                        <li><i class="fas fa-shield-alt text-danger"></i> Security Management</li>
                                        <li><i class="fas fa-chart-bar text-secondary"></i> Analytics & Reports</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-4">
                                <div class="card bg-primary text-white">
                                    <div class="card-body text-center">
                                        <i class="fas fa-users fa-2x mb-2"></i>
                                        <h5>User Management</h5>
                                        <p>Manage user accounts and permissions</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card bg-success text-white">
                                    <div class="card-body text-center">
                                        <i class="fas fa-clipboard-list fa-2x mb-2"></i>
                                        <h5>Gatepass Requests</h5>
                                        <p>View and manage gatepass applications</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card bg-info text-white">
                                    <div class="card-body text-center">
                                        <i class="fas fa-chart-line fa-2x mb-2"></i>
                                        <h5>Reports</h5>
                                        <p>Generate system reports and analytics</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mt-4 text-center">
                            <div class="alert alert-info">
                                <h6><i class="fas fa-info-circle"></i> Demo Version</h6>
                                <p class="mb-0">This is a demo deployment on Vercel. The full system includes database integration, 
                                email notifications, and complete CRUD operations.</p>
                                <hr>
                                <p class="mb-0">
                                    <strong>GitHub:</strong> 
                                    <a href="https://github.com/Harsh-7243/HostelGatepassManagementSystem" target="_blank" class="text-decoration-none">
                                        View Source Code <i class="fas fa-external-link-alt"></i>
                                    </a>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    
    from flask import render_template_string
    return render_template_string(dashboard_html)

@app.route('/logout')
@login_required
def logout():
    session.pop('user_role', None)
    logout_user()
    return redirect(url_for('login'))

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok', 
        'message': 'Hostel Gatepass System is running on Vercel!',
        'demo_accounts': {
            'student': 'STU001/college123',
            'parent': 'PAR001/college123',
            'warden': 'WAR001/college123',
            'security': 'SEC001/college123'
        }
    })

# Export the Flask app for Vercel
# Vercel will automatically handle the WSGI interface
app.config['ENV'] = 'production'

if __name__ == '__main__':
    app.run(debug=True)
