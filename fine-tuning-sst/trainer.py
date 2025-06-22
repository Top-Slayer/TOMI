# Load dataset
from datasets import Dataset
from evaluate import load as load_metric
import pandas as pd
import torchaudio
import numpy as np
import re
import json
import os


# repo_name = "wav2vec2-large-xls-r-300m-lao"


# from dotenv import load_dotenv
# load_dotenv()
# import huggingface_hub
# huggingface_hub.login(token=os.getenv("HUGGING_FACE_API"))


df = pd.read_csv("laos-transcript/train.tsv", sep="\t")
train_ds = Dataset.from_pandas(df)

df = pd.read_csv("laos-transcript/test.tsv", sep="\t")
test_ds = Dataset.from_pandas(df)


# Convert Audio to array datas
def get_speech_file_to_array(base_path):
    def speech_file_to_array(batch):
        full_path = os.path.join(base_path, batch["path"])
        speech_array, sampling_rate = torchaudio.load(full_path)

        if speech_array.shape[0] > 1:
            speech_array = speech_array.mean(dim=0, keepdim=True)

        audio_array = speech_array[0].numpy()

        if not isinstance(audio_array, np.ndarray):
            print(f"Warning: Expected numpy array but got {type(audio_array)}")
            audio_array = np.array(audio_array)

        batch["audio"] = {
            "array": audio_array,
            "sampling_rate": sampling_rate,
        }

        return batch

    return speech_file_to_array


train_ds = train_ds.map(get_speech_file_to_array("laos-transcript/train_clips"))
test_ds = test_ds.map(get_speech_file_to_array("laos-transcript/test_clips"))


# Remove some special character
chars_to_remove_regex = "[\,\?\.\!\-\;\:\"\“\%\‘\”\�']"


def remove_special_characters(batch):
    batch["sentence"] = re.sub(chars_to_remove_regex, "", batch["sentence"]).lower()
    return batch


train_ds = train_ds.map(remove_special_characters)
test_ds = test_ds.map(remove_special_characters)


# Extract all chars and save into vocab.json file
def extract_all_chars(batch):
    all_text = " ".join(batch["sentence"])
    vocab = list(set(all_text))
    return {"vocab": [vocab], "all_text": [all_text]}


vocab_train = train_ds.map(
    extract_all_chars,
    batched=True,
    batch_size=-1,
    keep_in_memory=True,
    remove_columns=train_ds.column_names,
)
vocab_test = test_ds.map(
    extract_all_chars,
    batched=True,
    batch_size=-1,
    keep_in_memory=True,
    remove_columns=test_ds.column_names,
)
vocab_list = list(set(vocab_train["vocab"][0]) | set(vocab_test["vocab"][0]))
vocab_dict = {v: k for k, v in enumerate(sorted(vocab_list))}
vocab_dict["|"] = vocab_dict[" "]
del vocab_dict[" "]
vocab_dict["[UNK]"] = len(vocab_dict)
vocab_dict["[PAD]"] = len(vocab_dict)

with open("vocab.json", "w") as f:
    json.dump(vocab_dict, f, indent=6, ensure_ascii=False)


# Tokenizer
from transformers import Wav2Vec2CTCTokenizer

tokenizer = Wav2Vec2CTCTokenizer.from_pretrained(
    "./", unk_token="[UNK]", pad_token="[PAD]", word_delimiter_token="|"
)

print(tokenizer.tokenize(text=train_ds["sentence"][0]))
# tokenizer.push_to_hub(repo_name)


# Sampling rate of audio
from transformers import Wav2Vec2FeatureExtractor

feature_extractor = Wav2Vec2FeatureExtractor(
    feature_size=1,
    sampling_rate=16000,
    padding_value=0.0,
    do_normalize=True,
    return_attention_mask=False,
)
# feature_extractor.push_to_hub(repo_name)


# Define processor
from transformers import Wav2Vec2Processor

processor = Wav2Vec2Processor(feature_extractor=feature_extractor, tokenizer=tokenizer)
# processor.push_to_hub(repo_name)


# Test random output
# ======================================================================
import torch
import random

