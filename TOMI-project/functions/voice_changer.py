import argparse
import wave
import struct
import socketio
import time
import urllib3
import numpy as np
import os
from pydub import AudioSegment

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BUFFER_SIZE = 2048 * 2 * 10
SAMPLING_RATE = 44100
GAIN = 10

in_folder = "sentences"
out_folder = "vc_sentences"

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

        # Optional: Save or play output
        if self.wave_writer is not None:
            self.wave_writer.writeframes(data)


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


if __name__ == "__main__":
    parser = setupArgParser()
    args, unknown = parser.parse_known_args()

    os.makedirs(out_folder, exist_ok=True)
    in_file_path = [os.path.join(in_folder, f) for f in os.listdir(in_folder)]
    # input_wav_path = args.file
    input_wav_path = in_file_path

    convert_to_44100(input_wav_path)

    wf = wave.open(input_wav_path, "rb")
    assert wf.getnchannels() == 1, "Input must be mono"
    assert wf.getsampwidth() == 2, "Input must be 16-bit PCM"
    assert wf.getframerate() == SAMPLING_RATE, "Input must be 44100Hz"


    with wave.open(f"{out_folder}/output.wav", "wb") as out_wav:
        out_wav.setnchannels(1)
        out_wav.setsampwidth(2)  # 16-bit
        out_wav.setframerate(SAMPLING_RATE)

        sio = socketio.Client(ssl_verify=False)
        my_namespace = MyCustomNamespace("/test", out_wav)
        sio.register_namespace(my_namespace)
        sio.connect(args.url)

        print(f"[>] Streaming from '{input_wav_path}'...")

        try:
            while True:
                data = wf.readframes(BUFFER_SIZE)
                if not data:
                    break  # End of file
                sio.emit(
                    "request_message", [time.time() * 1000, data], namespace="/test"
                )
                time.sleep(BUFFER_SIZE / SAMPLING_RATE)
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user")
        finally:
            wf.close()
            sio.disconnect()
