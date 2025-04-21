import argparse
import wave
import struct
import socketio
import time
import urllib3
import numpy as np
import os, io
from pydub import AudioSegment
from scipy.io import wavfile
from multiprocessing import shared_memory

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BUFFER_SIZE = 2048 * 2 * 10
SAMPLING_RATE = 44100
GAIN = 10

# dont forget to make mono in audio


def convert_to_44100(path):
    audio = AudioSegment.from_file(path)
    audio = audio.set_frame_rate(44100)
    audio.export(path, format="wav")


def setupArgParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:18888/",
        help="url",
    )
    parser.add_argument(
        "--file", type=str, required=True, help="Path to input wav file"
    )
    return parser


class MyCustomNamespace(socketio.ClientNamespace):
    def __init__(self, namespace: str, wave_writer: wave.Wave_write):
        super().__init__(namespace)
        self.wave_writer = wave_writer

    def on_connect(self):
        print(f"[Socket.IO] connected")

    def on_disconnect(self):
        print(f"[Socket.IO] disconnected")

    def on_response(self, msg):
        timestamp = msg[0]
        data = msg[1]
        perf = msg[2]
        responseTime = time.time() * 1000 - timestamp
        print(f"RT:{responseTime:.1f}ms", perf)

        unpackedData = struct.unpack("<%sh" % (len(data) // 2), data)
        data = np.array(unpackedData, dtype=np.int32) * GAIN
        data = np.clip(data, -32768, 32767).astype(np.int16)
        data = struct.pack("<%sh" % len(data), *data)


def stream_from_file(filename, sio, namespace="/test"):
    wf = wave.open(filename, "rb")

    if (
        wf.getnchannels() != 1
        or wf.getsampwidth() != 2
        or wf.getframerate() != SAMPLING_RATE
    ):
        print(f"[Error] WAV must be mono, 16-bit, {SAMPLING_RATE}Hz")
        return

    print("[INFO] Streaming from file...")

    while True:
        frames = wf.readframes(BUFFER_SIZE)
        if len(frames) == 0:
            break
        timestamp = time.time() * 1000
        sio.emit("request_message", [timestamp, frames], namespace=namespace)
        time.sleep(BUFFER_SIZE / SAMPLING_RATE)  # simulate real-time pacing

    wf.close()
    print("[INFO] Streaming completed.")


def convert(name, shape, dtype, offsets):
    shm = shared_memory.SharedMemory(name=name)
    shared_array = np.ndarray(shape, dtype=dtype, buffer=shm.buf)

    sio = socketio.Client(ssl_verify=False)
    sio.connect("http://localhost:18888/", namespaces=["/test"])

    print("[>] Connected and ready to stream.")

    try:
        streamed_blocks = set()

        while True:
            if offsets:
                for i, (start, length) in enumerate(offsets):
                    audio_data = shared_array[start : start + length]

                    print(f"\n[>] Streaming block [{i}] ({length} samples)")

                    os.makedirs("out_folder", exist_ok=True)
                    wavfile.write(
                        f"out_folder/output_{i}.wav", SAMPLING_RATE, audio_data
                    )

                    for j in range(len(audio_data)):
                        chunk = audio_data[j : j + BUFFER_SIZE].tobytes()
                        sio.emit(
                            "request_message",
                            [int(time.time() * 1000), chunk],
                            namespace="/test",
                        )
                        time.sleep(BUFFER_SIZE / SAMPLING_RATE)
                    streamed_blocks.add(i)
            else:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
    finally:
        print("[!] Steam has stoped")
        sio.disconnect()
        shm.close()
