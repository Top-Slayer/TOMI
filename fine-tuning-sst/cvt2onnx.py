import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torchaudio

model_name = "model/checkpoint-3600"  
model = Wav2Vec2ForCTC.from_pretrained(model_name)
processor = Wav2Vec2Processor.from_pretrained(model_name)

model.eval()  

dummy_waveform = torch.randn(1, 16000)

inputs = processor(dummy_waveform.squeeze().numpy(), return_tensors="pt", sampling_rate=16000)
input_values = inputs["input_values"]

torch.onnx.export(
    model,                           # model being run
    (input_values,),                # model input (a tuple for dynamic axes)
    "wav2vec2.onnx",                # output file
    input_names=["input_values"],
    output_names=["logits"],
    dynamic_axes={
        "input_values": {1: "sequence_length"},  # variable-length audio
        "logits": {1: "sequence_length"},
    },
    opset_version=17,
    do_constant_folding=True
)