rand_int = random.randint(0, len(train_ds) - 1)

sample = train_ds[rand_int]
print(sample["sentence"])

audio_tensor = torch.tensor(sample["audio"]["array"]).unsqueeze(0)
sampling_rate = 16000

torchaudio.save("output.wav", audio_tensor, sampling_rate)
# ======================================================================


# Show random audio properties
# ======================================================================
rand_int = random.randint(0, len(train_ds) - 1)

print("Target text:", train_ds[rand_int]["sentence"])
print("Input array shape:", len(train_ds[rand_int]["audio"]["array"]))
print("Sampling rate:", train_ds[rand_int]["audio"]["sampling_rate"])
# ======================================================================


def prepare_dataset(batch):
    audio = batch["audio"]["array"]
    sampling_rate = batch["audio"]["sampling_rate"]

    batch["input_values"] = processor(audio, sampling_rate=sampling_rate).input_values[
        0
    ]
    batch["labels"] = processor(text=batch["sentence"]).input_ids
    return batch


train_ds = train_ds.map(prepare_dataset)
test_ds = test_ds.map(prepare_dataset)


# ============================ Trainer ============================
import torch

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class DataCollatorCTCWithPadding:
    processor: Wav2Vec2Processor
    padding: Union[bool, str] = True

    def __call__(
        self, features: List[Dict[str, Union[List[int], torch.Tensor]]]
    ) -> Dict[str, torch.Tensor]:
        input_features = [
            {"input_values": feature["input_values"]} for feature in features
        ]
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        batch = self.processor.pad(
            input_features,
            padding=self.padding,
            return_tensors="pt",
        )
        with self.processor.as_target_processor():
            labels_batch = self.processor.pad(
                label_features,
                padding=self.padding,
                return_tensors="pt",
            )

        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )

        batch["labels"] = labels

        return batch


data_collator = DataCollatorCTCWithPadding(processor=processor, padding=True)
wer_metric = load_metric("wer")
cer_metric = load_metric("cer")


def compute_metrics(pred):
    pred_logits = pred.predictions
    pred_ids = np.argmax(pred_logits, axis=-1)
    pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id

    pred_str = processor.batch_decode(pred_ids, skip_special_tokens=True)
    label_ids = np.where(
        pred.label_ids != -100, pred.label_ids, processor.tokenizer.pad_token_id
    )
    label_str = processor.batch_decode(
        label_ids, group_tokens=False, skip_special_tokens=True
    )

    wer = wer_metric.compute(predictions=pred_str, references=label_str)
    cer = cer_metric.compute(predictions=pred_str, references=label_str)

    return {"wer": wer, "cer": cer}


from transformers import Wav2Vec2ForCTC

model = Wav2Vec2ForCTC.from_pretrained(
    "facebook/wav2vec2-xls-r-300m",
    attention_dropout=0.0,
    hidden_dropout=0.0,
    feat_proj_dropout=0.0,
    mask_time_prob=0.05,
    layerdrop=0.0,
    ctc_loss_reduction="mean",
    pad_token_id=processor.tokenizer.pad_token_id,
    vocab_size=len(processor.tokenizer),
    ignore_mismatched_sizes=True,
)

# model.freeze_feature_extractor()
model.freeze_feature_encoder()

from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="model",
    group_by_length=True,
    per_device_train_batch_size=8,
    gradient_accumulation_steps=4,
    eval_strategy="steps",
    num_train_epochs=60,
    gradient_checkpointing=True,
    fp16=True,
    save_steps=200,
    eval_steps=200,
    logging_steps=50,
    learning_rate=5e-5,
    warmup_steps=1000,
    save_total_limit=3,
    lr_scheduler_type ="linear",
    push_to_hub=False,
    dataloader_num_workers=2,
    warmup_ratio=0.1,
)

from transformers import Trainer

trainer = Trainer(
    model=model,
    data_collator=data_collator,
    args=training_args,
    compute_metrics=compute_metrics,
    train_dataset=train_ds,
    eval_dataset=test_ds,
    processing_class=processor.feature_extractor,
)

trainer.train()
# trainer.push_to_hub()
