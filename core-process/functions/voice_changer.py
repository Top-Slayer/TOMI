# python voice_changer_2.py && python -m rvc_python cli -i audio.wav -o output.wav -mp mikuAI/MikuAI.pth -ip mikuAI/added_IVF3010_Flat_nprobe_1_v2.index -rsr 16000 -rmr 16000 -pi 12

from transformers import VitsModel, AutoTokenizer
import torch
import numpy as np
from scipy.io.wavfile import write as wav_write
from rvc_python.infer import RVCInference
from io import BytesIO


def change_voice():
    text = "ມື້ນີ້ທ່ານຮູ້ສຶກເມື້ອຍໆນະໃຫ້ໂທມິຊ່ວຍຫຍັງໄດ້ແດ່"

    model = VitsModel.from_pretrained("facebook/mms-tts-lao")
    tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-lao")

    inputs = tokenizer(text, return_tensors="pt")
    inputs["input_ids"] = inputs["input_ids"].long()

    if inputs["input_ids"].shape[1] == 0:
        print("[TTS] ❌ Tokenizer returned empty input.")
        exit(1)

    with torch.no_grad():
        int16_datas = model(**inputs).waveform

    int16_datas = (int16_datas.cpu().numpy() * 32767).astype(np.int16).squeeze()

    print(
        f"TTS output info: {int16_datas} size: {len(int16_datas)} shape: {int16_datas.shape}"
    )

    # test write wav file
    buffer = BytesIO()
    wav_write(buffer, rate=model.config.sampling_rate, data=int16_datas)
    buffer.seek(0)


    rvc = RVCInference(
        device="cuda:0",
        model_path="mikuAI/MikuAI.pth",
        index_path="mikuAI/added_IVF3010_Flat_nprobe_1_v2.index",
    )
    rvc.set_params(f0up_key=12, f0method="rmvpe")

    rvc.infer_file(buffer, "output.wav")
