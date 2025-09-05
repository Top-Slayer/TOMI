from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torch
import torchaudio
import io
from utils import logging as lg
import csv
from datetime import datetime


# model_path = "../fine-tuning-sst/model.bak/checkpoint-20100"

model_paths = {
    "lao": "TopSlayer/wav2vec2-xls-r-300m-lao",
    "thai": "airesearch/wav2vec2-large-xlsr-53-th",
}

models = {}
processors = {}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

for lang, path in model_paths.items():
    models[lang] = Wav2Vec2ForCTC.from_pretrained(path).to(device)
    processors[lang] = Wav2Vec2Processor.from_pretrained(path)

    print(f"Loaded {lang.upper()} model from: {path}")
print(f"Process device: {device}")


def transcript(wav_bytes: bytes, lang: str = "lao") -> str:
    if isinstance(lang, dict):
        lang = lang.get("lang", "lao")

    print(lg.log_concat(f"Used language: {lang}"))

    model = models[lang]
    processor = processors[lang]

    buffer = io.BytesIO(wav_bytes)
    speech_array, sampling_rate = torchaudio.load(buffer)

    if speech_array.shape[0] > 1:
        speech_array = speech_array.mean(dim=0)
    nd_speech_array = speech_array.numpy()

    input_dict = processor(
        nd_speech_array, return_tensors="pt", padding=True, sampling_rate=sampling_rate
    )

    logits = model(input_dict.input_values.to(device)).logits
    pred_ids = torch.argmax(logits, dim=-1)[0]
    clean_prediction = processor.decode(pred_ids).replace("[PAD]", "")

    # if lang == "lao":
    #     with open(
    #         "tmp/raw_datasets/sample.tsv", "a", encoding="utf-8", newline=""
    #     ) as f:
    #         writer = csv.writer(f, delimiter="\t")

    #         des_file = f"{datetime.now().strftime('%d%m%Y_%H%M%S_%f')[:-3]}.wav"
    #         waveform = torch.clamp(speech_array, -1.0, 1.0)
    #         waveform_int16 = (waveform * 32767).to(torch.int16)
    #         torchaudio.save(
    #             f"tmp/raw_datasets/clips/{des_file}.wav",
    #             waveform_int16,
    #             sampling_rate,
    #             encoding="PCM_S",
    #             bits_per_sample=16,
    #         )
    #         writer.writerow([des_file, clean_prediction])

    return clean_prediction
