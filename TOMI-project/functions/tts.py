from transformers import VitsModel, AutoTokenizer
import torch
import scipy
import numpy as np
import os
from shared_datas import mem

model = VitsModel.from_pretrained("facebook/mms-tts-lao")
tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-lao")

def transcript(text: str):
    inputs = tokenizer(text, return_tensors="pt")

    # print(f"\nProcess {text}.wav: {inputs}")

    with torch.no_grad():
        output = model(**inputs).waveform

    output = (output.cpu().numpy() * 32767).astype(np.int16).squeeze()
    print(output)

    mem.write_audio(output)

    # scipy.io.wavfile.write(f"{folder}/{n}.wav", rate=model.config.sampling_rate, data=output)

# text2speech("ມື້ນີ້ເມື່ອຍບໍໃຫ້ໂທມິຊ່ວຍຫຍັງນາຍທ່ານໄດ້ແດ່")

# Dep for this tts
# pip install "accelerate==1.6.0" "transformers==4.35.0"
