from flask import current_app
from extensions import db
from models import User
import logging
from app import app

def verify_and_fix_admin():
    with app.app_context():
        try:
            # Check if admin user exists
            admin = User.query.filter_by(email='admin@marketharvest.com').first()
            
            if not admin:
                app.logger.error('Admin user not found')
                return False
                
            # Update admin user properties if needed
            needs_update = False
            
            if not admin.is_admin:
                admin.is_admin = True
                needs_update = True
                app.logger.info('Updated admin privileges')
                
            if not admin.email_verified:
                admin.email_verified = True
                needs_update = True
                app.logger.info('Updated email verification status')
            
            # Update password using set_password method
            admin.set_password('MarketHarvest2024!')
            needs_update = True
            app.logger.info('Updated admin password')
            
            if needs_update:
                db.session.commit()
                app.logger.info('Admin user updated successfully')
            else:
                app.logger.info('Admin user already has correct settings')
                
            return True
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error updating admin user: {str(e)}')
            return False

if __name__ == '__main__':
    success = verify_and_fix_admin()
    print('Admin user verified and updated successfully' if success else 'Failed to verify/update admin user')
