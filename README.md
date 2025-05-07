# BloodDonor - Blood Donation Management Platform

![BloodDonor Logo](static/images/logo.png)

## About The Project

BloodDonor is a comprehensive web platform designed to connect blood donors with hospitals and blood banks. It streamlines the blood donation process by providing an easy-to-use interface for donors to schedule appointments, track their donation history, and respond to emergency blood requests.

## Features

### For Donors
- Create and manage donor profiles with medical information
- Schedule blood donation appointments with hospitals
- View and track donation history
- Earn badges based on donation milestones
- Receive real-time notifications for emergency blood requests
- View compatibility with emergency requests based on blood type

### For Hospitals
- Create and manage hospital profiles
- Create emergency blood requests
- View and manage appointment schedules
- Track donor responses to emergency requests

### For Administrators
- Comprehensive dashboard with system statistics
- Manage donor and hospital accounts
- Create and manage notifications
- Review and approve donation appointments
- Create and distribute badges to donors
- Monitor emergency blood requests

## Technology Stack

- **Backend**: Python with Flask framework
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript
- **UI Framework**: Bootstrap 5
- **Icons**: Font Awesome

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/blooddonor.git
   cd blooddonor
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. Run the application:
   ```
   python app.py
   ```

7. Access the application in your browser:
   ```
   http://localhost:5000
   ```

## Default Admin Login Credentials
Email: admin@blooddonor.com 
Password: admin123
