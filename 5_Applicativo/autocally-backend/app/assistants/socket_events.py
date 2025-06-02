# flask_socketio and assistant logic (unchanged except for stt integration)
from flask_socketio import emit
from .models import Assistant
from libs.assistant.assistant_llm import AssistantLLM
from libs.assistant.text_to_speech import TTS
from libs.assistant.speech_to_text import SpeechToText
#from .transcript_handler import TranscriptHandler
from ..security.routes import auth
from flask import request
import logging
import time
import asyncio
import eventlet
from eventlet import spawn_after
from ..extensions import socketio

eventlet.monkey_patch()

assistant_llm_cache = {}
tts_cache = {}
stt_cache = {}

@socketio.on('connect')
def handle_connect():
    logging.info('Client connected')
    socketio.emit('connection_established', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected')
    try:
        tts_cache.clear()
        assistant_llm_cache.clear()
        stt_cache.clear()
    except Exception as e:
        logging.error(f"Error in disconnect handler: {str(e)}")

@socketio.on('chat_message')
def handle_message(data):
    logging.info(f"Received chat_message: {data}")
    try:
        assistant_id = data.get('assistant_id')
        question = data.get('question')
        use_tts = data.get('use_tts', False)
        
        if not assistant_id:
            socketio.emit('error', {'message': 'Missing assistant_id'})
            return
            
        assistant = Assistant.query.get_or_404(assistant_id)
        
        if assistant_id not in assistant_llm_cache:
            assistant_llm_cache[assistant_id] = AssistantLLM(assistant_id)
        
        if question:
            llm_start_time = time.time()
            assistant_llm = assistant_llm_cache[assistant_id]
            response = assistant_llm.get_response(question)
            llm_response_time = time.time() - llm_start_time
            
            socketio.emit('chat_response', {
                'content': response,
                'assistant_id': assistant_id,
                'llm_response_time': llm_response_time
            })
            
            if use_tts:
                handle_tts(assistant_id, response, tts_cache)
        
    except Exception as e:
        logging.error(f"Error in chat_message handler: {str(e)}")
        socketio.emit('error', {'message': str(e)})

def handle_tts(assistant_id, response, tts_cache):
    try:
        if assistant_id not in tts_cache:
            tts_cache[assistant_id] = TTS(assistant_id)
        
        tts = tts_cache[assistant_id]
        tts_start_time = time.time()
        audio_stream = tts.get_audio_stream(response)
        
        first_chunk = True
        for chunk in audio_stream:
            if chunk and len(chunk) > 0:
                if first_chunk:
                    first_chunk_time = time.time() - tts_start_time
                    socketio.emit('audio_chunk', {
                        'audio': chunk,
                        'assistant_id': assistant_id,
                        'final': False,
                        'first_chunk_time': first_chunk_time
                    })
                    first_chunk = False
                else:
                    socketio.emit('audio_chunk', {
                        'audio': chunk,
                        'assistant_id': assistant_id,
                        'final': False
                    })
        
        socketio.emit('audio_chunk', {
            'assistant_id': assistant_id,
            'final': True
        })
        
    except Exception as e:
        logging.error(f"TTS error: {str(e)}")
        socketio.emit('error', {'message': f'TTS error: {str(e)}'})

@socketio.on('start_stt')
def handle_start_stt():
    try:
        assistant_id = request.args.get('assistant_id')
        if not assistant_id:
            logging.warning("No assistant_id provided for start_stt")
            socketio.emit('error', {'message': 'No assistant_id provided'})
            return
            
        # Create new STT instance if not exists
        if assistant_id not in stt_cache:
            stt_cache[assistant_id] = SpeechToText(assistant_id)
            
        speech_to_text = stt_cache[assistant_id]
        
        def start_stream_task():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(speech_to_text.start_stream())
                finally:
                    loop.close()
            except Exception as e:
                logging.error(f"Error starting STT stream: {str(e)}")
                socketio.emit('error', {'message': str(e)})
        
        eventlet.spawn(start_stream_task)
        socketio.emit('stt_started', {'status': 'ready', 'assistant_id': assistant_id})
        
    except Exception as e:
        logging.error(f"Error in start_stt: {str(e)}")
        socketio.emit('error', {'message': str(e)})

@socketio.on('stt_audio_chunk')
def handle_audio_chunk(data):
    assistant_id = data.get('assistant_id')
    audio_data = data.get('audio')
    
    try:
        if assistant_id and audio_data:
            if assistant_id in stt_cache:
                speech_to_text = stt_cache[assistant_id]
                eventlet.spawn(process_stt_chunk, speech_to_text, {
                    'audio': audio_data
                })
            else:
                # Automatically restart STT if not in cache
                stt_cache[assistant_id] = SpeechToText(assistant_id)
                speech_to_text = stt_cache[assistant_id]
                
                def start_stream_task():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(speech_to_text.start_stream())
                        finally:
                            loop.close()
                    except Exception as e:
                        logging.error(f"Error starting STT stream: {str(e)}")
                        socketio.emit('error', {'message': str(e)})
                
                eventlet.spawn(start_stream_task)
                eventlet.spawn(process_stt_chunk, speech_to_text, {
                    'audio': audio_data
                })
                socketio.emit('stt_started', {'status': 'ready', 'assistant_id': assistant_id})
    except Exception as e:
        logging.error(f"Exception in handle_audio_chunk: {str(e)}")
        socketio.emit('error', {'message': f'Error processing audio: {str(e)}'})

@socketio.on('stop_stt')
def handle_stop_stt():
    try:
        assistant_id = request.args.get('assistant_id')
        if not assistant_id:
            logging.warning("No assistant_id provided for stop_stt")
            socketio.emit('error', {'message': 'No assistant_id provided'})
            return
            
        if assistant_id in stt_cache:
            speech_to_text = stt_cache[assistant_id]
            
            def stop_stream_task():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(speech_to_text.stop_stream())
                    finally:
                        loop.close()
                    logging.info(f"STT stream stopped for assistant {assistant_id}")
                    
                    # Don't remove from cache here - only on disconnect
                    
                except Exception as e:
                    logging.error(f"Error stopping STT stream: {str(e)}")
            
            eventlet.spawn(stop_stream_task)
            socketio.emit('stt_stopped', {'status': 'stopped', 'assistant_id': assistant_id})
        else:
            logging.warning(f"No STT stream found for assistant {assistant_id}")
            socketio.emit('stt_stopped', {'status': 'not_found', 'assistant_id': assistant_id})
            
    except Exception as e:
        logging.error(f"Error stopping STT: {str(e)}")
        socketio.emit('error', {'message': f'Error stopping STT: {str(e)}'})

@socketio.on('chat_cleanup')
def handle_chat_cleanup(data):
    try:
        assistant_id = data.get('assistant_id')
        if assistant_id:
            # Clear TTS cache
            if assistant_id in tts_cache:
                del tts_cache[assistant_id]
            
            # Clear LLM cache    
            if assistant_id in assistant_llm_cache:
                del assistant_llm_cache[assistant_id]
            
            # Clean up STT if exists
            if assistant_id in stt_cache:
                speech_to_text = stt_cache[assistant_id]
                
                def cleanup_task():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(speech_to_text.stop_stream())
                        finally:
                            loop.close()
                        
                        del stt_cache[assistant_id]
                        logging.info(f"Cleaned up resources for assistant {assistant_id}")
                        
                    except Exception as e:
                        logging.error(f"Error in cleanup task: {str(e)}")
                
                eventlet.spawn(cleanup_task)
                
    except Exception as e:
        logging.error(f"Error in chat cleanup handler: {str(e)}")

def process_stt_chunk(speech_to_text, audio_chunk_data):
    try:
        if not speech_to_text.is_streaming:
            logging.warning("STT stream not started, ignoring audio chunk")
            return
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(speech_to_text.process_chunk(audio_chunk_data))
        finally:
            loop.close()
    except Exception as e:
        logging.error(f"Error in process_stt_chunk: {str(e)}")

