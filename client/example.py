#import build  # not important for use case

import audio
import time
import json

with open("config_tunnel.json", "r") as f:
    data = json.load(f)

hostname = data["hostname"]
port = data["port"]

audio.MicRecorder().start()
audio.AudioStreamer(hostname=hostname, port=port).start()

while True:
    print("Hello world!")
    time.sleep(5)
