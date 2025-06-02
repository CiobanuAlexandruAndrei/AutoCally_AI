from ..extensions import db
from ..phone_numbers.models import PhoneNumber

class Assistant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    prompt = db.Column(db.String(10000), nullable=True)
    greeting_message = db.Column(db.String(500), nullable=True)
    cartesia_voice_id = db.Column(db.String(64), nullable=True)
    llm_model = db.Column(db.String(64), default="llama-3.3-70b-versatile")
    llm_temperature = db.Column(db.Float, default=0.0)
    llm_max_tokens = db.Column(db.Integer, default=100)

    phone_number_id = db.Column(db.Integer, db.ForeignKey('phone_number.id'), nullable=True)
    phone_number = db.relationship('PhoneNumber', backref='assistants', lazy='joined')

    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    profile = db.relationship('Profile', backref='assistants', foreign_keys=[profile_id])

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

""" 
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assistant_id = db.Column(db.Integer, db.ForeignKey('assistant.id'), nullable=False)
    assistant = db.relationship('Assistant', backref='conversations')

    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    profile = db.relationship('Profile', backref='conversations')

    question = db.Column(db.String(1024), nullable=False)
    answer = db.Column(db.String(1024), nullable=False)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now()) """
    

class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    function = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
