import logging
from flask import request, session, current_app
from . import socketio
import json
import time

logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    """Handle socket.io connection event with detailed diagnostics"""
    client_id = request.sid
    
    # More detailed logging for debugging
    headers = dict(request.headers)
    # Sanitize headers for logging (remove potentially sensitive info)
    if 'Cookie' in headers:
        headers['Cookie'] = '[REDACTED]'
    if 'Authorization' in headers:
        headers['Authorization'] = '[REDACTED]'
    
    # Log detailed connection info
    logger.info(f"Socket.IO client connected: {client_id}")
    logger.info(f"Connection details - Transport: {request.environ.get('wsgi.url_scheme', 'unknown')}")
    logger.info(f"Connection headers: {json.dumps(headers)}")
    logger.info(f"Origin: {request.origin}")
    logger.info(f"URL scheme: {request.environ.get('wsgi.url_scheme')}")
    
    # Extract the origin for CORS checking
    origin = request.headers.get('Origin', '')
    cors_origins = current_app.config.get('CORS_ORIGINS', '*')
    
    # Log CORS verification
    if cors_origins == '*':
        logger.info(f"CORS is set to wildcard '*', accepting all origins")
    else:
        logger.info(f"Checking if origin '{origin}' is in allowed list: {cors_origins}")
        allowed = origin in cors_origins.split(',')
        logger.info(f"Origin '{origin}' is {'allowed' if allowed else 'NOT allowed'}")
    
    # Acknowledge connection to the client with more info
    socketio.emit('connection_established', {
        'status': 'connected',
        'client_id': client_id,
        'timestamp': time.time(),
        'server_info': {
            'cors_allowed_origins': cors_origins,
            'transport': request.environ.get('wsgi.url_scheme', 'unknown')
        }
    }, to=client_id)
    
    return True

@socketio.on('disconnect')
def handle_disconnect():
    """Handle socket.io disconnect event"""
    client_id = request.sid
    logger.info(f"Client disconnected: {client_id}")

@socketio.on('error')
def handle_error(error):
    """Handle socket.io error event"""
    client_id = request.sid
    logger.error(f"Socket.IO error from client {client_id}: {error}")

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat messages from clients"""
    client_id = request.sid
    logger.info(f"Received message from {client_id}: {data}")
    
    # Echo the message back to the client with some additional info
    response = {
        'content': f"Echo: {data.get('question', '')}",
        'assistant_id': data.get('assistant_id'),
        'status': 'received',
        'message': data,
        'timestamp': time.time()
    }
    
    socketio.emit('chat_response', response, to=client_id)

# Add a health check event to test socket connectivity
@socketio.on('ping_test')
def handle_ping_test(data):
    """Simple ping-pong test for socket connectivity"""
    client_id = request.sid
    logger.info(f"Ping test from client {client_id}")
    
    socketio.emit('pong_test', {
        'message': 'pong',
        'received_data': data,
        'timestamp': time.time()
    }, to=client_id) 