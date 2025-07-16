from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torch
import torchaudio
import io
from utils import logging as lg


model_path = "../fine-tuning-sst/model/checkpoint-5200"

model = Wav2Vec2ForCTC.from_pretrained(model_path)
processor = Wav2Vec2Processor.from_pretrained(model_path)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

print(lg.log_concat("STT model path:", model_path))
print(lg.log_concat("Process device:", device))


def transcript(wav_bytes: bytes) -> str:
    buffer = io.BytesIO(wav_bytes)
    speech_array, sampling_rate = torchaudio.load(buffer)

    if speech_array.shape[0] > 1:
        speech_array = speech_array.mean(dim=0)
    speech_array = speech_array.numpy()

    input_dict = processor(
        speech_array, return_tensors="pt", padding=True, sampling_rate=sampling_rate
    )

    logits = model(input_dict.input_values.to(device)).logits
    pred_ids = torch.argmax(logits, dim=-1)[0]
    clean_prediction = processor.decode(pred_ids).replace("[PAD]", "")

    return clean_prediction
