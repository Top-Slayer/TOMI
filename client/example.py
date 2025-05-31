import build

import audio

byte_datas = audio.record()

audio.sent2server(audio_data=byte_datas)