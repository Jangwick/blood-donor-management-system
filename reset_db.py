from app import app, db, User, Notification, DonorProfile
from werkzeug.security import generate_password_hash
from datetime import datetime

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables with the correct schema
        db.create_all()
        
        # Create admin user
        admin_password = generate_password_hash('admin123')
        admin = User(
            username='admin',
            email='admin@blooddonor.com',
            password=admin_password,
            role='admin',
            is_active=True,
            registered_date=datetime.utcnow()
        )
        db.session.add(admin)
        
        # Create sample notification
        notification = Notification(
            title='Welcome to BloodDonor',
            message='Thank you for using our platform!',
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.session.add(notification)
        
        # Commit changes
        db.session.commit()
        print("Database has been reset and recreated with initial data.")

if __name__ == "__main__":
    reset_database()
