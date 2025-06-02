import uuid
from flask import jsonify, request, Response, current_app
from flask_httpauth import HTTPTokenAuth
from . import assistants
from ..extensions import db
from .models import Assistant
from ..security.routes import auth
from .serializers import AssistantSchema
from libs.assistant.assistant_llm import AssistantLLM
import flask
import asyncio
import requests
import os
from libs.assistant.get_voices import get_voices_print
from dotenv import load_dotenv
import eventlet

load_dotenv()

assistant_schema = AssistantSchema()
assistants_schema = AssistantSchema(many=True)


assistant_llm_cache = {}

@assistants.route('/create', methods=['POST'])
@auth.login_required
def create_assistant():
    data = request.get_json()
    current_user = auth.current_user()
    current_profile = current_user.profile

    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400

    name = data.get('name')
    if not name:
        name = 'New Assistant ' + str(uuid.uuid4())
        
    new_assistant = Assistant(
        name=name,
        prompt=data.get('prompt'),
        greeting_message=data.get('greeting_message'),
        cartesia_voice_id=data.get('cartesia_voice_id'),
        phone_number_id=data.get('phone_number_id'),
        profile_id=current_profile.id,
        llm_model=data.get('llm_model', "llama-3.3-70b-versatile"),
        llm_temperature=data.get('llm_temperature', 0.0),
        llm_max_tokens=data.get('llm_max_tokens', 100)
    )
    
    db.session.add(new_assistant)
    db.session.commit()
    
    return jsonify({
        'message': 'Assistant created successfully',
        'assistant': {
            'id': new_assistant.id,
            'name': new_assistant.name,
            'prompt': new_assistant.prompt,
            'greeting_message': new_assistant.greeting_message,
            'cartesia_voice_id': new_assistant.cartesia_voice_id,
            'phone_number_id': new_assistant.phone_number_id,
            'llm_model': new_assistant.llm_model,
            'llm_temperature': new_assistant.llm_temperature,
            'llm_max_tokens': new_assistant.llm_max_tokens
        }
    }), 201


@assistants.route('/delete/<int:assistant_id>', methods=['DELETE'])
@auth.login_required
def delete_assistant(assistant_id):
    print('delete_assistant', assistant_id)
    print('request', request)

    try:
        current_user = auth.current_user()
        current_profile = current_user.profile
        
        if not current_profile:
            return jsonify({'error': 'No profile found for user'}), 400
            
        assistant = Assistant.query.get_or_404(assistant_id)
        
        if assistant.profile_id != current_profile.id:
            return jsonify({'error': 'Unauthorized access'}), 403
            
        db.session.delete(assistant)
        db.session.commit()
        
        return jsonify({'message': 'Assistant deleted successfully'}), 200
    except Exception as e:
        print('error', e)
        return jsonify({'error': str(e)}), 500


@assistants.route('/', methods=['GET'])
@auth.login_required
def get_assistants():
    try:
        current_user = auth.current_user()
        current_profile = current_user.profile
        
        if not current_profile:
            return jsonify({'error': 'No profile found for user'}), 400
            
        all_assistants = Assistant.query.filter_by(profile_id=current_profile.id).all()
        result = assistants_schema.dump(all_assistants)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@assistants.route('/<int:assistant_id>', methods=['GET'])
@auth.login_required
def get_assistant(assistant_id):
    try:
        current_profile = auth.current_user().profile
        assistant = Assistant.query.get(assistant_id)
        
        if not assistant:
            return jsonify({'error': 'Assistant not found'}), 404
            
        if assistant.profile_id != current_profile.id:
            return jsonify({'error': 'Unauthorized access'}), 403
            
        result = assistant_schema.dump(assistant)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@assistants.route('/update/<int:assistant_id>', methods=['PUT'])
@auth.login_required
def update_assistant(assistant_id):
    print('update_assistant', assistant_id)
    print('request', request)

    current_profile = auth.current_user().profile
    assistant = Assistant.query.get_or_404(assistant_id)
    
    if assistant.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    data = request.get_json()
    
    if 'name' in data:
        assistant.name = data['name']
    if 'prompt' in data:
        assistant.prompt = data['prompt']
    if 'greeting_message' in data:
        assistant.greeting_message = data['greeting_message']
    if 'cartesia_voice_id' in data:
        assistant.cartesia_voice_id = data['cartesia_voice_id']
    if 'phone_number_id' in data:
        assistant.phone_number_id = data['phone_number_id']
    if 'llm_model' in data:
        assistant.llm_model = data['llm_model']
    if 'llm_temperature' in data:
        assistant.llm_temperature = data['llm_temperature']
    if 'llm_max_tokens' in data:
        assistant.llm_max_tokens = data['llm_max_tokens']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Assistant updated successfully',
        'assistant': {
            'id': assistant.id,
            'name': assistant.name,
            'prompt': assistant.prompt,
            'greeting_message': assistant.greeting_message,
            'cartesia_voice_id': assistant.cartesia_voice_id,
            'phone_number_id': assistant.phone_number_id,
            'llm_model': assistant.llm_model,
            'llm_temperature': assistant.llm_temperature,
            'llm_max_tokens': assistant.llm_max_tokens
        }
    })


@assistants.route('/voices', methods=['GET'])
@auth.login_required
def get_voices():
    try:
        def fetch_voices():
            return requests.get(
                "https://api.cartesia.ai/voices/",
                params={},
                headers={
                    "X-API-Key": os.getenv('CARTESIA_API_KEY'),
                    "Cartesia-Version": "2024-06-10"
                },
            )

        pool = eventlet.GreenPool()
        response = pool.spawn(fetch_voices).wait()
        
        if response.status_code == 200:
            voices = response.json()

            """ Debug logging
            for voice in voices[:3]:
                print(f"Voice ID: {voice.get('id')}")
                print(f"Name: {voice.get('name')}")
                print(f"Language: {voice.get('language')}")
                print("-" * 30) """

            return jsonify([{
                'id': voice.get('id'),
                'name': voice.get('name'), 
                'description': voice.get('description'),
                'language': voice.get('language'),
                'gender': voice.get('gender'),
            } for voice in voices]), 200

        else:
            return jsonify({'error': f'Error fetching voices: {response.text}'}), response.status_code
            
    except Exception as e:
        print(f"Error in get_voices: {str(e)}")
        return jsonify({'error': str(e)}), 500
