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
total_minutes = total_seconds / 60
total_hours = total_seconds / 3600

# Final report
print("\n========== Summary ==========")
print(f"Total files found:        {total_files}")
print(f"Successfully loaded:      {success_count}")
print(f"Empty or unreadable:      {total_files - success_count}")
print(f"Total duration (seconds): {total_seconds:.2f}")
print(f"Total duration (minutes): {total_minutes:.2f}")
print(f"Total duration (hours):   {total_hours:.2f}")
if success_count > 0:
    print(f"Average duration/file:    {total_seconds / success_count:.2f} sec")