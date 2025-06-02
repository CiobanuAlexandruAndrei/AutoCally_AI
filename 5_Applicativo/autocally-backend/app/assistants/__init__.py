from flask import Blueprint

assistants = Blueprint('assistants', __name__)

from . import routes, models, forms, serializers
