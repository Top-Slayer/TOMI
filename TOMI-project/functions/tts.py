from transformers import VitsModel, AutoTokenizer
import torch
import numpy as np
from shared_datas import mem
import scipy

model = VitsModel.from_pretrained("facebook/mms-tts-lao")
tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-lao")


def synthesize(text: str):
    inputs = tokenizer(text, return_tensors="pt")
    inputs["input_ids"] = inputs["input_ids"].long()

    with torch.no_grad():
        output = model(**inputs).waveform

    output = (output.cpu().numpy() * 32767).astype(np.int16).squeeze()

    print(f"\ntts: {output} size: {len(output)} shape: {output.shape}")

    scipy.io.wavfile.write("out_folder/techno.wav", rate=model.config.sampling_rate, data=output)

    mem.write_audio(output)


# text2speech("ມື້ນີ້ເມື່ອຍບໍໃຫ້ໂທມິຊ່ວຍຫຍັງນາຍທ່ານໄດ້ແດ່")

# Dep for this tts
# pip install "accelerate==1.6.0" "transformers==4.35.0"
