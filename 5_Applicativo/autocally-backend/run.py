import eventlet
eventlet.monkey_patch()  # This should be FIRST import

from dotenv import load_dotenv
load_dotenv()

import logging

# Configure logging to show all levels for websocket-related loggers
logging.basicConfig(level=logging.DEBUG)  # Change to DEBUG level

# Configure specific loggers
logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)
logging.getLogger('werkzeug').setLevel(logging.DEBUG)
logging.getLogger('eventlet').setLevel(logging.DEBUG)

# Keep the custom logger for our app
app_logger = logging.getLogger('app')
app_logger.setLevel(logging.INFO)

# Remove or comment out this block that was silencing the loggers
"""
for logger_name in ['socketio', 'engineio', 'werkzeug', 'eventlet']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)
"""

from app import create_app
from app.extensions import socketio
import os

app = create_app()

if __name__ == "__main__":
    cert_dir = os.path.join(os.path.dirname(__file__), 'certs')
    ssl_context = (
        os.path.join(cert_dir, 'server.cert'),
        os.path.join(cert_dir, 'server.key')
    )
    
    # Set debug to True to see more logs
    socketio.run(
        app,
        debug=True,  # Changed to True
        host='0.0.0.0',
        port=5000,
        ssl_context=ssl_context
    )