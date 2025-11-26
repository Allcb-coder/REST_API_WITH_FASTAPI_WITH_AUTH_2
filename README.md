cat > README.md << 'EOF'
# Advertisement Service - Part 2

A complete FastAPI REST API for advertisement management with JWT authentication and role-based permissions.

##  Features

- **JWT Authentication** - Secure login with 48-hour tokens
- **User Management** - Complete CRUD with role-based permissions
- **Advertisement System** - Buy/sell ads with ownership
- **Role-Based Access** - User and Admin roles with different permissions
- **RESTful API** - Proper HTTP methods and status codes
- **Auto Documentation** - Interactive Swagger UI
- **SQLite Database** - SQLAlchemy ORM with relationships

##  API Endpoints

###  Authentication
- `POST /login` - Login and get JWT token

### 👥 Users
- `POST /user` - Register new user (public)
- `GET /user/{id}` - Get user by ID (public)
- `PATCH /user/{id}` - Update user (owner or admin only)
- `DELETE /user/{id}` - Delete user (owner or admin only)

###  Advertisements
- `POST /advertisement` - Create ad (authenticated users)
- `GET /advertisement/{id}` - Get ad by ID (public)
- `PATCH /advertisement/{id}` - Update ad (owner or admin only)
- `DELETE /advertisement/{id}` - Delete ad (owner or admin only)
- `GET /advertisement?{query}` - Search ads (public)

##  Permission System

### 👤 Unauthenticated Users
- Register new account
- View user profiles
- View advertisements
- Search advertisements

### 👥 Authenticated Users (user role)
- All unauthenticated permissions
- Update own profile
- Delete own account
- Create advertisements
- Update own advertisements
- Delete own advertisements

###  Admin Users (admin role)
- Full access to all operations
- Manage any user or advertisement

##  Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt