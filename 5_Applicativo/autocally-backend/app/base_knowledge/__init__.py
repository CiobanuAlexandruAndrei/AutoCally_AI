from flask import Blueprint

base_knowledge = Blueprint('base-knowledge', __name__)

from . import routes, models, forms, serializers