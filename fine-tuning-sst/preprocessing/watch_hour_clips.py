import os
import torchaudio

folder_path = "../laos-transcript/train_clips"
total_seconds = 0
total_files = 0
success_count = 0
empty_count = 0

for root, _, files in os.walk(folder_path):
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

# Convert to time units
hours = total_seconds // 3600
minutes = (total_seconds % 3600) // 60
remaining_seconds = total_seconds % 60

print(f"{hours} hours, {minutes} minutes, {remaining_seconds} seconds")