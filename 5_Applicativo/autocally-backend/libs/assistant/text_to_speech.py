from cartesia import Cartesia
#from cartesia.tts import TtsRequestEmbeddingSpecifierParams, OutputFormat_RawParams

import os
from app.extensions import db
from app.assistants.models import Assistant
from dotenv import load_dotenv
import logging

load_dotenv()

class TTS:
    def __init__(self, assistant_id):
        self.assistant_id = assistant_id
        self.voice_id = None
        self.ws = None
        self.is_connected = False
        
        logging.info(f"Initializing TTS for assistant_id: {assistant_id}")

        assistant = Assistant.query.get(assistant_id)
        
        print('Cartesia voice id: ' + assistant.cartesia_voice_id)

        if assistant:
            self.voice_id = assistant.cartesia_voice_id
            logging.debug(f"Using voice_id from assistant: {self.voice_id}")
        else:
            logging.error(f"Assistant not found with id: {assistant_id}")
            raise ValueError("Assistant not found")

        if not self.voice_id:
            self.voice_id = "79693aee-1207-4771-a01e-20c393c89e6f"
            #self.voice_id = "e00d0e4c-a5c8-443f-a8a3-473eb9a62355"
            logging.info("Using default voice_id")

        logging.debug("Initializing Cartesia client")
        self.cartesia_client = Cartesia(api_key=os.environ.get("CARTESIA_API_KEY"))

    def get_audio_stream(self, text):
        try:
            voice = self.cartesia_client.voices.get(id=self.voice_id)

            logging.info(f"Generating audio stream for text: {text}")
            model_id = "sonic-english"
            output_format = {
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 22050
            }

            logging.debug("Creating Cartesia websocket connection")

            ws = self.cartesia_client.tts.websocket()

            try:
                audio_chunks = []  # Store chunks for local playback
                
                for output in ws.send(
                    model_id=model_id,
                    transcript=text,
                    voice_id=self.voice_id,
                    stream=True,
                    language="it",
                    output_format=output_format
                ):
                    logging.debug(f"[TTS]Received output: {output.keys()}")
                    if 'audio' in output.keys():
                        buffer = output['audio']
                        logging.debug(f"[TTS]Received audio chunk of size: {len(buffer)}")
                        audio_chunks.append(buffer)  # Store chunk
                        if buffer:
                            yield buffer

                #self._play_audio_locally(audio_chunks, output_format['sample_rate'])

            except Exception as inner_e:
                logging.error(f"Inner error during TTS generation: {str(inner_e)}")
                raise
            finally:
                ws.close()

        except Exception as e:
            logging.error(f"Error in get_audio_stream: {str(e)}")
            raise

    def _play_audio_locally(self, audio_chunks, sample_rate):
        """Play audio chunks locally for testing purposes."""
        try:
            import sounddevice as sd
            import numpy as np
            
            # Concatenate all chunks
            audio_data = b''.join(audio_chunks)
            
            # Convert bytes to numpy array of float32
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            # Play the audio
            sd.play(audio_array, sample_rate)
            sd.wait()  # Wait until audio is finished playing
            
            logging.info("Audio playback completed")
        except ImportError:
            logging.error("sounddevice not installed. Install with: pip install sounddevice numpy")
        except Exception as e:
            logging.error(f"Error playing audio locally: {str(e)}")

