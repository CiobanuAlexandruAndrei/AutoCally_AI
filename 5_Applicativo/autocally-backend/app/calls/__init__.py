from flask import Blueprint

calls = Blueprint('calls', __name__)

from . import routes, models, forms, serializers, test_call_routes