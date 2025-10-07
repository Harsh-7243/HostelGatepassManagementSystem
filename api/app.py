from flask import Flask, jsonify, render_template_string, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import os
from datetime import datetime

app = Flask(__name__)
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
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE, 
                                role=current_user.role, 
                                user_name=current_user.name)

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
