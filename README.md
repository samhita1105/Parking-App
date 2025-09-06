# Vehicle Parking App

## Description
Vehicle Parking App is a web application designed to provide a seamless solution for finding and managing parking spaces. It supports both regular users and administrators, allowing users to book and release parking spots while enabling admins to manage parking lots and users efficiently.

## Features
- User registration and secure login with password hashing using bcrypt
- User dashboard to view available parking lots and book/release parking spots
- Admin dashboard to create, edit, and delete parking lots
- Booking cost calculation based on parking duration and price per hour
- Role-based access control with separate views for users and admins

## Technologies Used
- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- bcrypt
- SQLite
- Bootstrap 5 for frontend styling

## Setup Instructions
1. Clone the repository or download the project files.
2. Ensure you have Python installed (version 3.7 or higher recommended).
3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
5. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Run the application:
   ```bash
   python app.py
   ```
7. Open your browser and navigate to `http://127.0.0.1:5000/` to access the app.

## Usage
- Register a new user or login with existing credentials.
- Users can view parking lots, book available spots, and release them when done.
- Admin users can access the admin dashboard to manage parking lots and view users.
- The system calculates the total cost of parking based on the duration and lot pricing.

## Project Structure
```
.
├── app.py                  # Main Flask application and routes
├── parking.db              # SQLite database file
├── requirements.txt        # Python dependencies
├── static/
│   └── css/
│       └── style.css       # CSS styles
└── templates/              # HTML templates for various pages
    ├── admin_dashboard.html
    ├── base.html
    ├── index.html
    ├── login.html
    ├── lot_form.html
    ├── register.html
    └── user_dashboard.html
```

## Default Admin Credentials
- Username: `admin`
- Password: `admin123`

The admin user is automatically created on the first run of the application.
