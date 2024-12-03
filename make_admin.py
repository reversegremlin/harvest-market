from flask import current_app
from extensions import db
from models import User
from app import app

def make_user_admin(username):
    with app.app_context():
        try:
            # Find user by username
            user = User.query.filter_by(username=username).first()
            
            if not user:
                app.logger.error(f'User {username} not found')
                return False, f'User {username} not found'
                
            if user.is_admin:
                app.logger.info(f'User {username} is already an admin')
                return True, f'User {username} is already an admin'
            
            # Update admin status
            user.is_admin = True
            db.session.commit()
            
            app.logger.info(f'Successfully made {username} an admin')
            return True, f'Successfully made {username} an admin'
            
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            app.logger.error(f'Error making {username} admin: {error_msg}')
            return False, f'Error making {username} admin: {error_msg}'

if __name__ == '__main__':
    success, message = make_user_admin('nadiabellamorris')
    print(message)
