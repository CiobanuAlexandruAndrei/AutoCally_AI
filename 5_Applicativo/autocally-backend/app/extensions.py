from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
ma = Marshmallow()

# Create a single SocketIO instance to be shared across the application
socketio = SocketIO(
    async_mode='eventlet',
    cors_allowed_origins='*',
    path='/socket.io',
    always_connect=True,
    ping_timeout=60,
    ping_interval=25,
    engineio_logger=False,
    logger=False,
    secure=True,
)
