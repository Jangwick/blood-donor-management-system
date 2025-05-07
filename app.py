from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from flask_migrate import Migrate
from sqlalchemy import text  # Add this import for text SQL queries

app = Flask(__name__)
app.config['SECRET_KEY'] = 'blooddonorwebsitesecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blooddonor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Association table for many-to-many relationship between User and Badge
user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True),
    db.Column('earned_date', db.DateTime, default=datetime.utcnow)
)

# Models
class DonorProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    blood_type = db.Column(db.String(5))
    weight = db.Column(db.Float)
    allergies = db.Column(db.Text)
    medications = db.Column(db.Text)
    past_illnesses = db.Column(db.Text)
    has_tattoos = db.Column(db.Boolean, default=False)
    recent_travel = db.Column(db.Text)
    last_donation_date = db.Column(db.DateTime)
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    contact_number = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='donor')  # donor, hospital, admin
    registered_date = db.Column(db.DateTime, default=datetime.utcnow)  # Added field
    donations = db.relationship('Donation', backref='donor', lazy=True)
    badges = db.relationship('Badge', secondary=user_badges, backref='users')
    profile = db.relationship('DonorProfile', backref='user', uselist=False)
    location = db.Column(db.String(200), nullable=True)  # Added location attribute

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    donation_date = db.Column(db.DateTime, default=datetime.utcnow)
    blood_center = db.Column(db.String(100))
    blood_component = db.Column(db.String(50))
    quantity = db.Column(db.Float)
    location = db.Column(db.String(100))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key for donor
    hospital_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key for hospital
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')  # Updated default status to 'pending'
    approved_by_admin = db.Column(db.Boolean, default=False)  # New field to track admin approval

    # Explicit relationships with foreign_keys
    donor = db.relationship('User', foreign_keys=[donor_id], backref=db.backref('donor_appointments', lazy='dynamic'))
    hospital = db.relationship('User', foreign_keys=[hospital_id], backref=db.backref('hospital_appointments', lazy='dynamic'))

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    criteria = db.Column(db.String(100))
    icon = db.Column(db.String(50))

class EmergencyRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    quantity_needed = db.Column(db.Float, nullable=False)
    urgency_level = db.Column(db.String(20), default='normal')  # normal, urgent, critical
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Remove the updated_at column for now
    # updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, fulfilled, expired
    message = db.Column(db.Text)
    
    # Add relationships
    hospital = db.relationship('User', foreign_keys=[hospital_id], backref=db.backref('emergency_requests', lazy='dynamic'))
    responses = db.relationship('EmergencyResponse', backref='request', lazy='dynamic', cascade="all, delete-orphan")

class EmergencyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('emergency_request.id'), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    response = db.Column(db.String(20))  # available, unavailable
    response_time = db.Column(db.DateTime, default=datetime.utcnow)
    arrival_status = db.Column(db.String(20), default='pending')  # pending, arrived, no-show

    # Add relationship to donor
    donor = db.relationship('User', foreign_keys=[donor_id], backref=db.backref('emergency_responses', lazy='dynamic'))

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    request_id = db.Column(db.Integer, db.ForeignKey('emergency_request.id'), nullable=True)
    
    # Add relationship to emergency request
    emergency_request = db.relationship('EmergencyRequest', foreign_keys=[request_id], backref=db.backref('notifications', lazy='dynamic'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'hospital':
                return redirect(url_for('hospital_dashboard'))
            else:
                return redirect(url_for('donor_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        contact_number = request.form.get('contact_number')
        role = request.form.get('role', 'donor')
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, 
                        contact_number=contact_number, role=role)
        db.session.add(new_user)
        db.session.commit()
        if role == 'donor':
            new_profile = DonorProfile(user_id=new_user.id)
            db.session.add(new_profile)
            db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

# Donor routes
@app.route('/donor/dashboard')
@login_required
def donor_dashboard():
    if current_user.role != 'donor':
        return redirect(url_for('index'))
    profile = current_user.profile
    donations = current_user.donations
    
    # Use raw SQL instead of ORM to avoid the missing column issues
    appointments_rows = db.session.execute(
        text("SELECT id, donor_id, hospital_id, appointment_date, status FROM appointment WHERE donor_id = :donor_id"),
        {'donor_id': current_user.id}
    ).fetchall()
    # Process the appointment rows into a usable format
    appointments = []
    for appt in appointments_rows:
        hospital = User.query.get(appt.hospital_id)
        
        # Convert appointment_date to a datetime object if it's a string
        appointment_date = appt.appointment_date
        if isinstance(appointment_date, str):
            try:
                appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d')
                except ValueError:
                    # If parsing fails, use current date as fallback
                    appointment_date = datetime.utcnow()
        appointments.append({
            'id': appt.id,
            'hospital': hospital,
            'appointment_date': appointment_date,
            'status': appt.status,
        })
    badges = current_user.badges
    
    # Temporarily use raw SQL to get notifications without request_id
    notifications_rows = db.session.execute(
        text("SELECT id, title, message, is_read, created_at FROM notification ORDER BY created_at DESC")
    ).fetchall()
    
    now = datetime.utcnow()
    return render_template('donor/dashboard.html', profile=profile, 
                           donations=donations, appointments=appointments, 
                           badges=badges, notifications=notifications_rows, now=now)

@app.route('/donor/notification/respond', methods=['POST'])
@login_required
def respond_to_notification():
    if current_user.role != 'donor':
        return redirect(url_for('index'))
    
    notification_id = request.form.get('notification_id')
    response = request.form.get('response')
    
    # Temporary simplified version without request_id functionality
    flash(f'You responded "{response}" to the notification.', 'info')
    return redirect(url_for('donor_dashboard'))

@app.route('/donor/profile', methods=['GET', 'POST'])
@login_required
def donor_profile():
    if current_user.role != 'donor':
        return redirect(url_for('index'))
    profile = current_user.profile
    if request.method == 'POST':
        profile.name = request.form.get('name')
        profile.age = int(request.form.get('age'))
        profile.gender = request.form.get('gender')
        profile.blood_type = request.form.get('blood_type')
        profile.weight = float(request.form.get('weight'))
        profile.allergies = request.form.get('allergies')
        profile.medications = request.form.get('medications')
        profile.past_illnesses = request.form.get('past_illnesses')
        profile.has_tattoos = True if request.form.get('has_tattoos') == 'yes' else False
        profile.recent_travel = request.form.get('recent_travel')
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('donor_dashboard'))
    return render_template('donor/profile.html', profile=profile)

@app.route('/donor/appointments')
@login_required
def donor_appointments():
    if current_user.role != 'donor':
        return redirect(url_for('index'))
    
    # Use raw SQL to query appointments to avoid any column issues
    appointments_rows = db.session.execute(
        text("""SELECT a.id, a.hospital_id, a.appointment_date, a.status, 
                u.username as hospital_name, u.location as hospital_location 
                FROM appointment a 
                JOIN user u ON a.hospital_id = u.id 
                WHERE a.donor_id = :donor_id 
                ORDER BY a.appointment_date DESC"""),
        {'donor_id': current_user.id}
    ).fetchall()
    
    # Format the appointments data
    appointments = []
    for appt in appointments_rows:
        # Convert appointment_date to a datetime object if it's a string
        appointment_date = appt.appointment_date
        if isinstance(appointment_date, str):
            try:
                appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d')
                except ValueError:
                    appointment_date = datetime.utcnow()
        
        appointments.append({
            'id': appt.id,
            'hospital_name': appt.hospital_name,
            'hospital_location': appt.hospital_location or 'Location not provided',
            'appointment_date': appointment_date,
            'date': appointment_date.strftime('%B %d, %Y'),
            'time': appointment_date.strftime('%I:%M %p'),
            'status': appt.status.capitalize()
        })
    
    return render_template('donor/appointments.html', appointments=appointments)

@app.route('/donor/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    if current_user.role != 'donor':
        return redirect(url_for('index'))
    
    # Find the appointment and verify it belongs to the current user
    appointment = db.session.execute(
        text("SELECT * FROM appointment WHERE id = :id AND donor_id = :donor_id"),
        {'id': appointment_id, 'donor_id': current_user.id}
    ).fetchone()
    
    if appointment:
        # Cancel the appointment
        db.session.execute(
            text("UPDATE appointment SET status = 'cancelled' WHERE id = :id"),
            {'id': appointment_id}
        )
        db.session.commit()
        flash('Appointment cancelled successfully.', 'success')
    else:
        flash('Appointment not found or you do not have permission to cancel it.', 'danger')
    
    return redirect(url_for('donor_appointments'))

@app.route('/donor/history')
@login_required
def donor_history():
    if current_user.role != 'donor':
        return redirect(url_for('index'))
        
    # Get actual donation history for the current user
    donations = Donation.query.filter_by(user_id=current_user.id).order_by(Donation.donation_date.desc()).all()
    
    # Format donation history with all necessary data
    donation_history = []
    for donation in donations:
        donation_history.append({
            "id": donation.id,
            "date": donation.donation_date.strftime('%B %d, %Y'),
            "raw_date": donation.donation_date,
            "location": donation.location,
            "blood_center": donation.blood_center,
            "blood_component": donation.blood_component,
            "quantity": donation.quantity,
            "blood_type": current_user.profile.blood_type if current_user.profile else "Unknown",
            "status": "Completed"  # Default status for recorded donations
        })
        
    # Get profile for badge progress display
    profile = current_user.profile
    
    # Calculate donation stats
    total_donations = len(donation_history)
    total_quantity = sum(item["quantity"] for item in donation_history) if donation_history else 0
    
    # Calculate time until next eligible donation
    days_until_eligible = 0
    if profile and profile.last_donation_date:
        days_since_last = (datetime.utcnow() - profile.last_donation_date).days
        days_until_eligible = max(0, 90 - days_since_last)  # Standard 90-day wait period
    
    return render_template('donor/history.html', 
                          donation_history=donation_history,
                          profile=profile,
                          total_donations=total_donations,
                          total_quantity=total_quantity,
                          days_until_eligible=days_until_eligible)

@app.route('/donor/badges')
@login_required
def donor_badges():
    if current_user.role != 'donor':
        return redirect(url_for('index'))
    
    # Get current user's badges from the database
    user_badges = current_user.badges
    
    # Get all available badges to show what the donor can earn
    all_badges = Badge.query.all()
    
    # Determine which badges the user hasn't earned yet
    earned_badge_ids = [badge.id for badge in user_badges]
    unearned_badges = [badge for badge in all_badges if badge.id not in earned_badge_ids]
    
    # Calculate progress for various badge criteria
    donation_count = Donation.query.filter_by(user_id=current_user.id).count()
    
    # Calculate donations in the past year for "Regular Donor" badge
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    recent_donations = Donation.query.filter(
        Donation.user_id == current_user.id,
        Donation.donation_date > one_year_ago
    ).count()
    
    # Calculate lifetime donation volume
    total_volume = db.session.query(db.func.sum(Donation.quantity)).filter(
        Donation.user_id == current_user.id
    ).scalar() or 0
    
    # Build badge progress data
    badge_progress = {
        "first_donation": {
            "current": min(donation_count, 1),
            "target": 1,
            "percentage": min(donation_count * 100, 100)
        },
        "regular_donor": {
            "current": min(recent_donations, 3),
            "target": 3,
            "percentage": min(recent_donations * 100 // 3, 100)
        },
        "lifetime_volume": {
            "current": total_volume,
            "target": 10,
            "percentage": min(int(total_volume * 10), 100)
        }
    }
    
    return render_template('donor/badges.html', 
                          earned_badges=user_badges, 
                          unearned_badges=unearned_badges,
                          badge_progress=badge_progress,
                          donation_count=donation_count,
                          recent_donations=recent_donations,
                          total_volume=total_volume)

@app.route('/donor/schedule-donation', methods=['GET', 'POST'])
@login_required
def donor_schedule_donation():
    if current_user.role != 'donor':
        return redirect(url_for('index'))
    if request.method == 'POST':
        hospital_id = request.form.get('hospital_id')
        appointment_date = request.form.get('appointment_date')
        # Validate input
        if not hospital_id or not appointment_date:
            flash('Please select a hospital and appointment date.', 'danger')
            return redirect(url_for('donor_schedule_donation'))
        try:
            # Parse the appointment_date string into a datetime object
            appointment_date = datetime.strptime(appointment_date, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format. Please select a valid date and time.', 'danger')
            return redirect(url_for('donor_schedule_donation'))
        
        # Use direct SQL to insert the appointment without the approved_by_admin column
        db.session.execute(
            text("INSERT INTO appointment (donor_id, hospital_id, appointment_date, status) VALUES (:donor_id, :hospital_id, :appointment_date, :status)"),
            {
                'donor_id': current_user.id,
                'hospital_id': int(hospital_id),
                'appointment_date': appointment_date,
                'status': 'pending'
            }
        )
        db.session.commit()
        flash('Donation appointment requested successfully! Awaiting admin approval.', 'success')
        return redirect(url_for('donor_dashboard'))
    hospitals = User.query.filter_by(role='hospital').all()
    return render_template('donor/schedule_donation.html', hospitals=hospitals)

# Hospital routes
@app.route('/hospital/dashboard')
@login_required
def hospital_dashboard():
    if current_user.role != 'hospital':
        return redirect(url_for('index'))
    emergency_requests = EmergencyRequest.query.filter_by(hospital_id=current_user.id).order_by(EmergencyRequest.created_at.desc()).all()
    appointments = Appointment.query.filter_by(hospital_id=current_user.id).order_by(Appointment.appointment_date).all()
    return render_template('hospital/dashboard.html', emergency_requests=emergency_requests, appointments=appointments)

# Emergency Request Routes for Hospitals
@app.route('/hospital/emergency-requests')
@login_required
def hospital_emergency_requests():
    if current_user.role != 'hospital':
        return redirect(url_for('index'))
    # Get all emergency requests created by this hospital
    emergency_requests = EmergencyRequest.query.filter_by(hospital_id=current_user.id).order_by(EmergencyRequest.created_at.desc()).all()
    
    return render_template('hospital/emergency_requests.html', emergency_requests=emergency_requests)

@app.route('/hospital/create-emergency-request', methods=['GET', 'POST'])
@login_required
def hospital_create_emergency_request():
    if current_user.role != 'hospital':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        blood_type = request.form.get('blood_type')
        quantity_needed = request.form.get('quantity_needed')
        urgency_level = request.form.get('urgency_level')
        message = request.form.get('message')
        
        # Validate input
        if not blood_type or not quantity_needed or not urgency_level:
            flash('Please complete all required fields.', 'danger')
            return redirect(url_for('hospital_create_emergency_request'))
        
        # Create new emergency request
        new_request = EmergencyRequest(
            hospital_id=current_user.id,
            blood_type=blood_type,
            quantity_needed=float(quantity_needed),
            urgency_level=urgency_level,
            message=message,
            status='active'
        )
        db.session.add(new_request)
        db.session.commit()
        
        # Create a system notification for this emergency request - without request_id
        notification = Notification(
            title=f"URGENT: {blood_type} Blood Needed",
            message=f"{current_user.username} has issued an emergency request for {blood_type} blood ({quantity_needed} units). Urgency level: {urgency_level.upper()}. {message}"
        )
        db.session.add(notification)
        db.session.commit()
        flash('Emergency request created successfully!', 'success')
        return redirect(url_for('hospital_emergency_requests'))
        
    return render_template('hospital/create_emergency_request.html')

@app.route('/hospital/emergency-requests/<int:request_id>/cancel', methods=['POST'])
@login_required
def hospital_cancel_emergency_request(request_id):
    if current_user.role != 'hospital':
        return redirect(url_for('index'))
    
    emergency_request = EmergencyRequest.query.filter_by(id=request_id, hospital_id=current_user.id).first_or_404()
    emergency_request.status = 'cancelled'
    db.session.commit()
    flash('Emergency request has been cancelled.', 'success')
    return redirect(url_for('hospital_emergency_requests'))

# Admin Emergency Request Management
@app.route('/admin/emergency-requests')
@login_required
def admin_emergency_requests():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    # Get all emergency requests
    active_requests = EmergencyRequest.query.filter_by(status='active').order_by(EmergencyRequest.created_at.desc()).all()
    fulfilled_requests = EmergencyRequest.query.filter_by(status='fulfilled').order_by(EmergencyRequest.created_at.desc()).all()
    cancelled_requests = EmergencyRequest.query.filter_by(status='cancelled').order_by(EmergencyRequest.created_at.desc()).all()
    expired_requests = EmergencyRequest.query.filter_by(status='expired').order_by(EmergencyRequest.created_at.desc()).all()
    # Get current time for age calculations
    now = datetime.utcnow()
    
    return render_template('admin/emergency_requests.html', 
                          active_requests=active_requests,
                          fulfilled_requests=fulfilled_requests,
                          cancelled_requests=cancelled_requests,
                          expired_requests=expired_requests,
                          now=now)

@app.route('/admin/emergency-requests/<int:request_id>/fulfill', methods=['POST'])
@login_required
def admin_fulfill_emergency_request(request_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    emergency_request = EmergencyRequest.query.get_or_404(request_id)
    emergency_request.status = 'fulfilled'
    db.session.commit()
    flash('Emergency request marked as fulfilled.', 'success')
    return redirect(url_for('admin_emergency_requests'))

@app.route('/admin/emergency-requests/<int:request_id>/expire', methods=['POST'])
@login_required
def admin_expire_emergency_request(request_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    emergency_request = EmergencyRequest.query.get_or_404(request_id)
    emergency_request.status = 'expired'
    db.session.commit()
    flash('Emergency request marked as expired.', 'success')
    return redirect(url_for('admin_emergency_requests'))

# Donor Emergency Response
@app.route('/donor/emergency-requests')
@login_required
def donor_emergency_requests():
    if current_user.role != 'donor':
        return redirect(url_for('index'))
    
    # Only show active emergency requests that match the donor's blood type
    blood_type = None
    if current_user.profile and current_user.profile.blood_type:
        blood_type = current_user.profile.blood_type
    
    # Get all active emergency requests
    active_requests = EmergencyRequest.query.filter_by(status='active').order_by(EmergencyRequest.created_at.desc()).all()
    
    # Filter requests that match the donor's blood type or if blood_type is None, show all
    if blood_type:
        matching_requests = [req for req in active_requests if is_compatible(blood_type, req.blood_type)]
    else:
        matching_requests = active_requests
    
    # Check if the donor has already responded to any requests
    responded_request_ids = [resp.request_id for resp in EmergencyResponse.query.filter_by(donor_id=current_user.id).all()]
    
    return render_template('donor/emergency_requests.html', 
                          matching_requests=matching_requests,
                          responded_request_ids=responded_request_ids)

@app.route('/donor/emergency-requests/<int:request_id>/respond', methods=['POST'])
@login_required
def donor_respond_to_emergency(request_id):
    if current_user.role != 'donor':
        return redirect(url_for('index'))
    
    emergency_request = EmergencyRequest.query.get_or_404(request_id)
    response_type = request.form.get('response', 'available')
    
    # Check if donor has already responded
    existing_response = EmergencyResponse.query.filter_by(
        request_id=request_id,
        donor_id=current_user.id
    ).first()
    
    if existing_response:
        # Update existing response
        existing_response.response = response_type
        existing_response.response_time = datetime.utcnow()
    else:
        # Create new response
        new_response = EmergencyResponse(
            request_id=request_id,
            donor_id=current_user.id,
            response=response_type,
            arrival_status='pending'
        )
        db.session.add(new_response)
    
    db.session.commit()
    
    if response_type == 'available':
        flash('Thank you for your willingness to help! The hospital will contact you shortly.', 'success')
    else:
        flash('Thank you for your response. Stay safe!', 'info')
    
    return redirect(url_for('donor_emergency_requests'))

# Helper function to determine blood type compatibility
def is_compatible(donor_type, recipient_type):
    # Universal recipient (AB+) can receive from any donor
    if recipient_type == 'AB+':
        return True
    
    # O- is universal donor
    if donor_type == 'O-':
        return True
    
    # Simple compatibility check - this is a simplified version and should be expanded
    compatibility = {
        'O+': ['O+', 'O-'],
        'O-': ['O-'],
        'A+': ['A+', 'A-', 'O+', 'O-'],
        'A-': ['A-', 'O-'],
        'B+': ['B+', 'B-', 'O+', 'O-'],
        'B-': ['B-', 'O-'],
        'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
        'AB-': ['A-', 'B-', 'AB-', 'O-']
    }
    
    if recipient_type in compatibility:
        return donor_type in compatibility[recipient_type]
    
    return False

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    # Fetch data for the dashboard
    donors = User.query.filter_by(role='donor').all()
    hospitals = User.query.filter_by(role='hospital').all()
    users_count = len(donors)
    hospitals_count = len(hospitals)
    donations_count = Donation.query.count()
    emergency_requests_count = EmergencyRequest.query.filter_by(status='active').count()
    
    # Update badge assignments for donors with donations
    check_and_award_badges()
    
    badges = Badge.query.all()
    
    # Count pending appointments using raw SQL with text() function
    pending_appointments_count = db.session.execute(
        text("SELECT COUNT(*) FROM appointment WHERE status = 'pending'")
    ).scalar()
    # Fetch the latest 5 notifications
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
        users_count=users_count,
        hospitals_count=hospitals_count,
        donations_count=donations_count,
        emergency_requests_count=emergency_requests_count,
        pending_appointments_count=pending_appointments_count,
        donors=donors,
        hospitals=hospitals,
        badges=badges,
        notifications=notifications
    )

# Helper function to check and award badges based on donations
def check_and_award_badges():
    # Get all donors
    donors = User.query.filter_by(role='donor').all()
    
    # Get the first donation badge
    first_donation_badge = Badge.query.filter_by(name='First Donation').first()
    if not first_donation_badge:
        # Create the badge if it doesn't exist
        first_donation_badge = Badge(
            name='First Donation',
            description='Awarded for completing your first blood donation',
            criteria='one_donation',
            icon='star'
        )
        db.session.add(first_donation_badge)
    
    # Get the regular donor badge
    regular_donor_badge = Badge.query.filter_by(name='Regular Donor').first()
    if not regular_donor_badge:
        # Create the badge if it doesn't exist
        regular_donor_badge = Badge(
            name='Regular Donor',
            description='Awarded for donating 3 or more times in a year',
            criteria='three_donations_year',
            icon='medal'
        )
        db.session.add(regular_donor_badge)
    
    db.session.commit()
    
    # Check each donor for badge eligibility
    for donor in donors:
        donations = Donation.query.filter_by(user_id=donor.id).all()
        
        # Award First Donation badge
        if donations and first_donation_badge not in donor.badges:
            donor.badges.append(first_donation_badge)
        
        # Count donations in the past year
        one_year_ago = datetime.utcnow() - timedelta(days=365)
        recent_donations = [d for d in donations if d.donation_date > one_year_ago]
        
        # Award Regular Donor badge
        if len(recent_donations) >= 3 and regular_donor_badge not in donor.badges:
            donor.badges.append(regular_donor_badge)
    
    db.session.commit()

@app.route('/admin/create/donor', methods=['GET', 'POST'])
@login_required
def admin_create_donor():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        blood_type = request.form.get('blood_type')
        # Check if the email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('admin_create_donor'))
        # Create the new donor user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, role='donor')
        db.session.add(new_user)
        db.session.commit()
        # Create the donor profile (removing duplicate code)
        new_profile = DonorProfile(user_id=new_user.id, name=full_name, blood_type=blood_type)
        db.session.add(new_profile)
        db.session.commit()
        flash('Donor account created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/create_donor.html')

@app.route('/admin/create/hospital', methods=['GET', 'POST'])
@login_required
def admin_create_hospital():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        contact_number = request.form.get('contact_number')
        hospital_name = request.form.get('hospital_name')
        hospital_address = request.form.get('hospital_address')
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('admin_create_hospital'))
        # Create new hospital user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            contact_number=contact_number,
            role='hospital'
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Hospital account created successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/create_hospital.html')

@app.route('/admin/create/notification', methods=['GET', 'POST'])
@login_required
def admin_create_notification():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        # Validate title and message
        if not title or not message:
            flash('Title and message are required.', 'danger')
            return redirect(url_for('admin_create_notification'))
        # Create a new notification
        notification = Notification(
            title=title,
            message=message
        )
        db.session.add(notification)
        db.session.commit()
        flash('Notification created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/create_notification.html')

@app.route('/admin/create/badge', methods=['GET', 'POST'])
@login_required
def admin_create_badge():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        criteria = request.form.get('criteria')
        icon = request.form.get('icon')
        # Check if badge already exists
        if Badge.query.filter_by(name=name).first():
            flash('A badge with this name already exists', 'danger')
            return redirect(url_for('admin_create_badge'))
        # Create new badge
        new_badge = Badge(
            name=name,
            description=description,
            criteria=criteria,
            icon=icon
        )
        db.session.add(new_badge)
        db.session.commit()
        flash('Badge created successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/create_badge.html')

@app.route('/admin/create-emergency-request', methods=['GET', 'POST'])
@login_required
def admin_create_emergency_request():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        hospital_id = request.form.get('hospital_id')
        blood_type = request.form.get('blood_type')
        quantity_needed = request.form.get('quantity_needed')
        urgency_level = request.form.get('urgency_level')
        message = request.form.get('message')
        
        # Validate input
        if not hospital_id or not blood_type or not quantity_needed or not urgency_level:
            flash('Please complete all required fields.', 'danger')
            return redirect(url_for('admin_create_emergency_request'))
        
        # Create new emergency request
        new_request = EmergencyRequest(
            hospital_id=hospital_id,
            blood_type=blood_type,
            quantity_needed=float(quantity_needed),
            urgency_level=urgency_level,
            message=message,
            status='active'
        )
        db.session.add(new_request)
        db.session.commit()
        
        # Create a system notification for this emergency request - now with request_id
        hospital = User.query.get(hospital_id)
        notification = Notification(
            title=f"URGENT: {blood_type} Blood Needed",
            message=f"{hospital.username} has issued an emergency request for {blood_type} blood ({quantity_needed} units). Urgency level: {urgency_level.upper()}. {message}",
            request_id=new_request.id  # Link the notification to the emergency request
        )
        db.session.add(notification)
        db.session.commit()
        flash('Emergency request created successfully!', 'success')
        return redirect(url_for('admin_emergency_requests'))
    
    # Get all hospitals for the dropdown selection
    hospitals = User.query.filter_by(role='hospital').all()
    return render_template('admin/create_emergency_request.html', hospitals=hospitals)

# Admin Management Routes
@app.route('/admin/donors')
@login_required
def admin_donors():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    donors = User.query.filter_by(role='donor').all()
    return render_template('admin/donors.html', donors=donors)

@app.route('/admin/donors/<int:donor_id>/view')
@login_required
def admin_view_donor(donor_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    # Fetch donor details from the database using the User model
    donor = User.query.filter_by(id=donor_id, role='donor').first_or_404()
    # Get the donor's donation history
    donations = Donation.query.filter_by(user_id=donor_id).order_by(Donation.donation_date.desc()).all()
    
    # Get appointment history using raw SQL to avoid the missing column issue
    appointments_rows = db.session.execute(
        text("SELECT id, donor_id, hospital_id, appointment_date, status FROM appointment WHERE donor_id = :donor_id ORDER BY appointment_date DESC"),
        {'donor_id': donor_id}
    ).fetchall()
    
    # Process the appointment rows into a usable format
    appointments = []
    for appt in appointments_rows:
        hospital = User.query.get(appt.hospital_id)
        
        # Convert appointment_date to a datetime object if it's a string
        appointment_date = appt.appointment_date
        if isinstance(appointment_date, str):
            try:
                appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d')
                except ValueError:
                    appointment_date = datetime.utcnow()
        appointments.append({
            'id': appt.id,
            'hospital': hospital,
            'appointment_date': appointment_date,
            'status': appt.status
        })
    
    return render_template('admin/view_donor.html', donor=donor, donations=donations, appointments=appointments)

@app.route('/admin/donors/<int:donor_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_donor(donor_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    donor = User.query.get_or_404(donor_id)
    if request.method == 'POST':
        try:
            # Update donor's main details
            donor.username = request.form['username']
            donor.email = request.form['email']
            # Update donor's profile details
            if donor.profile:
                donor.profile.name = request.form.get('username', donor.profile.name)
                donor.profile.blood_type = request.form.get('blood_type', donor.profile.blood_type)
            else:
                # Create a profile if it doesn't exist
                donor.profile = DonorProfile(
                    user_id=donor.id,
                    name=request.form.get('username'),
                    blood_type=request.form.get('blood_type')
                )
            db.session.commit()
            flash('Donor details updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))  # Redirect to the dashboard after saving
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", 'danger')
    return render_template('admin/edit_donor.html', donor=donor)

@app.route('/admin/donors/<int:donor_id>/delete', methods=['POST'])
@login_required
def admin_delete_donor(donor_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    donor = User.query.filter_by(id=donor_id, role='donor').first_or_404()
    try:
        # Delete the associated donor profile if it exists
        if donor.profile:
            db.session.delete(donor.profile)
        # Delete the donor
        db.session.delete(donor)
        db.session.commit()
        flash('Donor deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the donor: {str(e)}", 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/donors/<int:donor_id>/add-donation', methods=['POST'])
@login_required
def add_donation(donor_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    donor = User.query.filter_by(id=donor_id, role='donor').first_or_404()
    
    # Get form data
    donation_date = request.form.get('donation_date')
    blood_center = request.form.get('blood_center')
    blood_component = request.form.get('blood_component')
    quantity = request.form.get('quantity')
    location = request.form.get('location')
    
    # Convert string date to datetime
    donation_date = datetime.strptime(donation_date, '%Y-%m-%d')
    
    # Create new donation record
    donation = Donation(
        user_id=donor_id,
        donation_date=donation_date,
        blood_center=blood_center,
        blood_component=blood_component,
        quantity=float(quantity),
        location=location,
    )
    
    # Update donor's last donation date
    if donor.profile:
        donor.profile.last_donation_date = donation_date
    
    db.session.add(donation)
    db.session.commit()
    flash('Donation record added successfully!', 'success')
    return redirect(url_for('admin_view_donor', donor_id=donor_id))

# Admin Management Routes for Hospitals
@app.route('/admin/hospitals')
@login_required
def admin_hospitals():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    hospitals = User.query.filter_by(role='hospital').all()
    return render_template('admin/hospitals.html', hospitals=hospitals)

@app.route('/admin/hospitals/<int:hospital_id>/view')
@login_required
def admin_view_hospital(hospital_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    hospital = User.query.filter_by(id=hospital_id, role='hospital').first_or_404()
    return render_template('admin/view_hospital.html', hospital=hospital)

@app.route('/admin/hospitals/<int:hospital_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_hospital(hospital_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    hospital = User.query.filter_by(id=hospital_id, role='hospital').first_or_404()
    if request.method == 'POST':
        try:
            hospital.username = request.form['username']
            hospital.email = request.form['email']
            hospital.contact_number = request.form.get('contact_number', hospital.contact_number)
            hospital.location = request.form.get('location', hospital.location)
            db.session.commit()
            flash('Hospital details updated successfully!', 'success')
            return redirect(url_for('admin_hospitals'))
        except KeyError as e:
            flash(f"Missing form field: {e.args[0]}", 'danger')
    return render_template('admin/edit_hospital.html', hospital=hospital)

@app.route('/admin/hospitals/<int:hospital_id>/delete', methods=['GET', 'POST'])
@login_required
def admin_delete_hospital(hospital_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    hospital = User.query.filter_by(id=hospital_id, role='hospital').first_or_404()
    if request.method == 'POST':
        db.session.delete(hospital)
        db.session.commit()
        flash('Hospital deleted successfully!', 'success')
        return redirect(url_for('admin_hospitals'))
    return render_template('admin/delete_confirmation.html', entity_name=hospital.username, cancel_url=url_for('admin_hospitals'))

# Admin Management Routes for Blood Banks
@app.route('/admin/blood-banks')
@login_required
def admin_blood_banks():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    blood_banks = User.query.filter_by(role='blood_bank').all()
    return render_template('admin/blood_banks.html', blood_banks=blood_banks)

@app.route('/admin/blood-banks/<int:blood_bank_id>/view')
@login_required
def admin_view_blood_bank(blood_bank_id):
    if current_user.role != 'admin':  # Fixed: removed the extra parenthesis
        return redirect(url_for('index'))
    blood_bank = User.query.filter_by(id=blood_bank_id, role='blood_bank').first_or_404()
    return render_template('admin/view_blood_bank.html', blood_bank=blood_bank)

@app.route('/admin/blood-banks/<int:blood_bank_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_blood_bank(blood_bank_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    blood_bank = User.query.filter_by(id=blood_bank_id, role='blood_bank').first_or_404()
    if request.method == 'POST':
        blood_bank.username = request.form['username']
        blood_bank.email = request.form['email']
        blood_bank.contact_number = request.form['contact_number']
        db.session.commit()
        flash('Blood bank details updated successfully!', 'success')
        return redirect(url_for('admin_blood_banks'))
    return render_template('admin/edit_blood_bank.html', blood_bank=blood_bank)

@app.route('/admin/blood-banks/<int:blood_bank_id>/delete', methods=['GET', 'POST'])
@login_required
def admin_delete_blood_bank(blood_bank_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    blood_bank = User.query.filter_by(id=blood_bank_id, role='blood_bank').first_or_404()
    if request.method == 'POST':
        db.session.delete(blood_bank)
        db.session.commit()
        flash('Blood bank deleted successfully!', 'success')
        return redirect(url_for('admin_blood_banks'))
    return render_template('admin/delete_confirmation.html', entity_name=blood_bank.username, cancel_url=url_for('admin_blood_banks'))

@app.route('/admin/badges')
@login_required
def admin_badges():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    badges = Badge.query.all()
    return render_template('admin/badges.html', badges=badges)

@app.route('/admin/notifications')
@login_required
def admin_notifications():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    # Fetch all notifications
    notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template('admin/notifications.html', notifications=notifications)

@app.route('/admin/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def admin_mark_notification_read(notification_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    notification = Notification.query.get_or_404(notification_id)
    notification.is_read = True
    db.session.commit()
    flash('Notification marked as read.', 'success')
    return redirect(url_for('admin_notifications'))

@app.route('/admin/notifications/<int:notification_id>/delete', methods=['POST'])
@login_required
def admin_delete_notification(notification_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    notification = Notification.query.get_or_404(notification_id)
    db.session.delete(notification)
    db.session.commit()
    flash('Notification deleted successfully.', 'success')
    return redirect(url_for('admin_notifications'))

@app.route('/admin/requests')
@login_required
def admin_requests():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    # Fetch all active emergency requests
    requests = EmergencyRequest.query.order_by(EmergencyRequest.created_at.desc()).all()
    return render_template('admin/requests.html', requests=requests)

@app.route('/admin/donations')
@login_required
def admin_donations():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    # Fetch all donations
    donations = Donation.query.order_by(Donation.donation_date.desc()).all()
    return render_template('admin/donations.html', donations=donations)

@app.route('/admin/appointments')
@login_required
def admin_appointments():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    # Use a direct SQL query with text() function
    pending_appointments = db.session.execute(
        text("SELECT id, donor_id, hospital_id, appointment_date, status FROM appointment WHERE status = 'pending'")
    ).fetchall()
    # Get donor and hospital details for each appointment
    appointments_with_details = []
    for appt in pending_appointments:
        donor = User.query.get(appt.donor_id)
        hospital = User.query.get(appt.hospital_id)
        
        # Convert appointment_date to a datetime object if it's a string
        appointment_date = appt.appointment_date
        if isinstance(appointment_date, str):
            try:
                appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d')
                except ValueError:
                    appointment_date = datetime.utcnow()
        appointments_with_details.append({
            'id': appt.id,
            'donor': donor,
            'hospital': hospital,
            'appointment_date': appointment_date,
            'status': appt.status
        })
    
    return render_template('admin/appointments.html', pending_appointments=appointments_with_details)

@app.route('/admin/appointments/<int:appointment_id>/approve', methods=['POST'])
@login_required
def approve_appointment(appointment_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    # Update only the status field with text() function
    db.session.execute(
        text("UPDATE appointment SET status = 'approved' WHERE id = :id"),
        {'id': appointment_id}
    )
    db.session.commit()
    flash('Appointment approved successfully!', 'success')
    return redirect(url_for('admin_appointments'))

if __name__ == '__main__':
    with app.app_context():
        # Ensure the database schema exists (only creates tables if they don't already exist)
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_password = generate_password_hash('admin123')
            admin = User(username='admin', email='admin@blooddonor.com', 
                         password=admin_password, role='admin')
            db.session.add(admin)
            db.session.commit()
            
            # Create sample notification
            notification = Notification(
                title='Welcome to BloodDonor',
                message='Thank you for using our platform!',
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()
            
    app.run(debug=True)