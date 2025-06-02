from ..extensions import db

class PhoneNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_sid = db.Column(db.String(64), nullable=False)
    auth_token = db.Column(db.String(64), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    profile = db.relationship('Profile', backref='phone_numbers')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())