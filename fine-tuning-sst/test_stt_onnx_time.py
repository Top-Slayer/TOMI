from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import onnxruntime as ort
import torchaudio
import numpy as np
import torch
import time

model_path = "../../fine-tuning-sst/model/checkpoint-2130"
onnx_model_path = "wav2vec2.onnx"

model = Wav2Vec2ForCTC.from_pretrained(model_path)
processor = Wav2Vec2Processor.from_pretrained(model_path)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

session = ort.InferenceSession(onnx_model_path)

print("STT model path:", model_path)
print("ONNX model path:", onnx_model_path)


def transcript_onnx(path: str) -> str:
    speech_array, sampling_rate = torchaudio.load(path)
    if speech_array.shape[0] > 1:
        speech_array = speech_array.mean(dim=0)
    speech_array = speech_array.numpy()

    input_dict = processor(
        speech_array, return_tensors="np", padding=True, sampling_rate=sampling_rate
    )

    input_name = session.get_inputs()[0].name
    logits = session.run(None, {input_name: input_dict["input_values"]})[0]
    pred_ids = np.argmax(logits, axis=-1)[0]
    clean_prediction = processor.decode(pred_ids).replace("[PAD]", "")

    return clean_prediction


def transcript(path: str) -> str:
    speech_array, sampling_rate = torchaudio.load(path)

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


if __name__ == "__main__":
    num = 100

    start_time = time.time()
    for _ in range(num):
        transcript("../test_16k.wav")
    end_time = time.time()
    pyth_time = end_time - start_time
    print(f"PyTorch Elapsed time: {pyth_time}", end="\n\n")

    start_time = 0
    end_time = 0

    start_time = time.time()
    for _ in range(num):
        transcript_onnx("../test_16k.wav")
    end_time = time.time()
    onnx_time = end_time - start_time
    print(f"ONNX Elapsed time: {onnx_time}", end="\n\n")


    print("ONNX faster than PyTorch:", pyth_time / onnx_time)