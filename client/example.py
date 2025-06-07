import build  # not important for use case

import audio
import time

# hostname = "34.123.252.74"
# port = 1212

# audio.load_ssl(hostname=hostname, port=port)

# byte_datas = audio.record()

with open("voice.wav", "rb") as f:
    wav_bytes = f.read()

audio.AudioStreamer(audio_data=wav_bytes).start()

while True:
    print("Hello world!")
    time.sleep(5)


# audio.sent2server(
#     audio_data=wav_bytes,
# )
