#import build  # not important for use case

import audio
import time

hostname, port = audio.get_config("http://XXXXXXXXXXXXXXX")
audio.MicRecorder().start()
audio.AudioStreamer(hostname=hostname, port=port).start()

while True:
    print("Main process")
    time.sleep(5)
