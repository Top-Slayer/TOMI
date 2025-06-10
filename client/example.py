import build  # not important for use case

import audio
import time

hostname = "2.tcp.us-cal-1.ngrok.io"
port = 19490

streamer = audio.AudioStreamer(hostname=hostname, port=port)
streamer.mic().start()

while True:
    print("Hello world!")
    time.sleep(5)


# audio.sent2server(
#     audio_data=wav_bytes,
# )
