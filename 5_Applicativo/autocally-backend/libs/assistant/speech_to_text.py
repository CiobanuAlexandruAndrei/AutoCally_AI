import os
import logging
import asyncio
import base64
from deepgram import DeepgramClient, DeepgramClientOptions, LiveOptions, LiveTranscriptionEvents
from dotenv import load_dotenv
import eventlet
import nest_asyncio
from flask_socketio import emit
from flask import current_app
import numpy as np
import time
import wave

load_dotenv()
nest_asyncio.apply()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

deepgram_logger = logging.getLogger('deepgram_api')
deepgram_logger.setLevel(logging.INFO)
deepgram_file_handler = logging.FileHandler('deepgram_api.log')
deepgram_file_handler.setLevel(logging.INFO)
deepgram_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
deepgram_file_handler.setFormatter(deepgram_formatter)
deepgram_logger.addHandler(deepgram_file_handler)
deepgram_logger.propagate = False  # To not see in the console

class SpeechToText:
    def __init__(self, assistant_id):
        logger.info(f"Initializing SpeechToText for assistant {assistant_id}")
        deepgram_logger.info(f"=== INITIALIZING SPEECH TO TEXT ===")
        deepgram_logger.info(f"Assistant ID: {assistant_id}")
        
        self.assistant_id = assistant_id
        self.dg_client = None
        self.dg_connection = None
        self.transcript_parts = []
        self.is_streaming = False
        self.loop = None
        self.audio_chunks = []
        self.audio_buffer = []
        
        if not self.check_api_key():
            raise ValueError("Invalid or missing Deepgram API key")
        
        # Configure Deepgram client options
        options_dict = {"keepalive": "true", "vad_events": "true"}
        config = DeepgramClientOptions(options=options_dict)
        self.dg_client = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"), config)
        logger.info("Deepgram async client initialized successfully")

    def check_api_key(self):
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            deepgram_logger.error("DEEPGRAM_API_KEY is not set")
            return False
        masked_key = api_key[:4] + "..." if len(api_key) > 4 else "..."
        deepgram_logger.info(f"Using Deepgram API key starting with: {masked_key}")
        return True

    def handle_open(self, event, client):
        logger.info(f"Connection opened: {event}")
        deepgram_logger.info(f"=== DEEPGRAM CONNECTION OPENED ===")
        deepgram_logger.info(f"Assistant ID: {self.assistant_id}")
        self.is_streaming = True
        if self.audio_buffer:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(self.process_buffered_chunks(), loop)

    def handle_close(self, event, client):
        logger.info(f"Connection closed: {event}")
        deepgram_logger.info(f"=== DEEPGRAM CONNECTION CLOSED ===")
        self.is_streaming = False

    def handle_transcript(self, client, result=None):
        deepgram_logger.info(f"=== DEEPGRAM TRANSCRIPT RECEIVED ===")
        deepgram_logger.debug(f"Transcript result: {result}")
        if result and hasattr(result, 'channel') and hasattr(result.channel, 'alternatives') and len(result.channel.alternatives) > 0:
            sentence = result.channel.alternatives[0].transcript
            is_final = getattr(result, 'is_final', False)
            if sentence:
                self.transcript_parts.append(sentence)
                deepgram_logger.info(f"About to emit transcript event: text='{sentence}', final={is_final}")
                
                from app.assistants.socket_events import socketio
                
                socketio.emit('stt_transcript', {
                    'transcript': sentence,
                    'assistant_id': self.assistant_id,
                    'final': is_final
                })
                
                if is_final:
                    self.transcript_parts = []
                    deepgram_logger.info("Reset transcript parts after final message")
                
                deepgram_logger.info(f"Emitted transcript event: '{sentence}', Final: {is_final}")

    def handle_error(self, error, client):
        logger.error(f"Deepgram error: {error}")
        deepgram_logger.error(f"=== DEEPGRAM ERROR === Error details: {error}")

    async def process_buffered_chunks(self):
        while self.audio_buffer:
            chunk = self.audio_buffer.pop(0)
            await self.process_chunk(chunk)
            logger.info("Processed buffered chunk")

    async def _initialize_connection(self):
        logger.info("Initializing connection")
        deepgram_logger.info("=== INITIALIZING DEEPGRAM CONNECTION ===")
        
        try:
            options = LiveOptions(
                model="nova-2-general", 
                punctuate=True, 
                language="it", 
                smart_format=True, 
                interim_results=True, 
                encoding="linear16", 
                sample_rate=16000, 
                channels=1
            )
            
            # Correctly initialize the live connection with version "1"
            self.dg_connection = self.dg_client.listen.live.v("1")
            deepgram_logger.info("Created Deepgram connection")
            
            # Register event handlers using LiveTranscriptionEvents enum
            self.dg_connection.on(LiveTranscriptionEvents.Open, self.handle_open)
            self.dg_connection.on(LiveTranscriptionEvents.Close, self.handle_close)
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.handle_transcript)
            self.dg_connection.on(LiveTranscriptionEvents.Error, self.handle_error)
            deepgram_logger.info("Event handlers registered")
            
            # Start the connection synchronously and check the result
            if not self.dg_connection.start(options):
                deepgram_logger.error("Failed to start Deepgram connection")
                return False
            deepgram_logger.info("Deepgram connection started successfully")
            
            # Wait for the connection to open (set by handle_open)
            for _ in range(50):
                if self.is_streaming:
                    deepgram_logger.info("Connection confirmed as open")
                    return True
                await asyncio.sleep(0.1)
            
            deepgram_logger.error("Timeout waiting for connection to open")
            return False
            
        except Exception as e:
            error_msg = f"Error initializing connection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            deepgram_logger.error(error_msg)
            return False

    def start_stream(self):
        logger.info("Starting stream")
        deepgram_logger.info("=== STARTING STREAM ===")
        deepgram_logger.info(f"Assistant ID: {self.assistant_id}")
        
        if self.is_streaming:
            logger.warning("Stream already started")
            deepgram_logger.warning("Stream already started")
            return True
        
        try:
            # Reset all state
            self.audio_chunks = []
            self.audio_buffer = []
            self.dg_connection = None
            
            # Create or get the event loop
            try:
                self.loop = asyncio.get_event_loop()
                if self.loop.is_closed():
                    self.loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.loop)
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            
            # Run the async connection initialization
            connection_success = self.loop.run_until_complete(self._initialize_connection())
            
            if not connection_success:
                logger.error("Failed to initialize Deepgram connection")
                deepgram_logger.error("Failed to start stream - connection initialization failed")
                return False
            
            logger.info("Stream initialized successfully")
            deepgram_logger.info("Stream initialized successfully")
            return True
        except Exception as e:
            error_msg = f"Error starting stream: {str(e)}"
            logger.error(error_msg, exc_info=True)
            deepgram_logger.error(error_msg)
            return False

    async def process_chunk(self, audio_chunk):
        logger.info("Processing chunk")
        if not self.is_streaming:
            logger.info("STT stream not started, buffering audio chunk")
            self.audio_buffer.append(audio_chunk)
            return
        
        try:
            if isinstance(audio_chunk, dict) and 'audio' in audio_chunk:
                audio_data = audio_chunk['audio']
            elif isinstance(audio_chunk, str):
                audio_data = base64.b64decode(audio_chunk)
            elif isinstance(audio_chunk, (bytes, bytearray)):
                audio_data = audio_chunk
            elif hasattr(audio_chunk, 'tolist') and callable(audio_chunk.tolist):
                audio_data = np.array(audio_chunk.tolist(), dtype=np.int16).tobytes()
            else:
                audio_data = bytes(audio_chunk)
            
            deepgram_logger.info(f"Audio chunk length: {len(audio_data)} bytes")
            self.audio_chunks.append(audio_data)
            
            if len(audio_data) > 0:
                # Send audio data synchronously
                self.dg_connection.send(audio_data)
                deepgram_logger.info(f"Sent {len(audio_data)} bytes to Deepgram")
        except Exception as e:
            error_msg = f"Error processing chunk: {str(e)}"
            logger.error(error_msg, exc_info=True)
            deepgram_logger.error(error_msg)
            raise

    async def stop_stream(self):
        if not self.is_streaming:
            logger.warning("Stream already stopped")
            return
        
        try:
            logger.info("Stopping stream")
            if self.dg_connection:
                self.save_audio_file()
                # Finish the connection synchronously
                self.dg_connection.finish()
                logger.info("Deepgram connection finished")
                self.dg_connection = None
            
            self.is_streaming = False
            self.audio_chunks = []
            self.audio_buffer = []
            logger.info("Stream stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping stream: {str(e)}", exc_info=True)
            self.is_streaming = False
            raise

    def save_audio_file(self, directory='audio_logs'):
        if not self.audio_chunks:
            logger.warning("No audio chunks to save")
            return
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{directory}/audio_{self.assistant_id}_{timestamp}.wav"
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.audio_chunks))
        
        logger.info(f"Saved audio file to {filename}")