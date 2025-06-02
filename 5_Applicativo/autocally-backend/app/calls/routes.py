from flask import Blueprint, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from .models import Call, CallType, ConversationTranscript, ConversationRole
from ..phone_numbers.models import PhoneNumber
from ..extensions import db
import logging
from datetime import datetime
from .socket_events import socketio
from . import calls

@calls.route('/incoming-call', methods=['POST'])
def handle_incoming_call():
    try:
        # Get call details from Twilio
        call_sid = request.values.get('CallSid')
        from_number = request.values.get('From')
        to_number = request.values.get('To')
        
        # Find the phone number in our system
        phone_number = PhoneNumber.query.filter_by(phone_number=to_number).first()
        if not phone_number:
            logging.error(f"No phone number found in system for {to_number}")
            return jsonify({'error': 'No phone number found in system'}), 404
        
        # Create call record in database
        call = Call(
            call_sid=call_sid,
            phone_number_id=phone_number.id,
            call_type=CallType.inbound,
            status="in-progress",
            direction="inbound",
            started_at=datetime.utcnow()
        )
        db.session.add(call)
        db.session.commit()
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Start a websocket connection with call info
        response.start().stream(url=f'/socket.io/?call_id={call.id}&phone_number_id={phone_number.id}')
        
        return str(response)
        
    except Exception as e:
        logging.error(f"Error handling incoming call: {str(e)}")
        return jsonify({'error': str(e)}), 500

@calls.route('/call-status', methods=['POST'])
def handle_call_status():
    try:
        call_sid = request.values.get('CallSid')
        call_status = request.values.get('CallStatus')
        
        # Update call status in database
        call = Call.query.filter_by(call_sid=call_sid).first()
        if call:
            call.status = call_status
            
            # If call ended, update end time and clean up websocket connection
            if call_status in ['completed', 'busy', 'failed', 'no-answer', 'canceled']:
                call.ended_at = datetime.utcnow()
                socketio.emit('call_ended', {'call_id': call.id})
                
            db.session.commit()
                
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logging.error(f"Error handling call status: {str(e)}")
        return jsonify({'error': str(e)}), 500
