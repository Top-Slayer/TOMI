import argparse
import wave
import struct
import socketio
import time
import urllib3
import numpy as np
import os, io
import base64
from pydub import AudioSegment
from scipy.io import wavfile
from multiprocessing import shared_memory

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BUFFER_SIZE = 2048 * 2 * 10  # 2 KiB
SAMPLING_RATE = 16000
GAIN = 10


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

        if self.wave_writer is not None:
            self.wave_writer.writeframes(data)


def convert(name, shape, dtype, offsets):
    shm = shared_memory.SharedMemory(name=name)
    shared_array = np.ndarray(shape, dtype=dtype, buffer=shm.buf)

    print("[>] Connected and ready to stream.")

    index = 0

    try:
        while True:
            if index < len(offsets):
                start, length = offsets[index]
                audio_data = shared_array[start : start + length]

                print(
                    f"\n[>] Streaming block: index [{index}] (data: {audio_data}, length: {length} samples)"
                )

                wav_path = f"out_folder/{index}.wav"
                os.makedirs("out_folder", exist_ok=True)

                out_wav = wave.open(wav_path, "wb")
                out_wav.setnchannels(1)
                out_wav.setsampwidth(2)
                out_wav.setframerate(SAMPLING_RATE)

                sio = socketio.Client(ssl_verify=False)
                my_namespace = MyCustomNamespace("/test", out_wav)
                sio.register_namespace(my_namespace)
                sio.connect("http://localhost:18888/", namespaces=["/test"])

                sio.emit(
                    "request_message",
                    [int(time.time() * 1000), audio_data.tobytes()],
                    namespace="/test",
                )
                time.sleep(len(audio_data) / SAMPLING_RATE)

                # for j in range(0, len(audio_data), BUFFER_SIZE):
                #     chunk = audio_data[j : j + BUFFER_SIZE]
                #     sio.emit(
                #         "request_message",
                #         [int(time.time() * 1000), chunk],
                #         namespace="/test",
                #     )
                #     time.sleep(BUFFER_SIZE / SAMPLING_RATE)

                index += 1
                sio.disconnect()
                out_wav.close()
            else:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")

    finally:
        print("[!] Steam has stoped")
        shm.close()
