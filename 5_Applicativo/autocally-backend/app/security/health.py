from . import security
from flask import jsonify

@security.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'Backend service is running'
    })
