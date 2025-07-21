from transformers import VitsModel, AutoTokenizer
import torch
import numpy as np
from utils import shmem
from utils import logging as lg
import scipy
from scipy.io.wavfile import write as wav_write
import io, os
from . import voice_changer as vc

model = VitsModel.from_pretrained("facebook/mms-tts-lao")
tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-lao")

not_vc_path = os.path.join("tmp", "not_vc.wav")


def synthesize(text: str):
    inputs = tokenizer(text, return_tensors="pt")
    inputs["input_ids"] = inputs["input_ids"].long()

    if inputs['input_ids'].shape[1] == 0:
        print(lg.log_concat("[TTS] ❌ Tokenizer returned empty input."))
        return

    with torch.no_grad():
        int16_datas = model(**inputs).waveform

    int16_datas = (int16_datas.cpu().numpy() * 32767).astype(np.int16).squeeze()

    print(lg.log_concat(f"TTS output info: {int16_datas} size: {len(int16_datas)} shape: {int16_datas.shape}"))

    # test write wav file
    scipy.io.wavfile.write(not_vc_path, rate=model.config.sampling_rate, data=int16_datas)
    vc_bytes = vc.change_voice(not_vc_path)

    buffer = io.BytesIO()
    buffer.write(vc_bytes)
    buffer.seek(0)

    shmem.write_bytes_to_shm(buffer.getvalue())



# text2speech("ມື້ນີ້ເມື່ອຍບໍໃຫ້ໂທມິຊ່ວຍຫຍັງນາຍທ່ານໄດ້ແດ່")

# Dep for this tts
# pip install "accelerate==1.6.0" "transformers==4.35.0"
