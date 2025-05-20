from pydub import AudioSegment
import os, shutil

# paths = ["sperated_dataset/train_clips", "sperated_dataset/test_clips"]

# for path in paths:
#     for f in os.listdir(path):
#         file_path = os.path.join(path, f)
#         sound = AudioSegment.from_file(file_path)
#         resampled = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
#         resampled.export(file_path, format="wav")

file_path = "test/test.ogg"
sound = AudioSegment.from_file(file_path)
resampled = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
file_name, _ = os.path.splitext(file_path)
file_name = file_name + ".wav"
shutil.move(file_path, file_name)
resampled.export(file_name, format="wav")