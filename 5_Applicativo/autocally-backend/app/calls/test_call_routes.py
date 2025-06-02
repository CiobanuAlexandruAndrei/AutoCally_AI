from flask import jsonify, request
from . import calls
from ..security.routes import auth
from .models import Call, CallType, ConversationTranscript, ConversationRole
from ..phone_numbers.models import PhoneNumber
from ..extensions import db
from datetime import datetime
from .socket_events import socketio, active_calls, handle_tts
from libs.assistant.assistant_llm import AssistantLLM
from libs.assistant.text_to_speech import TTS
from libs.assistant.speech_to_text import SpeechToText
import logging
import time
from threading import Thread
import eventlet

@calls.route('test-call/start', methods=['POST'])
@auth.login_required
def start_test_call():
    try:
        data = request.get_json()
        phone_number_id = data.get('phone_number_id')

        logging.warning(f"📞 [TEST-CALL] Starting test call with phone_number_id {phone_number_id}")

        if not phone_number_id:
            logging.error(f"❌ [ERROR] Phone number ID is required")
            return jsonify({'error': 'Phone number ID is required'}), 400

        # Verify phone number exists and is available
        phone_number = PhoneNumber.query.get(phone_number_id)
        if not phone_number:
            logging.error(f"❌ [ERROR] Phone number not found with ID {phone_number_id}")
            return jsonify({'error': 'Phone number not found'}), 404

        # Create a new call record
        new_call = Call(
            call_sid=f"test-{datetime.utcnow().timestamp()}",
            phone_number_id=phone_number_id,
            call_type=CallType.test,
            status='initiated',
            direction='outbound',
            started_at=datetime.utcnow()
        )
        
        db.session.add(new_call)
        db.session.commit()
        logging.warning(f"📞 [TEST-CALL] Created new call record with ID {new_call.id}")

        # Get the assistant from the phone number's assistants collection
        if not phone_number.assistants or len(phone_number.assistants) == 0:
            logging.error(f"❌ [ERROR] No assistants associated with phone number {phone_number_id}")
            return jsonify({'error': 'No assistant is associated with this phone number'}), 400
            
        # Use the first assistant associated with this phone number
        assistant = phone_number.assistants[0]
        logging.warning(f"🤖 [LLM] Using assistant {assistant.id} ({assistant.name if hasattr(assistant, 'name') else 'unnamed'}) for test call")
        
        # Initialize call components in active_calls cache - IMPORTANT: client_sid starts as None
        call_id_str = str(new_call.id)
        active_calls[call_id_str] = {
            'assistant_llm': AssistantLLM(assistant.id),
            'tts': TTS(assistant.id),
            'stt': SpeechToText(assistant.id),
            'is_speaking': False,
            'client_sid': None,  # Initialize as None, will be updated when client connects
            'pending_audio': [],  # Initialize empty pending audio list
            'is_greeting_audio': True,  # Mark that next audio will be greeting
            'call_started_time': datetime.utcnow().timestamp()  # Add timestamp for tracking
        }
        logging.warning(f"📞 [TEST-CALL] Initialized components for call {new_call.id}")

        # Store greeting as assistant message
        greeting = "Hello! How can I help you today?"
        transcript = ConversationTranscript(
            call_id=new_call.id,
            transcript=greeting,
            role=ConversationRole.assistant,
            created_at=datetime.utcnow()
        )
        db.session.add(transcript)
        db.session.commit()

        # Generate and store greeting for later delivery
        logging.warning(f"📞 [TEST-CALL] Generating greeting for call {new_call.id}")
        
        # Use a short delay before generating audio to give client time to connect
        def delayed_greeting_generation():
            # Check if client has connected yet
            if call_id_str in active_calls:
                call_data = active_calls[call_id_str]
                client_sid = call_data.get('client_sid')
                
                if client_sid:
                    logging.warning(f"📞 [TEST-CALL] Client {client_sid} already connected, generating greeting")
                else:
                    logging.warning(f"📞 [TEST-CALL] No client connected yet for call {call_id_str}, will store greeting for later")
                    
                # Generate greeting regardless - it will be delivered when client connects
                handle_tts(call_id_str, greeting, thread_safe=True)
        
        # Use a 1-second delay to give client time to connect
        eventlet.spawn_after(1.0, delayed_greeting_generation)
        
        logging.warning(f"📞 [TEST-CALL] Greeting preparation scheduled for call {new_call.id}")

        return jsonify({
            'status': 'success',
            'call_id': new_call.id,
            'phone_number_id': phone_number.id
        })

    except Exception as e:
        logging.error(f"❌ [ERROR] Error starting test call: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@calls.route('test-call/end', methods=['POST'])
@auth.login_required
def end_test_call():
    try:
        data = request.get_json()
        call_id = data.get('call_id')
        
        if not call_id:
            return jsonify({'error': 'Missing call_id'}), 400
            
        # Get the call
        call = Call.query.get(call_id)
        if not call:
            return jsonify({'error': 'Call not found'}), 404
            
        # Update call status
        call.status = 'completed'
        call.ended_at = datetime.utcnow()
        db.session.commit()
        
        # Clean up active calls cache
        call_id_str = str(call_id)
        if call_id_str in active_calls:
            del active_calls[call_id_str]
        
        # Emit call_ended event to socket
        socketio.emit('call_ended', {'call_id': call_id})
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@calls.route('test-call/available-phone-numbers', methods=['GET'])
@auth.login_required
def get_test_call_available_phone_numbers():
    try:
        logging.info("Fetching available phone numbers")
        
        # Get current user's profile
        current_user = auth.current_user()
        current_profile = current_user.profile
        
        if not current_profile:
            logging.error("No profile found for current user")
            return jsonify({'error': 'No profile found for user'}), 400
        
        # Get phone numbers for current user's profile
        phone_numbers = PhoneNumber.query.filter_by(profile_id=current_profile.id).all()
        logging.info(f"Found {len(phone_numbers)} phone numbers for profile {current_profile.id}")
        
        # Format the response
        phone_numbers_data = [{
            'id': phone.id,
            'phone_number': phone.phone_number,
            'assistants': [{'id': assistant.id, 'name': assistant.name} for assistant in phone.assistants],
            'name': phone.phone_number  # Using phone number as name since there's no name field
        } for phone in phone_numbers]
        
        logging.info("Successfully formatted phone numbers data")
        return jsonify({
            'status': 'success',
            'phone_numbers': phone_numbers_data
        })
        
    except Exception as e:
        logging.error(f"Error in get_test_call_available_phone_numbers: {str(e)}")
        logging.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500 