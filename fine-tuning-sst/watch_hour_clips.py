import os
import torchaudio

folder_path = "sperated_dataset/train_clips"
total_seconds = 0

for filename in os.listdir(folder_path):
    if filename.endswith(".wav") or filename.endswith(".mp3"):
        filepath = os.path.join(folder_path, filename)
        try:
            waveform, sample_rate = torchaudio.load(filepath)
            duration = waveform.shape[1] / sample_rate
            total_seconds += duration
        except Exception as e:
            print(f"Error reading {filename}: {e}")

total_hours = total_seconds / 3600
print(f"Total duration: {total_hours:.2f} hours")
