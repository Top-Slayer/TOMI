import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write as wav_write
import time
import io
import grpc
import audio_pb2
import audio_pb2_grpc
import wave


SAMPLE_RATE = 16000  # Hz
CHANNELS = 1
CHUNK_DURATION = 0.1  # seconds
SILENCE_THRESHOLD = 0.001  # Adjust based on noise floor
MAX_SILENCE_DURATION = 3.0  # seconds


def _is_silent(audio_chunk, threshold):
    volume = np.sqrt(np.mean(audio_chunk**2))
    return volume < threshold


def record() -> io.BytesIO:
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


def sent2server(audio_data: bytes, ip_addr="localhost:50051"):
    request = audio_pb2.AudioData(
        format="wav", sample_rate=16000, audio_bytes=audio_data
    )

    channel = grpc.insecure_channel(ip_addr)
    stub = audio_pb2_grpc.AudioServiceStub(channel)
    response = stub.UploadAudio(request)

    print("Server says:", response.message)
