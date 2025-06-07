import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write as wav_write
import time
import io
import grpc
import audio_pb2
import audio_pb2_grpc
import wave
import threading
# import ssl
# import socket


SAMPLE_RATE = 16000  # Hz
CHANNELS = 1  # Mono
CHUNK_DURATION = 0.1  # seconds
SILENCE_THRESHOLD = 0.001  # Adjust based on noise floor
MAX_SILENCE_DURATION = 3.0  # seconds


def _is_silent(audio_chunk, threshold):
    volume = np.sqrt(np.mean(audio_chunk**2))
    return volume < threshold


def record() -> bytes:
    print("🎙️ Recording... Speak now.")
    frames = []
    silence_start = None

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32"
    ) as stream:
        while True:
            audio_chunk, _ = stream.read(int(SAMPLE_RATE * CHUNK_DURATION))
            frames.append(audio_chunk)

            if _is_silent(audio_chunk, SILENCE_THRESHOLD):
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

    return buffer.getvalue()


# def sent2server(audio_data: bytes, hostname="localhost", port=1212):
#     try:
#         ip_address = socket.gethostbyname(hostname)
#         print(f"Resolved {hostname} to {ip_address}")
#     except socket.gaierror as e:
#         print(f"DNS resolution failed for {hostname}: {e}")
#         raise

#     try:
#         with open("../server/server.pem", "rb") as f:
#             trusted_cert = f.read()
#         credentials = grpc.ssl_channel_credentials(root_certificates=trusted_cert)
#         channel = grpc.secure_channel(f"{hostname}:{port}", credentials)
#         stub = audio_pb2_grpc.AudioServiceStub(channel)

#         request = audio_pb2.AudioData(
#             format="wav", sample_rate=16000, audio_bytes=audio_data
#         )
#         response = stub.UploadAudio(request)
#         print("Server says:", response.message)
#         return response
#     except grpc.RpcError as e:
#         print(f"gRPC call failed: {e.details()}")
#         if "SSL" in str(e):
#             print("SSL handshake failed. Ensure server.pem is correct and trusted.")
#         raise
#     except Exception as e:
#         print(f"Error connecting to server: {str(e)}")
#         raise


class AudioStreamer(threading.Thread):
    def __init__(self, audio_data: bytes, hostname="localhost", port=50051):
        super().__init__(daemon=True)
        self.hostname = hostname
        self.audio_data = audio_data
        self.port = port
    

    def run(self):
        request = audio_pb2.AudioData(
            format="wav", sample_rate=16000, audio_bytes=self.audio_data
        )

        with grpc.insecure_channel(f"{self.hostname}:{self.port}") as channel:
            stub = audio_pb2_grpc.AudioServiceStub(channel)
            response_stream = stub.UploadAudio(request)

            for response in response_stream:
                print(f"Received {len(response.audio_bytes)} bytes from server")


# def sent2server(audio_data: bytes, hostname="localhost", port=50051):
#     request = audio_pb2.AudioData(
#         format="wav", sample_rate=16000, audio_bytes=audio_data
#     )

#     with grpc.insecure_channel(f"{hostname}:{port}") as channel:
#         stub = audio_pb2_grpc.AudioServiceStub(channel)
#         response_stream = stub.UploadAudio(request)

#         for response in response_stream:
#             print(f"Received {len(response.audio_bytes)} bytes from server")


# if __name__ == "__main__":
#     sent2server(audio_data=b"21948912480", hostname="1212-dep-01jwtpceq55ra5wcqkacdm9s5v-d.cloudspaces.litng.ai", port=443)
#     sent2server(audio_data=b"21948912480")
