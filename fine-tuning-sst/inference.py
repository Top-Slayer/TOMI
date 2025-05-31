from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torch
import torchaudio
from datasets import Dataset
import pandas as pd
import shutil
import time


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        self.interval = self.end - self.start
        print(f"\nExecution time: {self.interval:.4f} seconds")


with Timer():
    model_path = "model/checkpoint-2130"
    shutil.copy("vocab.json", model_path)

    model = Wav2Vec2ForCTC.from_pretrained(model_path)
    processor = Wav2Vec2Processor.from_pretrained(model_path)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # speech_array, sampling_rate = torchaudio.load("sperated_dataset/test_clips/0.wav")
    speech_array, sampling_rate = torchaudio.load("test/gg.wav")
    if speech_array.shape[0] > 1:
        speech_array = speech_array.mean(dim=0)
    speech_array = speech_array.numpy()

    input_dict = processor(speech_array, return_tensors="pt", padding=True, sampling_rate=16000)
    logits = model(input_dict.input_values.to(device)).logits
    pred_ids = torch.argmax(logits, dim=-1)[0]

    raw_prediction = processor.decode(pred_ids)
    clean_prediction = raw_prediction.replace("[PAD]", "")

    test_trainscription = Dataset.from_pandas(
        pd.read_csv("sperated_dataset/test.tsv", sep="\t")
    )


    print("Raw Prediction (with special tokens):")
    print(raw_prediction)

    print("\nClean Prediction:")
    print(clean_prediction)

    print("\nReference:")
    print(test_trainscription[0]["sentence"])