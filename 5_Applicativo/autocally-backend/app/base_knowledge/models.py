from ..extensions import db
from ..assistants.models import Assistant

assistant_base_knowledge = db.Table('assistant_base_knowledge',
    db.Column('assistant_id', db.Integer, db.ForeignKey('assistant.id'), primary_key=True),
    db.Column('base_knowledge_id', db.Integer, db.ForeignKey('base_knowledge.id'), primary_key=True)
)

class BaseKnowledge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    last_loaded = db.Column(db.DateTime, nullable=True)
    needs_reload = db.Column(db.Boolean, default=False)

    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    profile = db.relationship('Profile', backref='base_knowledge')

    folder_path = db.Column(db.String(256), nullable=False)

    files = db.relationship('BaseKnowledgeFile', backref='parent_knowledge', lazy=True)

    assistants = db.relationship('Assistant', secondary=assistant_base_knowledge, 
                               backref=db.backref('knowledge_bases', lazy='dynamic'))


class BaseKnowledgeFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    base_knowledge_id = db.Column(db.Integer, db.ForeignKey('base_knowledge.id'), nullable=False)
    base_knowledge = db.relationship('BaseKnowledge', backref='knowledge_files')

    file_path = db.Column(db.String(256), nullable=False)
    file_type = db.Column(db.String(128), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)


class TaskStatusBaseKnowledge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(128), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False)  # PENDING, STARTED, SUCCESS, FAILURE
    progress = db.Column(db.Integer, default=0)  # Progress from 0 to total_steps
    total_steps = db.Column(db.Integer, default=4)  # Total number of steps
    status_message = db.Column(db.String(255))  # Current status message
    result = db.Column(db.JSON, nullable=True)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    base_knowledge_id = db.Column(db.Integer, db.ForeignKey('base_knowledge.id'))


