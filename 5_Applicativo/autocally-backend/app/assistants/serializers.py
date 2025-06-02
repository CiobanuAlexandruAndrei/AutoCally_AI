from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from .models import Assistant

class AssistantSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Assistant
        load_instance = True
        include_fk = True  # This will include foreign keys like phone_number_id
