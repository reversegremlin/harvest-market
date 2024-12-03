from flask import current_app
from extensions import db
from models import User
import logging
from app import app

def create_admin_user():
    with app.app_context():
        try:
            # Check if admin user already exists
            existing_user = User.query.filter_by(email='admin@marketharvest.com').first()
            if existing_user:
                # Update existing admin user
                existing_user.username = 'admin'
                existing_user.first_name = 'Admin'
                existing_user.last_name = 'User'
                existing_user.is_admin = True
                existing_user.email_verified = True
                existing_user.set_password('MarketHarvest2024!')
                existing_user.avatar_url = f"https://api.dicebear.com/6.x/avataaars/svg?seed=admin"
                db.session.commit()
                app.logger.info('Existing admin user updated successfully')
                return True

            # Create new admin user
            admin = User(
                email='admin@marketharvest.com',
                username='admin',
                first_name='Admin',
                last_name='User',
                is_admin=True,
                email_verified=True
            )
            admin.set_password('MarketHarvest2024!')
            admin.avatar_url = f"https://api.dicebear.com/6.x/avataaars/svg?seed=admin"

            # Add and commit to database
            db.session.add(admin)
            db.session.commit()
            
            app.logger.info('Admin user created successfully')
            return True
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating admin user: {str(e)}')
            return False

if __name__ == '__main__':
    success = create_admin_user()
    print('Admin user created successfully' if success else 'Failed to create admin user')
