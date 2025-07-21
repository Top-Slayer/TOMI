from transformers import (
    Wav2Vec2ForCTC,
    Wav2Vec2FeatureExtractor,
    Wav2Vec2Processor,
)
import json
import argparse
import os
import torchaudio
import pandas as pd
from huggingface_hub import upload_folder
from importlib.metadata import version

parser = argparse.ArgumentParser()
parser.add_argument("--path", type=str)
args = parser.parse_args()

checkpoint_path = args.path
log_path = "model/runs"

repo_name = "TopSlayer/wav2vec2-large-xls-r-300m-lao"


def get_duration(path: str):
    total_seconds = 0
    total_files = 0
    success_count = 0
    empty_count = 0

    for root, _, files in os.walk(path):
        for filename in files:
            if filename.endswith(".wav") or filename.endswith(".mp3"):
                total_files += 1
                filepath = os.path.join(root, filename)

                if os.path.getsize(filepath) == 0:
                    print(f"Skipping empty file: {filename}")
                    empty_count += 1
                    continue

                try:
                    waveform, sample_rate = torchaudio.load(filepath)
                    duration = waveform.shape[1] / sample_rate
                    total_seconds += duration
                    success_count += 1
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60

    return hours, minutes, remaining_seconds


custom_jsons = []
with open(os.path.join(checkpoint_path, "trainer_state.json"), "r") as f:
    data = json.load(f)

for i, key in enumerate(data["log_history"]):
    if "eval_loss" in key:
        entry = {
            "train_loss": data["log_history"][i - 1]["loss"],
            "epoch": data["log_history"][i]["epoch"],
            "step": data["log_history"][i]["step"],
            "eval_loss": data["log_history"][i]["eval_loss"],
            "wer": data["log_history"][i]["eval_wer"],
            "cer": data["log_history"][i]["eval_cer"],
        }
        custom_jsons.append(entry)


headers = ["Training Loss", "Epoch", "Step", "Evaluation Loss", "WER", "CER"]

header_to_key = {
    "Training Loss": "train_loss",
    "Epoch": "epoch",
    "Step": "step",
    "Evaluation Loss": "eval_loss",
    "WER": "wer",
    "CER": "cer",
}

rows_md = "\n".join(
    "| "
    + " | ".join(
        (
            f"{row.get(header_to_key[h]):.4f}"
            if isinstance(row.get(header_to_key[h]), float)
            else str(row.get(header_to_key[h]) or "")
        )
        for h in headers
    )
    + " |"
    for row in custom_jsons
)

table_md = f"""
| {' | '.join(headers)} |
|{'|'.join([':' + '-'*(len(h)-2) + ':' for h in headers])}|
{rows_md}
"""


tokenizer = Wav2Vec2ForCTC.from_pretrained(checkpoint_path)
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(checkpoint_path)
processor = Wav2Vec2Processor.from_pretrained(checkpoint_path)

h, m, s = get_duration("laos-transcript/train_clips")
duration_str = f"{int(h)}h {int(m)}m {int(s)}s"

samples = len(pd.read_csv("laos-transcript/train.tsv", sep="\t"))

with open(f"{checkpoint_path}/README.md", "w") as f:
    f.write(
        f"""
---
base_model: facebook/wav2vec2-xls-r-300m
metrics:
- wer, cer
---

# Model

This model is a fine-tuned version of [facebook/wav2vec2-xls-r-300m](https://huggingface.co/facebook/wav2vec2-xls-r-300m) on the None dataset.
It achieves the following results on the evaluation set:
- Eval-Loss: {custom_jsons[-1]["eval_loss"]}
- WER: {custom_jsons[-1]["wer"]}
- CER: {custom_jsons[-1]["cer"]}

### Dataset details
- duration: {duration_str}
- samples: {samples}

### Training results
{table_md}

### Framework versions

- Transformers {version('transformers')}
- Pytorch {version('torch')}
- Datasets {version('datasets')}
- Tokenizers {version('tokenizers')}
"""
    )

upload_folder(repo_id=repo_name, folder_path=log_path)
upload_folder(repo_id=repo_name, folder_path=checkpoint_path)
