from flask import Flask
from .config import Config
from .extensions import db, migrate, cors, ma, socketio
from flask_wtf.csrf import CSRFProtect
from .security.routes import create_default_user


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = 'b5065f35e6b34d18ba2a3b86ae1d9675'

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})
    ma.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet', ping_timeout=60, ping_interval=25)


    with app.app_context():
        from .security import security as security_blueprint
        from .phone_numbers import phone_numbers as phone_numbers_blueprint
        from .assistants import assistants as assistants_blueprint
        from .base_knowledge import base_knowledge as base_knowledge_blueprint
        from .calls import calls as calls_blueprint
        
        app.register_blueprint(security_blueprint, url_prefix='/api/security')
        app.register_blueprint(phone_numbers_blueprint, url_prefix='/api/phone-numbers')
        app.register_blueprint(assistants_blueprint, url_prefix='/api/assistants')
        app.register_blueprint(base_knowledge_blueprint, url_prefix='/api/base-knowledge')
        app.register_blueprint(calls_blueprint, url_prefix='/api/calls')
        
        db.create_all()
        create_default_user()

    return app