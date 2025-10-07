# 🎓 Hostel Gatepass Management System

A modern, comprehensive digital solution for managing student gatepass requests in hostels with **user registration system** and role-based access for students, parents, wardens, and security guards.

## ✨ Features

### 🔐 Multi-Role Authentication & Registration
- **New User Registration**: Self-service registration with admin approval
- **Students**: Apply for gatepasses, track status
- **Parents**: Approve/reject student requests
- **Wardens**: Oversight, management & user approval
- **Security Guards**: Check-in/check-out management

### 🚀 Core Functionality
- **Modern UI/UX**: Beautiful split-screen login with tab navigation
- **User Registration**: Dynamic forms based on role selection
- **Admin Approval**: Pending registrations dashboard for wardens
- **Digital Gatepass System**: Complete application workflow
- **Real-time Status Tracking**: Live updates and notifications
- **Parent Integration**: Email notifications and approval system
- **Security Management**: Check-in/out with real-time status

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Database**
   ```bash
   python db_init.py
   ```

3. **Run Application**
   ```bash
   python app.py
   ```

4. **Access System**
   - Open http://localhost:5000
   - Use **Sign In** tab for existing users
   - Use **Register** tab for new user registration

## 👥 Test Accounts

- **Student**: STU001 / college123
- **Parent**: PAR001 / college123  
- **Warden**: WAR001 / college123
- **Security**: SEC001 / college123

## 🔄 Registration Workflow

1. **New User**: Fill registration form → Get User ID
2. **Admin Review**: Warden approves/rejects in dashboard
3. **Account Creation**: Approved users can login immediately
4. **Role Access**: Automatic redirect to appropriate dashboard

## 🛠️ Technology Stack

- **Backend**: Flask, SQLite
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Authentication**: Flask-Login with session management
- **Security**: Werkzeug password hashing
- **Database**: SQLite with enhanced schema for registration system

## 📁 Project Structure

```
HostelGatepassManagementSystem/
├── app.py                    # Main Flask application
├── db_init.py               # Database setup & sample data
├── user_registration.py     # Registration logic
├── gatepass.db             # SQLite database
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── static/css/style.css   # Custom styles
└── templates/             # HTML templates
    ├── login.html         # Modern login & registration
    ├── student_dashboard.html
    ├── parent_dashboard.html
    ├── warden_dashboard.html
    ├── security_dashboard.html
    ├── pending_registrations.html
    ├── register_success.html
    └── apply_gatepass.html
```

