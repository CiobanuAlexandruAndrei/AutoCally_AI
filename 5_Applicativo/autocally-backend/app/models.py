from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
import logging

# Initialize database and marshmallow extensions
db = SQLAlchemy()
ma = Marshmallow()

logger = logging.getLogger(__name__)

# User model - centralized from security models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<User {self.username}>'

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    user = db.relationship('User', backref='tokens')

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    user = db.relationship('User', backref=db.backref('profile', uselist=False))

def create_default_user():
    """Create a default user if one doesn't exist"""
    try:
        default_user = User.query.filter_by(username='alex').first()
        if not default_user:
            hashed_password = generate_password_hash('Admin$00', method='pbkdf2:sha256')
            new_user = User(
                username='alex',
                password=hashed_password,
                email='alex@gmail.com'
            )
            db.session.add(new_user)
            db.session.commit()
            
            new_profile = Profile(user_id=new_user.id)
            db.session.add(new_profile)
            db.session.commit()
            
            logger.info("Default user created successfully")
        else:
            logger.info("Default user already exists")
    except Exception as e:
        logger.error(f"Error creating default user: {str(e)}")
        db.session.rollback() 