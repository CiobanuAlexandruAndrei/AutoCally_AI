from ..phone_numbers.models import PhoneNumber
from libs.assistant.assistant_llm import AssistantLLM
from libs.assistant.text_to_speech import TTS
from libs.assistant.speech_to_text import SpeechToText
from ..security.routes import auth
from ..extensions import db, socketio
from flask import request, current_app
import logging
import time
import asyncio
import eventlet
from eventlet import spawn_after
from datetime import datetime
import numpy as np
from flask_socketio import emit
from .models import Call, ConversationTranscript, ConversationRole, CallSystemMessage, CallSystemMessageType

# We're using the socketio instance from extensions to avoid circular imports
# This is the same instance used in assistants/socket_events.py

eventlet.monkey_patch()

# Cache for active calls - simplified structure
active_calls = {}

@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connections - simplified like in assistants."""
    # Get call_id from query parameters
    call_id = request.args.get('call_id')
    phone_number_id = request.args.get('phone_number_id')
    
    logging.warning(f"🔌 [SOCKET] Connection parameters: call_id={call_id}, phone_number_id={phone_number_id}")
    
    # Always emit connection established event
    socketio.emit('connection_established', {
        'status': 'connected',
        'call_id': call_id
    })
    
    # Check if we're reconnecting to an active call
    if call_id and call_id in active_calls:
        call_data = active_calls[call_id]
        call_data['last_seen'] = time.time()  # Track when we last saw this client
        
        # Send call_ready to confirm the connection
        socketio.emit('call_ready', {
            'call_id': call_id,
            'phone_number_id': phone_number_id
        })
        
        # If there's pending audio, deliver it with a small delay to ensure client is ready
        if 'pending_audio' in call_data and call_data['pending_audio']:
            logging.warning(f"🔌 [SOCKET] Found pending audio for call {call_id}, scheduling delivery")
            # Use a small delay to make sure client is ready to receive
            eventlet.spawn_after(0.5, deliver_pending_audio, call_id)

def ping_client(call_id):
    """Send periodic pings to verify connection."""
    try:
        if call_id not in active_calls:
            return
            
        call_data = active_calls[call_id]
        
        # Send a ping
        socketio.emit('server_ping', {
            'timestamp': time.time(),
            'call_id': call_id
        })
        
        # Update last seen time
        call_data['last_seen'] = time.time()
        
        # Schedule next ping
        eventlet.spawn_after(5.0, ping_client, call_id)
            
    except Exception as e:
        logging.error(f"❌ [ERROR] Error in ping_client: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    logging.warning("🔌 [SOCKET] Client disconnected")

def deliver_pending_audio(call_id):
    """Deliver any pending audio chunks."""
    try:
        if call_id not in active_calls:
            logging.warning(f"❌ [AUDIO] Cannot deliver pending audio: call {call_id} not in active calls")
            return
            
        call_data = active_calls[call_id]
        if 'pending_audio' not in call_data or not call_data['pending_audio']:
            logging.warning(f"❌ [AUDIO] No pending audio found for call {call_id}")
            return
            
        pending_audio = call_data['pending_audio']
        is_greeting = call_data.get('is_greeting_audio', False)
        audio_format = call_data.get('audio_format', 'pcm_f32le')
        
        logging.warning(f"🔊 [AUDIO] Attempting to deliver {len(pending_audio)} pending chunks for call {call_id}")
        
        chunks_sent = 0
        for chunk in pending_audio:
            if not chunk:
                logging.warning(f"❌ [AUDIO] Empty chunk, skipping")
                continue
                
            try:
                audio_data = {
                    'call_id': call_id,
                    'audio': {
                        'data': chunk,
                        'format': 'raw',
                        'encoding': audio_format,
                        'sample_rate': 22050
                    },
                    'is_greeting': is_greeting,
                    'final': False
                }
                
                socketio.emit('audio_chunk', audio_data)
                chunks_sent += 1
                
                # Calculate appropriate delay based on audio chunk length
                # For PCM_F32LE format, each sample is 4 bytes (32 bits)
                # So the duration is (bytes / 4) / sample_rate
                chunk_duration = len(chunk) / 4 / 22050  # duration in seconds
                
                # Add a small buffer to ensure smooth playback (90% of the actual duration)
                sleep_time = chunk_duration * 0.9
                
                logging.debug(f"🔊 [AUDIO] Chunk size: {len(chunk)} bytes, duration: {chunk_duration:.4f}s, sleeping for {sleep_time:.4f}s")
                eventlet.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"❌ [AUDIO] Error sending pending chunk: {str(e)}")
        
        # Only clear pending audio if we sent all chunks
        if chunks_sent == len(pending_audio):
            call_data['pending_audio'] = []
            logging.info(f"🔊 [AUDIO] All pending chunks sent, cleared pending audio")
        else:
            logging.warning(f"❌ [AUDIO] Only sent {chunks_sent}/{len(pending_audio)} chunks")
        
        # Send completion marker
        try:
            socketio.emit('audio_chunk', {
                'call_id': call_id,
                'final': True,
                'chunks_sent': chunks_sent,
                'is_greeting': is_greeting
            })
            
            logging.warning(f"🔊 [AUDIO] Completed delivery of {chunks_sent} pending chunks")
        except Exception as e:
            logging.error(f"❌ [AUDIO] Error sending final marker: {str(e)}")
        
    except Exception as e:
        logging.error(f"🔊 [AUDIO] Error in pending audio delivery: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

@socketio.on('call_started')
def handle_call_started(data):
    """Handle call started event - simplified approach."""
    try:
        call_id = data.get('call_id')
        phone_number_id = data.get('phone_number_id')
        
        logging.warning(f"📞 [CALL] Starting call with ID {call_id} and phone_number_id {phone_number_id}")
        
        if not call_id or not phone_number_id:
            socketio.emit('error', {'message': 'Missing call_id or phone_number_id'})
            return
            
        # Get call and phone number from the database
        call = Call.query.get_or_404(call_id)
        phone_number = PhoneNumber.query.get_or_404(phone_number_id)
        
        # Initialize call components or update existing call data
        if str(call_id) in active_calls:
            # Update existing call data
            call_data = active_calls[str(call_id)]
            call_data['last_seen'] = time.time()  # Update last seen time
            logging.warning(f"📞 [CALL] Reconnected to existing call {call_id}")
        else:
            # Initialize call components
            assistant_id = None
            if phone_number.assistants and len(phone_number.assistants) > 0:
                assistant_id = phone_number.assistants[0].id
            
            if not assistant_id:
                socketio.emit('error', {'message': 'No assistant associated with this phone number'})
                return
            
            active_calls[str(call_id)] = {
                'assistant_llm': AssistantLLM(assistant_id),
                'tts': TTS(assistant_id),
                'stt': SpeechToText(assistant_id),
                'is_speaking': False,
                'pending_audio': [],
                'greeting_sent': False,  # Track if greeting has been sent
                'last_seen': time.time()
            }
            
            logging.warning(f"📞 [CALL] Initialized new call {call_id}")
        
        # Send call ready event
        socketio.emit('call_ready', {
            'call_id': call_id,
            'phone_number_id': phone_number_id
        })
        
        # Get reference to the call data
        call_data = active_calls[str(call_id)]
        
        # Check for pending audio
        if len(call_data.get('pending_audio', [])) > 0:
            logging.warning(f"📞 [CALL] Found {len(call_data['pending_audio'])} pending audio chunks, scheduling delivery")
            eventlet.spawn_after(0.5, deliver_pending_audio, str(call_id))
            return
            
        # If no pending audio and greeting not sent, start with a greeting
        if not call_data.get('greeting_sent', False):
            # Get the assistant associated with this phone number
            assistant_id = None
            if phone_number.assistants and len(phone_number.assistants) > 0:
                assistant_id = phone_number.assistants[0].id
            
            # Default greeting in case we don't have a custom one
            default_greeting = "Ciao sono il tuo assistente virtuale, come posso aiutarti oggi?"
            greeting = default_greeting
            
            # If we have an assistant, try to get a custom greeting
            if assistant_id:
                from ..assistants.models import Assistant
                assistant = Assistant.query.get(assistant_id)
                if assistant and assistant.greeting_message:
                    greeting = assistant.greeting_message
                    logging.info(f"📞 [CALL] Using custom greeting for assistant {assistant_id}: {greeting[:50]}...")
                else:
                    logging.info(f"📞 [CALL] No custom greeting found for assistant {assistant_id}, using default")
            else:
                logging.warning(f"📞 [CALL] No assistant associated with phone number {phone_number_id}, using default greeting")
            
            # Store greeting transcript in the database within this request context
            transcript = ConversationTranscript(
                call_id=call.id,
                transcript=greeting,
                role=ConversationRole.assistant,
                created_at=datetime.utcnow()
            )
            db.session.add(transcript)
            db.session.commit()
            
            # Mark greeting as sent to prevent duplicate greetings
            call_data['greeting_sent'] = True
            
            # Process greeting in a separate thread (audio only)
            eventlet.spawn(process_greeting, str(call_id), greeting)
            logging.warning(f"📞 [CALL] Greeting scheduled for call {call_id}")
        else:
            logging.warning(f"📞 [CALL] Greeting already sent for call {call_id}, skipping")
        
    except Exception as e:
        logging.error(f"❌ [ERROR] Exception in call_started handler: {str(e)}")
        socketio.emit('error', {'message': str(e)})

def process_greeting(call_id, greeting):
    """Process greeting in a separate thread - audio generation and delivery only."""
    try:
        # Skip if the call no longer exists
        if call_id not in active_calls:
            logging.warning(f"❌ [AUDIO] Cannot process greeting: call {call_id} not found")
            return
            
        call_data = active_calls[call_id]
        
        # Check if already speaking (prevent duplicate audio streaming)
        if call_data.get('is_speaking', False):
            logging.warning(f"❌ [AUDIO] Cannot process greeting: already speaking for call {call_id}")
            return
            
        # Mark as speaking to prevent duplicate audio streaming
        call_data['is_speaking'] = True
        
        greeting_start_time = time.time()
        tts = call_data['tts']
        
        logging.info(f"🔊 [AUDIO] Starting TTS for call {call_id}")
        
        try:
            audio_stream = tts.get_audio_stream(greeting)
            
            # Stream audio chunks immediately as they're generated
            first_chunk = True
            first_chunk_time = time.time() - greeting_start_time
            chunks_sent = 0
            
            for chunk in audio_stream:
                if chunk and len(chunk) > 0:
                    try:
                        audio_data = {
                            'call_id': call_id,
                            'audio': {
                                'data': chunk,
                                'format': 'raw',
                                'encoding': 'pcm_f32le',
                                'sample_rate': 22050
                            },
                            'is_greeting': True,
                            'final': False
                        }
                        
                        if first_chunk:
                            audio_data['first_chunk_time'] = first_chunk_time
                            first_chunk = False
                            logging.info(f"🔊 [AUDIO] Sending first greeting chunk with size {len(chunk)} bytes")
                        
                        socketio.emit('audio_chunk', audio_data)
                        chunks_sent += 1
                        
                        # Calculate appropriate delay based on audio chunk length
                        # For PCM_F32LE format, each sample is 4 bytes (32 bits)
                        # So the duration is (bytes / 4) / sample_rate
                        chunk_duration = len(chunk) / 4 / 22050  # duration in seconds
                        
                        # Add a small buffer to ensure smooth playback (90% of the actual duration)
                        sleep_time = chunk_duration * 0.9
                        
                        logging.debug(f"🔊 [AUDIO] Chunk size: {len(chunk)} bytes, duration: {chunk_duration:.4f}s, sleeping for {sleep_time:.4f}s")
                        eventlet.sleep(sleep_time)
                        
                    except Exception as e:
                        logging.error(f"❌ [AUDIO] Error sending chunk: {str(e)}")
            
            # Send completion marker after all chunks
            try:
                socketio.emit('audio_chunk', {
                    'call_id': call_id,
                    'final': True,
                    'chunks_sent': chunks_sent,
                    'is_greeting': True
                })
                logging.info(f"🔊 [AUDIO] Successfully completed greeting audio delivery for call {call_id}")
            except Exception as e:
                logging.error(f"❌ [AUDIO] Error sending final marker: {str(e)}")
                
        finally:
            # Reset speaking state regardless of success or failure
            if call_id in active_calls:
                active_calls[call_id]['is_speaking'] = False
                
    except Exception as e:
        logging.error(f"❌ [ERROR] Error processing greeting: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

@socketio.on('start_stt')
def handle_start_stt(data):
    """Handle start STT event for continuous audio stream processing."""
    try:
        call_id = data.get('call_id')
        
        if not call_id:
            socketio.emit('error', {'message': 'Missing call_id'})
            return
            
        if call_id not in active_calls:
            socketio.emit('error', {'message': 'Call not found'})
            return
            
        call_data = active_calls[call_id]
        speech_to_text = call_data['stt']
        
        logging.info(f"🎤 [STT] Starting speech-to-text stream for call {call_id}")
        
        def start_stt_stream():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(speech_to_text.start_stream())
                socketio.emit('stt_started', {'status': 'ready', 'call_id': call_id})
                logging.info(f"🎤 [STT] Speech recognition started successfully for call {call_id}")
            except Exception as e:
                logging.error(f"Error starting STT stream: {str(e)}")
                socketio.emit('error', {'message': str(e)})
            finally:
                loop.close()
        
        eventlet.spawn(start_stt_stream)
        
    except Exception as e:
        logging.error(f"Error in start_stt: {str(e)}")
        socketio.emit('error', {'message': str(e)})

@socketio.on('stt_audio_chunk')
def handle_audio_chunk(data):
    """Handle continuous audio chunks for STT processing."""
    try:
        call_id = data.get('call_id')
        audio_data = data.get('audio')
        sample_rate = data.get('sample_rate', 16000)
        format = data.get('format', 'linear16')
        
        if not call_id or not audio_data:
            return
            
        if call_id in active_calls:
            call_data = active_calls[call_id]
            speech_to_text = call_data['stt']
            
            # Process the chunk in a non-blocking way
            eventlet.spawn(process_audio_chunk, speech_to_text, audio_data, call_id, sample_rate, format)
        else:
            logging.warning(f"Call {call_id} not found in active calls")
            
    except Exception as e:
        logging.error(f"Exception in handle_audio_chunk: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

@socketio.on('stop_stt')
def handle_stop_stt(data):
    """Handle stopping the STT stream properly."""
    try:
        call_id = data.get('call_id')
        
        if not call_id:
            socketio.emit('error', {'message': 'Missing call_id'})
            return
            
        if call_id not in active_calls:
            socketio.emit('error', {'message': 'Call not found'})
            return
        
        logging.info(f"🎤 [STT] Stopping speech recognition for call {call_id}")
        
        call_data = active_calls[call_id]
        speech_to_text = call_data['stt']
        
        def stop_stream_task():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(speech_to_text.stop_stream())
                    logging.info(f"🎤 [STT] Successfully stopped STT stream for call {call_id}")
                finally:
                    loop.close()
            except Exception as e:
                logging.error(f"Error stopping STT stream: {str(e)}")
        
        eventlet.spawn(stop_stream_task)
        socketio.emit('stt_stopped', {'status': 'stopped', 'call_id': call_id})
        
    except Exception as e:
        logging.error(f"Error in stop_stt: {str(e)}")
        socketio.emit('error', {'message': str(e)})

def process_audio_chunk(speech_to_text, audio_data, call_id, sample_rate=16000, format='linear16'):
    """Process audio chunk for STT and generate response with proper error handling."""
    try:
        # Process audio using the SpeechToText process_chunk method
        # This needs to be handled properly since it's an async method
        
        # Create data structure expected by process_chunk
        audio_chunk_data = {
            'audio': audio_data,
            'sample_rate': sample_rate,
            'format': format,
            'call_id': call_id
        }
        
        # Since process_chunk is an async method, we need to run it in an event loop
        def process_in_eventlet():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(speech_to_text.process_chunk(audio_chunk_data))
                    logging.info(f"🎤 [STT] Successfully processed audio chunk for call {call_id}")
                finally:
                    loop.close()
            except Exception as e:
                logging.error(f"Error processing audio in eventlet: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
        
        # Spawn the async processing in an eventlet greenthread
        eventlet.spawn(process_in_eventlet)
        
        # The transcription handling will be done by the SpeechToText class
        # which emits 'stt_transcript' events when transcriptions are available
        
    except Exception as e:
        logging.error(f"Error processing audio chunk: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

def store_transcripts(call_id, caller_text, assistant_text):
    """Store transcripts in database with proper app context."""
    try:
        # Import Flask current_app
        from flask import current_app
        
        # Create a copy to ensure we have a reference to the app
        app = current_app._get_current_object()
        
        with app.app_context():
            # Store in database
            try:
                # Convert call_id to int if it's a string
                db_call_id = int(call_id)
                call = Call.query.get(db_call_id)
                
                if not call:
                    logging.error(f"Call with ID {db_call_id} not found")
                    return
                
                # Add caller transcript
                caller_transcript = ConversationTranscript(
                    call_id=call.id,
                    transcript=caller_text,
                    role=ConversationRole.caller,
                    created_at=datetime.utcnow()
                )
                db.session.add(caller_transcript)
                
                # Store assistant response
                assistant_transcript = ConversationTranscript(
                    call_id=call.id,
                    transcript=assistant_text,
                    role=ConversationRole.assistant,
                    created_at=datetime.utcnow()
                )
                db.session.add(assistant_transcript)
                db.session.commit()
                
                logging.info(f"Stored transcripts for call {call_id}")
            except Exception as e:
                logging.error(f"Database error in store_transcripts: {str(e)}")
                
    except Exception as e:
        logging.error(f"Error in store_transcripts: {str(e)}")

def generate_response_audio(call_id, response):
    """Generate audio for response with improved streaming and state management."""
    try:
        if call_id not in active_calls:
            logging.warning(f"❌ [AUDIO] Cannot generate response audio: call {call_id} not in active calls")
            return
            
        call_data = active_calls[call_id]
        tts = call_data['tts']
        
        # Set speaking state to prevent overlapping audio
        call_data['is_speaking'] = True
        
        logging.info(f"🔊 [AUDIO] Starting response audio generation for call {call_id}")
        
        # Generate and stream audio chunks immediately
        audio_stream = tts.get_audio_stream(response)
        
        chunks_sent = 0
        first_chunk = True
        tts_start_time = time.time()
        
        for chunk in audio_stream:
            if chunk and len(chunk) > 0:
                try:
                    audio_data = {
                        'call_id': call_id,
                        'audio': {
                            'data': chunk,
                            'format': 'raw',
                            'encoding': 'pcm_f32le',
                            'sample_rate': 22050
                        },
                        'is_greeting': False,
                        'final': False
                    }
                    
                    if first_chunk:
                        first_chunk_time = time.time() - tts_start_time
                        audio_data['first_chunk_time'] = first_chunk_time
                        first_chunk = False
                    
                    socketio.emit('audio_chunk', audio_data)
                    chunks_sent += 1
                    
                    # Calculate appropriate delay based on audio chunk length
                    chunk_duration = len(chunk) / 4 / 22050  # duration in seconds
                    sleep_time = chunk_duration * 0.9
                    
                    logging.debug(f"🔊 [AUDIO] Chunk size: {len(chunk)} bytes, duration: {chunk_duration:.4f}s, sleeping for {sleep_time:.4f}s")
                    eventlet.sleep(sleep_time)
                    
                except Exception as e:
                    logging.error(f"❌ [AUDIO] Error sending response chunk: {str(e)}")
        
        # Send completion marker
        try:
            socketio.emit('audio_chunk', {
                'call_id': call_id,
                'final': True,
                'chunks_sent': chunks_sent,
                'is_greeting': False
            })
            
            logging.info(f"🔊 [AUDIO] Successfully completed response audio delivery ({chunks_sent} chunks)")
        except Exception as e:
            logging.error(f"❌ [AUDIO] Error sending final marker: {str(e)}")
        
        # Reset speaking state and check for pending responses
        call_data['is_speaking'] = False
        
        # Process any pending responses
        if 'pending_responses' in call_data and call_data['pending_responses']:
            next_response = call_data['pending_responses'].pop(0)
            logging.info(f"🔊 [AUDIO] Processing pending response for call {call_id}")
            eventlet.spawn_after(0.5, generate_response_audio, call_id, next_response)
            
    except Exception as e:
        logging.error(f"❌ [ERROR] Error generating response audio: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        
        # Make sure we reset the speaking state even on error
        if call_id in active_calls:
            active_calls[call_id]['is_speaking'] = False

@socketio.on('direct_test_audio')
def handle_direct_test_audio():
    """Generate and send a simple test tone."""
    try:
        logging.warning(f"📢 [TEST AUDIO] Generating test tone")
        
        # Generate a simple sine wave test tone (500Hz for 0.5 seconds at 22050Hz sample rate)
        duration = 0.5  # seconds
        sample_rate = 22050
        frequency = 500  # Hz
        
        # Generate the tone
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(2 * np.pi * frequency * t)
        
        # Convert to int16
        tone_int16 = (tone * 32767).astype(np.int16)
        
        # Convert to bytes
        tone_bytes = tone_int16.tobytes()
        
        # Send as single chunk
        audio_data = {
            'call_id': 'test',
            'audio': {
                'data': tone_bytes,
                'format': 'raw'
            },
            'chunk_index': 0,
            'total_chunks': 1,
            'is_test_tone': True,
            'final': False
        }
        
        socketio.emit('audio_chunk', audio_data)
        
        # Send completion marker
        socketio.emit('audio_chunk', {
            'call_id': 'test',
            'final': True,
            'chunks_sent': 1,
            'total_chunks': 1,
            'is_test_tone': True
        })
        
        logging.warning(f"📢 [TEST AUDIO] Test tone sent")
        
    except Exception as e:
        logging.error(f"Error sending test audio: {str(e)}")

@socketio.on('debug_ping')
def handle_debug_ping(data):
    """Simple debug ping handler for testing connection."""
    try:
        logging.warning(f"🐛 [DEBUG] Debug ping received")
        
        # Send response
        socketio.emit('debug_pong', {
            'text': 'Debug pong from server!',
            'timestamp': time.time()
        })
        
        # Also broadcast to all
        socketio.emit('debug_broadcast', {
            'text': 'Test broadcast message',
            'sender': 'server'
        })
        
    except Exception as e:
        logging.error(f"Error in debug_ping handler: {str(e)}")

@socketio.on('simple_test')
def handle_simple_test(data):
    """Super simple test handler for basic connection testing."""
    try:
        logging.warning(f"🔍 [SIMPLE TEST] Received")
        
        socketio.emit('simple_test_response', {
            'text': 'Simple test response from server',
            'timestamp': time.time(),
            'received_data': data
        })
        
    except Exception as e:
        logging.error(f"Error in simple_test handler: {str(e)}")

# Add the missing handle_tts function
def handle_tts(call_id, text, thread_safe=False):
    """Handle text-to-speech generation and delivery."""
    try:
        logging.warning(f"🗣️ [TTS] Generating audio for call {call_id}, text: '{text[:30]}...'")
        
        if call_id not in active_calls:
            logging.error(f"❌ [ERROR] Cannot generate TTS: Call {call_id} not found in active calls")
            return False
        
        # If this is being called from test_call_routes, we need to store the transcript
        # in the database before spawning the thread
        try:
            # Only try to add to database if requested and we have a numeric call_id
            if thread_safe and str(call_id).isdigit():
                # Store transcript first using safe app context handling
                eventlet.spawn(store_assistant_transcript, int(call_id), text)
        except Exception as e:
            logging.error(f"❌ [ERROR] Error storing TTS transcript: {str(e)}")
            
        # Process the audio generation and delivery
        if thread_safe:
            # Use eventlet to spawn in a thread-safe manner
            eventlet.spawn(process_greeting, call_id, text)
            return True
        else:
            # Direct call for simpler contexts
            process_greeting(call_id, text)
            return True
            
    except Exception as e:
        logging.error(f"❌ [ERROR] Error in handle_tts: {str(e)}")
        return False

def store_assistant_transcript(call_id, text):
    """Store assistant transcript with proper app context."""
    try:
        from flask import current_app
        app = current_app._get_current_object()
        
        with app.app_context():
            try:
                call = Call.query.get(call_id)
                if call:
                    transcript = ConversationTranscript(
                        call_id=call.id,
                        transcript=text,
                        role=ConversationRole.assistant,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(transcript)
                    db.session.commit()
                    logging.info(f"Stored assistant transcript for call {call_id}")
                else:
                    logging.error(f"Call with ID {call_id} not found for transcript storage")
            except Exception as e:
                logging.error(f"Database error in store_assistant_transcript: {str(e)}")
    except Exception as e:
        logging.error(f"Error in store_assistant_transcript: {str(e)}")

@socketio.on('request_audio')
def handle_request_audio(data):
    """Handle client request for any pending audio."""
    try:
        client_sid = "1234"  # Fixed client SID
        call_id = data.get('call_id')
        
        if not call_id:
            logging.warning("❌ [AUDIO] Missing call_id in request_audio event")
            return
        
        logging.warning(f"🔊 [AUDIO] Client {client_sid} explicitly requested audio for call {call_id}")
        
        # Check if call exists
        if call_id not in active_calls:
            logging.warning(f"❌ [AUDIO] Cannot deliver audio: call {call_id} not found")
            socketio.emit('test_audio_result', {
                'success': False,
                'message': 'Call not found'
            })
            return
        
        call_data = active_calls[call_id]
        
        # Check for pending audio
        if 'pending_audio' in call_data and call_data['pending_audio']:
            pending_count = len(call_data['pending_audio'])
            logging.warning(f"🔊 [AUDIO] Found {pending_count} pending chunks for call {call_id}")
            
            # Use eventlet to spawn delivery with a slight delay to ensure connection is ready
            eventlet.spawn_after(0.1, deliver_pending_audio, str(call_id))
            
            socketio.emit('test_audio_result', {
                'success': True,
                'message': 'Delivering pending audio',
                'chunks_pending': pending_count
            })
        else:
            logging.warning(f"❌ [AUDIO] No pending audio found for call {call_id}")
            socketio.emit('test_audio_result', {
                'success': False,
                'message': 'No pending audio found'
            })
            
    except Exception as e:
        logging.error(f"❌ [ERROR] Error in request_audio handler: {str(e)}")
        socketio.emit('test_audio_result', {
            'success': False,
            'message': f'Error: {str(e)}'
        })

# Add a handler for the stt_transcript event emitted by the SpeechToText class
@socketio.on('stt_transcript')
def handle_stt_transcript(data):
    """Handle transcript events from the SpeechToText class and generate responses."""
    try:
        assistant_id = data.get('assistant_id')
        transcript = data.get('transcript')
        is_final = data.get('final', False)
        
        logging.info(f"🎤 [STT] Received transcript from SpeechToText: '{transcript}', final: {is_final}")
        
        # Find the corresponding call for this assistant_id
        call_id = None
        for cid, call_data in active_calls.items():
            if call_data.get('assistant_llm') and call_data['assistant_llm'].assistant_id == assistant_id:
                call_id = cid
                break
        
        if not call_id:
            logging.warning(f"🎤 [STT] Received transcript for unknown assistant_id: {assistant_id}")
            return
            
        # Forward the transcript to the frontend
        socketio.emit('stt_transcript', {
            'call_id': call_id,
            'transcript': transcript,
            'final': is_final
        })
        
        # If this is a final transcript, process it with the LLM and generate a response
        if is_final and transcript:
            logging.info(f"🎤 [STT] Processing final transcript for call {call_id}: '{transcript}'")
            
            call_data = active_calls[call_id]
            assistant_llm = call_data['assistant_llm']
            
            # Get response from LLM
            llm_start_time = time.time()
            response = assistant_llm.get_response(transcript)
            llm_response_time = time.time() - llm_start_time
            
            logging.info(f"🤖 [LLM] Response for call {call_id}: '{response}'")
            
            # Store transcripts in database
            eventlet.spawn(store_transcripts, call_id, transcript, response)
            
            # Send response transcript to frontend
            socketio.emit('transcript', {
                'call_id': call_id,
                'text': response,
                'assistant_id': assistant_id,
                'final': True
            })
            
            # Generate and stream audio response
            if not call_data.get('is_speaking', False):
                eventlet.spawn(generate_response_audio, call_id, response)
            else:
                logging.warning(f"🔊 [AUDIO] Already speaking for call {call_id}, queueing response")
                if 'pending_responses' not in call_data:
                    call_data['pending_responses'] = []
                call_data['pending_responses'].append(response)
                
    except Exception as e:
        logging.error(f"Error handling stt_transcript: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
