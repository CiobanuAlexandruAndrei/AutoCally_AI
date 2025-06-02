from ..extensions import db
from datetime import datetime
import enum 
from ..phone_numbers.models import PhoneNumber


class CallType(enum.Enum):
    inbound = 'inbound'
    outbound = 'outbound'
    test = 'test'

class Call(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_sid = db.Column(db.String(64), nullable=False)

    phone_number_id = db.Column(db.Integer, db.ForeignKey('phone_number.id'), nullable=False)
    phone_number = db.relationship('PhoneNumber', backref='calls')

    external_phone_number_id = db.Column(db.Integer, db.ForeignKey('external_phone_number.id'), nullable=True)
    external_phone_number = db.relationship('ExternalPhoneNumber', backref='calls')

    call_type = db.Column(db.Enum(CallType), nullable=False)

    status = db.Column(db.String(20), nullable=False)
    direction = db.Column(db.String(15), nullable=False)
    duration = db.Column(db.Integer, nullable=True)

    recording_url = db.Column(db.String(255), nullable=True)

    phone_number_id = db.Column(db.Integer, db.ForeignKey('phone_number.id'), nullable=False)
    phone_number = db.relationship('PhoneNumber', backref='calls')

    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)

    
class ConversationRole(enum.Enum):
    caller = 'caller'
    assistant = 'assistant'

class ConversationTranscript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transcript = db.Column(db.Text, nullable=False)

    start_time = db.Column(db.Integer, nullable=True)
    end_time = db.Column(db.Integer, nullable=True)

    call_id = db.Column(db.Integer, db.ForeignKey('call.id'), nullable=False)
    call = db.relationship('Call', backref='transcripts')

    role = db.Column(db.Enum(ConversationRole), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class CallSystemMessageType(enum.Enum):
    call_info = 'call_info'
    call_error = 'call_error'
    call_warning = 'call_warning'
    call_debug = 'call_debug'
    
class CallSystemMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    
    call_id = db.Column(db.Integer, db.ForeignKey('call.id'), nullable=False)
    call = db.relationship('Call', backref='system_messages')

    type = db.Column(db.Enum(CallSystemMessageType), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Phone numbers that call us or we call
class ExternalPhoneNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    
