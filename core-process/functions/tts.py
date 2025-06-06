from transformers import VitsModel, AutoTokenizer
import torch
import numpy as np
from utils import shmem
import scipy
from scipy.io.wavfile import write as wav_write
import io

model = VitsModel.from_pretrained("facebook/mms-tts-lao")
tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-lao")


def synthesize(text: str):
    inputs = tokenizer(text, return_tensors="pt")
    inputs["input_ids"] = inputs["input_ids"].long()

    with torch.no_grad():
        int16_datas = model(**inputs).waveform

    int16_datas = (int16_datas.cpu().numpy() * 32767).astype(np.int16).squeeze()

    print(f"\ntts: {int16_datas} size: {len(int16_datas)} shape: {int16_datas.shape}")

    # test write wav file
    # scipy.io.wavfile.write("out_folder/techno.wav", rate=model.config.sampling_rate, data=int16_datas)

    buffer = io.BytesIO()
    wav_write(buffer, model.config.sampling_rate, int16_datas)
    buffer.seek(0)

    shmem.write_bytes_to_shm(buffer.getvalue())


# text2speech("ມື້ນີ້ເມື່ອຍບໍໃຫ້ໂທມິຊ່ວຍຫຍັງນາຍທ່ານໄດ້ແດ່")

# Dep for this tts
# pip install "accelerate==1.6.0" "transformers==4.35.0"
