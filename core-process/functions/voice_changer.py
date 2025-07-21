# python voice_changer_2.py && python -m rvc_python cli -i audio.wav -o output.wav -mp mikuAI/MikuAI.pth -ip mikuAI/added_IVF3010_Flat_nprobe_1_v2.index -rsr 16000 -rmr 16000 -pi 12

from rvc_python.infer import RVCInference
from pydub import AudioSegment
import os, io
import wave


out_file = os.path.join("tmp", "alr_vc.wav")

rvc = RVCInference(
    device="cuda:0",
    model_path="mikuAI/MikuAI.pth",
    index_path="mikuAI/added_IVF3010_Flat_nprobe_1_v2.index",
)
rvc.set_params(f0up_key=10, f0method="rmvpe")


def change_voice(in_file: str) -> bytes:
    rvc.infer_file(in_file, out_file)

    sound = AudioSegment.from_file(out_file)
    resampled = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    buffer = io.BytesIO()
    resampled.export(buffer, format="wav")
    return buffer.getvalue()
