from flask import Blueprint

phone_numbers = Blueprint('phone-numbers', __name__)

from . import routes, models, forms, serializers