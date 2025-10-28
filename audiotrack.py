import numpy as np

class AudioTrack:
    """Encapsulates audio stream, VAD state, transcription, and translation."""
    def __init__(self):
        self.stream = []              # List to store processed audio chunks (numpy arrays)
        self.transcription = ""       # Accumulated transcription text
        self.translation = ""         # Accumulated translation text
        self.live_api_translation = "" # Accumulated live api translation text
        self.last_vad_pause = False   # Tracks the last VAD pause state
        self.processing_active = False # Flag to prevent concurrent processing tasks
        self.continuous_pause_count = 0 # Counter for consecutive pause segments
        self.speech_segment_count = 0 # Counter for non-pause audio segments
        self.speech_segment_count_before_pause = 0
        self.current_stream = []

    def add_chunk(self, processed_chunk):
        """Appends a processed audio chunk (numpy array) to the stream."""
        if processed_chunk is not None:
            self.stream.append(processed_chunk)

    def get_aggregated_audio(self):
        """Concatenates all chunks in the stream into a single NumPy array."""
        if not self.stream:
            return None
        try:
            return np.concatenate(self.stream)
        except ValueError: # Handle case where stream might be empty despite check (race condition?)
             print("Warning: Attempted to concatenate empty stream.")
             return None

    def clear_stream(self):
        """Resets the audio stream to an empty list."""
        self.stream = []

    def update_transcription(self, new_transcription):
        """Appends new text results to the transcription and translation.
        Agent response is handled separately for streaming."""
        if new_transcription:
            self.transcription += new_transcription

    def update_translation(self, new_translation):
        """Appends new text results to the transcription and translation.
        Agent response is handled separately for streaming."""
        if new_translation:
            self.translation += new_translation

    def update_live_api_translation(self, new_translation):
        """Appends new text results to the live api translation."""
        if new_translation:
            self.live_api_translation += new_translation
            
    def finalize_results(self):
        """Appends new text results to the transcription and translation.
        Agent response is handled separately for streaming."""
        self.transcription += "\n"
        self.translation += "\n"

    def set_vad_pause_status(self, is_pause: bool):
        """Updates the last recorded VAD pause status and the continuous pause counter."""
        if is_pause:
            self.continuous_pause_count += 1
        else:
            # Reset the counter if the segment is not a pause
            self.continuous_pause_count = 0
            self.speech_segment_count += 1 # Increment speech segment counter
            
        if self.continuous_pause_count >= 1:
            self.last_vad_pause = is_pause
            self.speech_segment_count_before_pause = self.speech_segment_count
            self.speech_segment_count = 0
            
        else:
            self.last_vad_pause = False

        # print(f"is_pause:{is_pause},continuous_pause_count:{self.continuous_pause_count},speech_segment_count:{self.speech_segment_count},speech_segment_count_before_pause:{self.speech_segment_count_before_pause}")

    def get_stream_length(self):
        """Returns the number of chunks currently in the stream."""
        return len(self.stream)


    # Optional: Add a method to get the current pause count
    def get_continuous_pause_count(self):
        """Returns the current count of continuous pauses."""
        return self.continuous_pause_count

    def get_speech_segment_count(self):
        """Returns the current count of speech segment."""
        return self.speech_segment_count
    
    def get_speech_segment_before_pause_count(self):
        """Returns the current count of speech segment before pause."""
        return self.speech_segment_count_before_pause
