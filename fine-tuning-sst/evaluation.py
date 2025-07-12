import os
import torch
import csv
import pandas as pd
import soundfile as sf
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from jiwer import cer
from tqdm import tqdm
import shutil


# Load model and processor
model_path = "model/checkpoint-3600"
shutil.copy("vocab.json", model_path)

processor = Wav2Vec2Processor.from_pretrained(model_path)
model = Wav2Vec2ForCTC.from_pretrained(model_path)
model.eval()

test_data = []

#### Evaluation doesn't seen dataset ####
with open("eval-dataset/eval.tsv", "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")
    for row in reader:
        test_data.append(
            (os.path.join("eval-dataset", row[0]), row[1])
        )


#### Evaluation test dataset ####
# with open("laos-transcript/test.tsv", "r", encoding="utf-8") as f:
#     reader = csv.reader(f, delimiter="\t")
#     for row in reader:
#         if len(row) >= 2:
#             test_data.append(
#                 (os.path.join("preprocessing", "dataset", "test_clips", row[0]), row[1])
#             )


test_data = test_data[1:]
results = []


def load_audio(file):
    speech, sr = sf.read(file)
    if sr != 16000:
        import torchaudio

        resample = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
        speech = resample(torch.tensor(speech).float()).numpy()
    return speech


avg_error_cer = 0

for audio_file, reference in tqdm(test_data):
    speech = load_audio(audio_file)
    input_values = processor(
        speech, return_tensors="pt", sampling_rate=16000
    ).input_values

    with torch.no_grad():
        logits = model(input_values).logits

    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.tokenizer.decode(
        predicted_ids[0], skip_special_tokens=True
    )

    error_cer = cer(reference, transcription)
    avg_error_cer += round(error_cer, 3)

    results.append(
        {
            "Audio File": audio_file,
            "Reference": reference,
            "Prediction": transcription,
            "CER": round(error_cer, 3),
        }
    )

df = pd.DataFrame(results)
df.to_csv("stt_evaluation_results.csv", index=False)

print(df.to_markdown())
print("Average CER:", avg_error_cer / len(test_data))
