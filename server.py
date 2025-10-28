import asyncio
import websockets
import numpy as np
import json
import time
from geminiworker import GeminiWorker
from audioprocessor import AudioProcessor
from audiotrack import AudioTrack
from google.cloud import texttospeech_v1beta1 as texttospeech
from google.cloud import resourcemanager_v3
import os
import subprocess
from typing import List

def initialize_clients():
    """
    Initializes the GeminiWorker and TextToSpeechClient.
    """
    global geminiworker, tts_client
    geminiworker = GeminiWorker()
    geminiworker.set_langage("Chinese (Simplified) (zh-CN)", "English (United States) (en-US)")

    tts_client = texttospeech.TextToSpeechClient()

def check_gcloud_auth():
    """
    Checks for gcloud authentication and prompts the user to log in if not authenticated.
    """
    try:
        # The 'r' at the end of the command was a typo in the prompt, so I am correcting it to 'token'
        subprocess.check_output(["gcloud", "auth", "application-default", "print-access-token"], stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Attempting to authenticate with gcloud...")
        subprocess.run(["gcloud", "auth", "application-default", "login"])
        print("Authentication successful, you can now start the application.")
        exit()

# --- Global Instances ---
geminiworker = None
tts_client = None
audio_processor = AudioProcessor()
# Each client will have its own AudioTrack
client_audio_tracks = {}

check_gcloud_auth()
initialize_clients()

debug = True
async def _get_full_response(gen):
    return "".join([item async for item in gen])

async def process_audio_chunk(websocket):
    """
    Handles a single client connection.
    """
    client_id = id(websocket)
    client_audio_tracks[client_id] = AudioTrack()
    current_audio_track = client_audio_tracks[client_id]
    last_message_time = None

    try:
        async for message in websocket:
            current_time = time.time()
            if last_message_time is not None:
                time_gap = current_time - last_message_time
                if debug:
                    print(f"Time gap between messages: {time_gap:.4f} seconds")
            last_message_time = current_time
            
            if debug:
                print("Connected")
            if isinstance(message, bytes):
                # Assuming the client sends raw audio data as bytes
                # The client should send audio in a format that can be converted to a numpy array
                # For example, 16-bit PCM
                data = np.frombuffer(message, dtype=np.int16)

                # Process audio (resample, VAD, etc.)
                processed_data = audio_processor.revise_audio_for_vad(data, original_sample_rate=16000) # Assuming 16kHz from client

                if processed_data is not None:
                    current_audio_track.add_chunk(processed_data.copy())
                    is_pause = audio_processor.vad_detect_pause(processed_data)
                    #if debug:
                        #print(f"is_pause:{is_pause}")
                    current_audio_track.set_vad_pause_status(is_pause)
                    if is_pause and current_audio_track.get_speech_segment_before_pause_count() > 1:
                        full_audio_data_float32 = current_audio_track.get_aggregated_audio()
                        current_audio_track.clear_stream()

                        if full_audio_data_float32 is not None:
                            # Create WAV buffer
                            full_audio_data_int16 = (full_audio_data_float32 * 32767).astype(np.int16)
                            import io
                            import wave
                            wav_buffer_io = io.BytesIO()
                            with wave.open(wav_buffer_io, 'wb') as wf:
                                wf.setnchannels(1)
                                wf.setsampwidth(2)
                                wf.setframerate(16000)
                                wf.writeframes(full_audio_data_int16.tobytes())
                            full_wav_buffer = wav_buffer_io.getvalue()
                            if debug:
                                print("process audio")
                            # Get transcription and translation
                            transcription_task = asyncio.create_task(_get_full_response(geminiworker.transcribe_audio(full_wav_buffer)))
                            translation_task = asyncio.create_task(_get_full_response(geminiworker.translate_audio(full_wav_buffer)))

                            transcription_result, translation_result = await asyncio.gather(transcription_task, translation_task)

                            response = {
                                "transcription": transcription_result,
                                "translation": translation_result
                            }
                            await websocket.send(json.dumps(response))

                            # --- Text-to-Speech ---
                            if translation_result:
                                synthesis_input = texttospeech.SynthesisInput(text=translation_result)
                                language_code = geminiworker.target_language.split('(')[-1].split(')')[0]
                                print(f"{language_code}-Chirp3-HD-Charon")
                                voice = texttospeech.VoiceSelectionParams(
                                    language_code=language_code,
                                    name=f"{language_code}-Chirp3-HD-Charon"
                                )
                                audio_config = texttospeech.AudioConfig(
                                    audio_encoding=texttospeech.AudioEncoding.MP3
                                )
                                tts_response = tts_client.synthesize_speech(
                                    input=synthesis_input, voice=voice, audio_config=audio_config
                                )
                                await websocket.send(tts_response.audio_content)


            elif isinstance(message, str):
                # Handle text messages (e.g., configuration)
                try:
                    config = json.loads(message)
                    if 'target_language' in config:
                        source_lang = geminiworker.source_language if hasattr(geminiworker, 'source_language') else "Chinese (Simplified) (zh-CN)"
                        geminiworker.set_langage(source_lang, config['target_language'])
                        await websocket.send(json.dumps({"status": "language updated"}))
                    if 'reference' in config:
                        geminiworker.set_reference(config['reference'])
                        await websocket.send(json.dumps({"status": "reference updated"}))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON"}))

    except websockets.exceptions.ConnectionClosed:
        print(f"Client {client_id} disconnected")
    finally:
        del client_audio_tracks[client_id]





async def main():
    # Set default languages

    async with websockets.serve(process_audio_chunk, "localhost", 8765):
        print("WebSocket server started at ws://localhost:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
