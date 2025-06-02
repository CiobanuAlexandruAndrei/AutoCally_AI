#!/bin/bash

echo "Starting Flask application with Socket.IO and SSL support..."

# Install necessary packages if they're not already installed
pip install pyopenssl eventlet flask-socketio

# Ensure we're in the correct directory
cd /app

# Print environment for debugging
echo "Environment variables:"
echo "FLASK_ENV: $FLASK_ENV" 
echo "SSL_CERT_PATH: $SSL_CERT_PATH"
echo "SSL_KEY_PATH: $SSL_KEY_PATH"
echo "CORS_ORIGINS: $CORS_ORIGINS"
echo "PWD: $(pwd)"
echo "Contents of current directory:"
ls -la

# Check for certificates using environment variables
echo "Checking for SSL certificates..."
if [ -f "$SSL_CERT_PATH" ] && [ -f "$SSL_KEY_PATH" ]; then
    echo "Found SSL certificates:"
    ls -la $SSL_CERT_PATH $SSL_KEY_PATH
else
    echo "Looking for certificates in standard locations..."
    if [ -f "server.cert" ] && [ -f "server.key" ]; then
        echo "Found certificates in current directory"
        export SSL_CERT_PATH="server.cert"
        export SSL_KEY_PATH="server.key"
    elif [ -f "certs/server.cert" ] && [ -f "certs/server.key" ]; then
        echo "Found certificates in certs directory"
        export SSL_CERT_PATH="certs/server.cert"
        export SSL_KEY_PATH="certs/server.key"
    else
        echo "No SSL certificates found. Will run in HTTP mode only."
    fi
fi

# Check CORS origins setting
if [ -z "$CORS_ORIGINS" ]; then
    echo "WARNING: CORS_ORIGINS not set, using wildcard '*' (not recommended for production)"
    export CORS_ORIGINS="*"
fi

# Create simple health check endpoint for testing
mkdir -p app/security

cat > app/security/health.py << EOF
from . import security
from flask import jsonify

@security.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'Backend service is running'
    })
EOF

# Run the Flask application using run.py
echo "Starting Flask application with run.py..."
python run.py 