import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write as wav_write
from scipy.io import wavfile
import io
import time
import grpc
import threading
import requests
from typing import Tuple

import audio_pb2
import audio_pb2_grpc

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
    if res.status_code != 200:
        print(f"[!] Can't get config from server: {__file__}")
        return None, None

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
            num_reconnect = 0
            audio_ready.wait()
            audio_ready.clear()

            while True:
                try:
                    # channel =  grpc.secure_channel(f"{self.hostname}:{self.port}",  grpc.ssl_channel_credentials())
                    channel = grpc.insecure_channel(f"{self.hostname}:{self.port}")

                    stub = audio_pb2_grpc.AudioServiceStub(channel)

                    response_stream = stub.StreamAudio(self._audio_request_generator())

                    for response in response_stream:
                        buf = io.BytesIO(response.audio_bytes)
                        print(f"[TOMI Speaker] Received {len(response.audio_bytes)} bytes from server")
                        print(f"[TOMI Speaker] Speaking...")

                        samplerate, data = wavfile.read(buf)
                        sd.play(data, samplerate)
                        sd.wait()

                    print(f"[TOMI Speaker] Ouput sound done.")
                    break

                except:
                    if num_reconnect >= 10:
                        print(f"[!] Out of maximum trying connect")
                        break

                    print(f"[X] gRPC Error connect to Server: Retrying in 0.1s...")
                    time.sleep(0.1)
                    num_reconnect += 1

            mic_ready.set()

class MicRecorder(threading.Thread):
    def __init__(self, callback=None):
        super().__init__(daemon=True)

    def _is_silent(self, audio_chunk, threshold):
        volumn = np.sqrt(np.mean(audio_chunk**2))
        # print(volumn) # For debug watch volumn
        return volumn < threshold

    def run(self):
        global audio_data

        while True:
            print("[TOMI Microphone] Listening...")
            with sd.InputStream(
                samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32"
            ) as stream:
                while True:
                    audio_chunk, _ = stream.read(int(SAMPLE_RATE * CHUNK_DURATION))
                    if not self._is_silent(audio_chunk, SILENCE_THRESHOLD):
                        print("[TOMI Microphone] Voice detected. Recording started.")
                        frames = [audio_chunk]
                        break

                silence_start = None
                while True:
                    audio_chunk, _ = stream.read(int(SAMPLE_RATE * CHUNK_DURATION))
                    frames.append(audio_chunk)

                    if self._is_silent(audio_chunk, SILENCE_THRESHOLD):
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > MAX_SILENCE_DURATION:
                            print("[TOMI Microphone] Silence detected. Stopping recording.")
                            break
                    else:
                        silence_start = None

            recorded_audio = np.concatenate(frames, axis=0)
            int16_audio = (recorded_audio * 32767).astype(np.int16)

            buffer = io.BytesIO()
            wav_write(buffer, SAMPLE_RATE, int16_audio)
            buffer.seek(0)

            audio_data = buffer.getvalue()

            audio_ready.set()
            mic_ready.wait()
            mic_ready.clear()
