# Hostel Gatepass Management System

A modern digital gateway management system for college hostels, built with Flask. It supports role-based dashboards for Students, Parents, Wardens, and Security Guards.

## Features

- Student gatepass application and tracking
- Parent approval workflow
- Warden oversight and closure
- Security guard check-in/check-out management
- Responsive UI with Bootstrap and custom styles
- SQLite database for easy setup

## Getting Started

### 1. Install dependencies

```sh
pip install -r requirements.txt
```

### 2. Initialize the database

```sh
python db_init.py
```

### 3. Run the application

```sh
python app.py
```

The app will be available at [http://localhost:5000](http://localhost:5000).

## Default Login Credentials

Use these credentials to log in for each role:

| Role      | User ID   | Password     | Name              |
|-----------|-----------|--------------|-------------------|
| Student   | STU001    | college123   | Arjun Kumar       |
| Student   | STU002    | college123   | Priya Sharma      |
| Student   | STU003    | college123   | Rohit Patel       |
| Student   | STU004    | college123   | Sneha Gupta       |
| Student   | STU005    | college123   | Vikram Singh      |
| Parent    | PAR001    | college123   | Rajesh Kumar      |
| Parent    | PAR002    | college123   | Sunita Sharma     |
| Parent    | PAR003    | college123   | Mahesh Patel      |
| Parent    | PAR004    | college123   | Kavita Gupta      |
| Parent    | PAR005    | college123   | Suresh Singh      |
| Warden    | WAR001    | college123   | Dr. Ramesh Verma  |
| Warden    | WAR002    | college123   | Prof. Meera Joshi |
| Security  | SEC001    | college123   | Ravi Shankar      |
| Security  | SEC002    | college123   | Mohan Lal         |
| Security  | SEC003    | college123   | Deepak Kumar      |

## Folder Structure

- `app.py` - Main Flask application
- `db_init.py` - Database initialization script
- `static/css/style.css` - Custom styles
- `templates/` - HTML templates for all dashboards and forms

