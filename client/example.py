#import build  # not important for use case

import audio
import time

hostname = "0.tcp.ngrok.io"
port = 18773

audio.MicRecorder().start()
audio.AudioStreamer(hostname=hostname, port=port).start()

while True:
    print("Hello world!")
    time.sleep(5)


# audio.sent2server(
#     audio_data=wav_bytes,
# )
