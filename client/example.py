import TOMI.client.audio as tomi_audio

hostname, port = tomi_audio.get_config("http://<GET_CONFIG_ENDPOINT>")

if hostname != None and port != None:
    tomi_audio.MicRecorder().start()
    tomi_audio.AudioStreamer(hostname=hostname, port=port).start()


while True:
    print("Main process")
