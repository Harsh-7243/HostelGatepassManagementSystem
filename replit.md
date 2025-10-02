# College Gatepass System

## Overview

A full-stack web application for managing college gatepass requests. The system allows students to request gatepasses, parents to approve/reject them, wardens to oversee all requests, and security guards to manage student check-in/check-out. The application implements a multi-role authentication system with distinct dashboards for each user type and includes automatic expiry logic for pending requests.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Choice**: Server-side rendering with Jinja2 templates and Bootstrap 5

The application uses a traditional multi-page architecture where the server renders complete HTML pages. Bootstrap provides responsive UI components without requiring a separate frontend build process.

**Rationale**: 
- Simpler deployment and maintenance
- No need for API contracts between frontend and backend
- Faster initial development for CRUD operations
- Bootstrap provides professional UI out of the box

**Key Components**:
- Role-specific dashboard templates (student, parent, warden, security)
- Login page with role selection
- Form-based interactions for gatepass applications and approvals

### Backend Architecture

**Framework**: Python Flask with Flask-Login for session management

**Design Pattern**: Model-View-Controller (MVC) where:
- Models are represented by database queries
- Views are Jinja2 templates
- Controllers are Flask route handlers in `app.py`

**Authentication System**:
- Role-based authentication with four distinct user types: students, parents, wardens, security guards
- Each role stored in separate database tables
- Session-based authentication using Flask-Login
- User role stored in session to determine table lookup during user loading
- Password hashing using Werkzeug security utilities

**Rationale**:
- Flask provides lightweight, flexible routing without excessive overhead
- Flask-Login handles session management securely
- Separate tables per role allow different attributes per user type
- Session-based auth appropriate for server-rendered pages

### Data Storage

**Database**: PostgreSQL (accessed via psycopg2)

**Schema Design**:
- **Users**: Separate tables for each role (students, parents, wardens, security_guards)
- **Core Table**: gatepass_requests with foreign keys to student and parent
- **Status Fields**: Uses string-based status tracking (not true ENUMs due to PostgreSQL compatibility)
  - `parent_approval_status`: 'Pending', 'Approved', 'Rejected'
  - `warden_status`: 'Open', 'Closed'
  - `security_guard_status`: 'Out', 'In'

**Key Fields**:
- Timestamp fields for request creation, approval, and expiry (1-hour expiry window)
- Duration tracking in hours
- Foreign key relationships establishing student-parent linkage

**Rationale**:
- PostgreSQL provides reliability and ACID compliance for approval workflows
- Separate user tables allow role-specific attributes
- Timestamp-based expiry enables automatic invalidation of stale requests
- Direct SQL via psycopg2 gives fine-grained control over queries

### Business Logic

**Gatepass Workflow**:
1. Student creates request → Sets expiry to 1 hour from creation
2. Parent receives "simulated notification" (logged message with approval/rejection links)
3. Parent approves/rejects before expiry
4. Warden views all approved requests for oversight
5. Security guard marks student as Out when leaving, In when returning
6. Warden can close completed requests

**Expiry Mechanism**:
- Requests have a 1-hour approval window
- Timestamp comparison determines if request is expired
- Expired requests cannot be approved and are displayed as such

**Access Control**:
- Each dashboard only shows relevant requests for that role
- Parents see only their linked students' pending requests
- Wardens see all approved requests
- Security guards search by student ID to find approved requests

## External Dependencies

### Third-Party Libraries

**Flask Ecosystem**:
- `Flask`: Core web framework for routing and request handling
- `flask-login`: User session management and authentication decorators
- `werkzeug.security`: Password hashing and verification

**Database**:
- `psycopg2`: PostgreSQL database adapter for Python

**Frontend**:
- `Bootstrap 5.1.3` (via CDN): CSS framework for responsive UI components

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Secret key for Flask session encryption (defaults to 'dev-secret-key' for development)

### Database Connection

The application uses a connection factory pattern (`get_db_connection()`) that creates new PostgreSQL connections on demand. Connections are manually opened and closed per request to avoid connection pooling complexity.

**Note**: The database initialization script (`db_init.py`) drops and recreates all tables, suitable for development but requires migration strategy for production.