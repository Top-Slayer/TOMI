import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write as wav_write
from scipy.io import wavfile
import io
import time
import io
import grpc
import audio_pb2
import audio_pb2_grpc
import wave
import threading
import requests
from typing import Tuple


SAMPLE_RATE = 16000  # Hz
CHANNELS = 1  # Mono
CHUNK_DURATION = 0.1  # seconds
SILENCE_THRESHOLD = 0.02  # Adjust based on noise floor
MAX_SILENCE_DURATION = 3.0  # seconds

mic_ready = threading.Event()
audio_ready = threading.Event()
audio_data: bytes = None


def get_config(url: str) -> Tuple[str, int]:
    res = requests.get(url)
    data = res.json()

    return data['hostname'], data['port']


class AudioStreamer(threading.Thread):
    def __init__(self, hostname="localhost", port=443):
        super().__init__(daemon=True)
        self.hostname = hostname
        self.port = port

    def _audio_request_generator(self):
        global audio_data
        yield audio_pb2.AudioData(
            format="wav", sample_rate=16000, audio_bytes=audio_data
        )

    def run(self):
        while True:
            audio_ready.wait()
            audio_ready.clear()

            # channel =  grpc.secure_channel(f"{self.hostname}:{self.port}",  grpc.ssl_channel_credentials())
            channel = grpc.insecure_channel(f"{self.hostname}:{self.port}")

            stub = audio_pb2_grpc.AudioServiceStub(channel)

            response_stream = stub.StreamAudio(self._audio_request_generator())
            for response in response_stream:
                buf = io.BytesIO(response.audio_bytes)
                samplerate, data = wavfile.read(buf)
                sd.play(data, samplerate)
                sd.wait()

                print(f"Received {len(response.audio_bytes)} bytes from server")

            mic_ready.set()


class MicRecorder(threading.Thread):
    def __init__(self, callback=None):
        super().__init__(daemon=True)

    def _is_silent(self, audio_chunk, threshold):
        volume = np.sqrt(np.mean(audio_chunk**2))
        print(volume)
        return volume < threshold

    def run(self):
        global audio_data

        while True:
            print("🎙️ Recording... Speak now.")
            frames = []
            silence_start = None

            with sd.InputStream(
                samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32"
            ) as stream:
                while True:
                    audio_chunk, _ = stream.read(int(SAMPLE_RATE * CHUNK_DURATION))
                    frames.append(audio_chunk)

                    if self._is_silent(audio_chunk, SILENCE_THRESHOLD):
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > MAX_SILENCE_DURATION:
                            print("⏹️ Silence detected. Stopping recording.")
                            break
                    else:
                        silence_start = None

            recorded_audio = np.concatenate(frames, axis=0)
            int16_audio = (recorded_audio * 32767).astype(np.int16)

            buffer = io.BytesIO()
            wav_write(buffer, SAMPLE_RATE, int16_audio)
            buffer.seek(0)

            with wave.open(buffer, "rb") as wf:
                print("Channels:", wf.getnchannels())
                print("Sample Width:", wf.getsampwidth())
                print("Frame Rate:", wf.getframerate())
                print("Frames:", wf.getnframes())
                print(f"Duration (sec): {wf.getnframes() / wf.getframerate()}s")

            audio_data = buffer.getvalue()

            audio_ready.set()
            mic_ready.wait()
            mic_ready.clear()
