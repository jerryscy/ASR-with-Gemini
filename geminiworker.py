import time
import os
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.genai.types import (
    HttpOptions, 
    Content,
    Part,
    GenerateContentConfig
)

load_dotenv()

class GeminiWorker:

    def __init__(self):
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION")

        if not project_id or not location:
            raise ValueError("GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set in the .env file")

        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
            http_options=HttpOptions(api_version="v1")
        )
        # Load the model
        self.model = 'gemini-2.5-flash'#'gemini-2.5-flash'#
        self.reference = ''
        self.transcript_history = ''


    def set_reference(self, reference):
        self.reference = reference
        
    def set_langage(self, source, target):
        self.source_language = source
        self.target_language = target
    
                
    def close(self):
        print("ProcessAudioByGemini closed")
        
    async def translate_audio(self, audio: bytes, debug=False):
        """
        Translate audio to target language.
        """
        parts = []        
        parts.append(types.Part.from_text(text=f'source_language: {self.source_language}'))
        parts.append(types.Part.from_text(text=f'target_language: {self.target_language}'))
        parts.append(types.Part.from_text(text='Input audio:'))
        parts.append(types.Part.from_bytes(data=audio, mime_type="audio/wav"))
        SYSTEM_INSTRUCTION=f"Translate the input audio into {self.target_language} UNMISTAKABLY. Return translated text and nothing else."
        # Only add previous_audio if it's not empty
        content = [types.UserContent(parts=parts)]        
        #start = time.time()
        
        # Make a single call to _generate_content_sync
        async for chunk in await self.client.aio.models.generate_content_stream(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0,
                max_output_tokens=512,
                top_p = 0.95,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=0,
                ),
            ),
            contents=content,
            ):
            if chunk.text:
                yield chunk.text

    async def transcribe_audio(self, audio: bytes, debug=False):
        """
        Transcribe audio to target language.
        """
        parts = []        
        #parts.append(types.Part.from_text(text=f'source_language: {self.source_language}'))
        parts.append(types.Part.from_text(text='Input audio:'))
        parts.append(types.Part.from_bytes(data=audio, mime_type="audio/wav"))
            
        # Only add previous_audio if it's not empty
        content = [types.UserContent(parts=parts)]        
        #start = time.time()
        
        # Make a single call to _generate_content_sync
        async for chunk in await self.client.aio.models.generate_content_stream(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction="Transcribe the audio file into text. Output only the transcription text.",
                temperature=0,
                top_p = 0.95,
                max_output_tokens=512,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=0,
                ),
            ),
            contents=content,
            ):
            if chunk.text:
                if debug:
                    print(f"trunk text {chunk.text}")
                yield chunk.text
            if debug:
                print("_"*80)
