import os
import torch
import csv
import pandas as pd
import soundfile as sf
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from jiwer import cer, wer
from tqdm import tqdm
import argparse
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str)
parser.add_argument("--eval", type=str)
parser.add_argument("--denoise", type=bool, default=False)

model_path = ""

args = parser.parse_args()

if args.model is not None:
    model_path = args.model
else:
    print("Not using model.")
    exit(1)


shutil.copy("vocab.json", model_path)
print(f"Using model: {model_path}")

test_data = []

if args.eval == "unseen":
    #### Evaluation doesn't seen dataset ####
    with open("eval-dataset/eval.tsv", "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            test_data.append((os.path.join("eval-dataset", row[0]), row[1]))

elif args.eval == "seen":
    #### Evaluation test dataset ####
    with open("laos-transcript/test.tsv", "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) >= 2:
                test_data.append(
                    (os.path.join("laos-transcript", "test_clips", row[0]), row[1])
                )

else:
    print("Don't have that choice.")
    exit(1)

processor = Wav2Vec2Processor.from_pretrained(model_path)
model = Wav2Vec2ForCTC.from_pretrained(model_path)
model.eval()


test_data = test_data[1:]
results = []


#################################################################################################################
import torchaudio
from df.enhance import enhance, init_df

df_model, df_state, _ = init_df()


def denoise_input_sound(audio_path: str) -> str:
    waveform, sample_rate = torchaudio.load(audio_path)

    resampler = torchaudio.transforms.Resample(
        orig_freq=sample_rate, new_freq=df_state.sr()
    )
    waveform = resampler(waveform)
    sample_rate = df_state.sr()

    enhanced = enhance(df_model, df_state, waveform)

    audio_tensor = torch.as_tensor(enhanced)
    if audio_tensor.ndim == 1:
        audio_tensor = audio_tensor.unsqueeze_(0)

    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(
            orig_freq=sample_rate, new_freq=16000
        )
        audio_tensor = resampler(audio_tensor)
        sr = 16000
    else:
        sr = sample_rate

    if audio_tensor.dtype != torch.int16:
        audio_tensor = (audio_tensor * (1 << 15)).clamp(-32768, 32767).to(torch.int16)

    des_path = "denoise_file.wav"
    torchaudio.save(des_path, audio_tensor, sr, format="wav")

    return des_path


#################################################################################################################


def load_audio(file):
    speech, sr = sf.read(file)
    if sr != 16000:
        import torchaudio

        resample = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
        speech = resample(torch.tensor(speech).float()).numpy()
    return speech


avg_error_cer = 0
avg_error_wer = 0

for audio_file, reference in tqdm(test_data):
    if args.denoise:
        denoise_file = denoise_input_sound(audio_file)

        orig = torch.tensor(load_audio(audio_file), dtype=torch.float32)
        denoised = torch.tensor(load_audio(denoise_file), dtype=torch.float32)

        min_len = min(orig.shape[-1], denoised.shape[-1])
        orig = orig[..., :min_len]
        denoised = denoised[..., :min_len]

        print(
            "MSE denoise:", torch.mean((orig - denoised) ** 2)
        )  # if high that use more denoise

        audio_file = denoise_file

    speech = load_audio(audio_file)
    input_values = processor(
        speech, return_tensors="pt", sampling_rate=16000
    ).input_values

    with torch.no_grad():
        logits = model(input_values).logits

    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.tokenizer.decode(
        predicted_ids[0], skip_special_tokens=True
    ).replace("[PAD]", "")

    error_cer = cer(reference, transcription)
    error_wer = wer(reference, transcription)

    avg_error_cer += round(error_cer, 3)
    avg_error_wer += round(error_wer, 3)

    results.append(
        {
            "Audio File": audio_file,
            "Reference": reference,
            "Prediction": transcription,
            "CER": round(error_cer, 3),
            "WER": round(error_wer, 3),
        }
    )

df = pd.DataFrame(results)
df.to_csv("stt_evaluation_results.csv", index=False)

print(df.to_markdown())
print("Average CER:", avg_error_cer / len(test_data))
print("Average WER:", avg_error_wer / len(test_data))
