import numpy as np
import torch
import torchaudio
from silero_vad import load_silero_vad

class AudioProcessor:
    """A class to handle audio processing tasks like VAD and resampling."""
    def __init__(self, target_sample_rate=16000):
        self.target_sample_rate = target_sample_rate
        try:
            self.vad_model = load_silero_vad()
            print("Silero VAD model loaded successfully.")
        except Exception as e:
            print(f"Error loading Silero VAD model: {e}")
            self.vad_model = None

    def revise_audio_for_vad(self, data, original_sample_rate):
        """
        Resamples audio to target_sample_rate, ensures float32, and converts to mono.
        Returns a float32 numpy array or None on error.
        """
        try:
            if data.dtype != np.float32:
                data_float32 = data.astype(np.float32) / 32768.0 if np.issubdtype(data.dtype, np.integer) else data.astype(np.float32)
            else:
                data_float32 = data

            if data_float32.ndim > 1:
                data_float32 = np.mean(data_float32, axis=1)

            if original_sample_rate != self.target_sample_rate:
                resampler = torchaudio.transforms.Resample(orig_freq=original_sample_rate, new_freq=self.target_sample_rate)
                data_float32 = resampler(torch.from_numpy(data_float32)).numpy()

            return data_float32

        except Exception as e:
            print(f"Error during audio revision for VAD: {e}. Returning None.")
            return None

    def vad_detect_pause(self, audio_float32_mono_16k):
        """
        Uses Silero VAD on pre-processed audio to detect silence.
        Returns True if a pause is detected, False otherwise.
        """
        if self.vad_model is None:
            print("VAD model not loaded, cannot perform VAD.")
            return False

        if audio_float32_mono_16k is None or audio_float32_mono_16k.size == 0:
            return True

        chunk_size = 512
        num_samples = audio_float32_mono_16k.shape[0]
        speech_detected_in_chunk = False
        silence_threshold = 0.8

        for i in range(0, num_samples, chunk_size):
            segment = audio_float32_mono_16k[i : i + chunk_size]

            if segment.shape[0] == 0:
                continue

            if segment.shape[0] < chunk_size:
                padding = np.zeros(chunk_size - segment.shape[0], dtype=np.float32)
                segment = np.concatenate((segment, padding))

            chunk_tensor = torch.from_numpy(segment)

            try:
                speech_prob = self.vad_model(chunk_tensor, self.target_sample_rate).item()
                if speech_prob >= silence_threshold:
                    speech_detected_in_chunk = True
                    break
            except Exception as e:
                print(f"Error during VAD processing for segment: {e}")
                speech_detected_in_chunk = True
                break

        return not speech_detected_in_chunk
