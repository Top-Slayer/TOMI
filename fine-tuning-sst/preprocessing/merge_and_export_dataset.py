import pandas as pd
import os
import shutil
from pydub import AudioSegment
import wave
import contextlib


old_name = "old_dataset"
new_name = "set_3"


# Move dataset to old_dataset

# if input("Move dataset to old_dataset or not [y/n]").lower() == "y":
#     if os.path.exists(old_name):
#         shutil.rmtree(old_name)
#     shutil.move("dataset", old_name)

os.makedirs(os.path.join("temp", "train_clips"), exist_ok=True)

df1 = pd.read_csv(os.path.join(old_name, "train.tsv"), sep="\t")
df2 = pd.read_csv(os.path.join(new_name, "train.tsv"), sep="\t")


def is_valid_wav(file_path):
    try:
        with contextlib.closing(wave.open(file_path, 'rb')) as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frame_rate = wf.getframerate()
            comp_type = wf.getcomptype()

            return (
                channels == 1 and           # mono
                sample_width == 2 and       # 16-bit = 2 bytes
                frame_rate == 16000 and     # 16kHz
                comp_type == 'NONE'         # PCM
            )
    except wave.Error:
        return False 


def copy_no_overwrite(src_dir, dst_dir, filename):
    src_path = os.path.join(src_dir, filename)
    dst_path = os.path.join(dst_dir, filename)

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    if not os.path.exists(src_path):
        print(f"Not found: {src_path}")
        return

    if not os.path.exists(dst_path):
        shutil.copy(src_path, dst_path)
        print(f"Copied: {dst_path}")
    else:
        print(f"Skipped (already exists): {dst_path}")


merged_df = pd.merge(df1, df2, on="sentence", indicator=True, how="outer")
print("Complete merge")

for path in merged_df["path_x"].dropna().tolist():
    copy_no_overwrite(os.path.join(old_name, "train_clips"), os.path.join("temp", "train_clips"), path)
print(f"Moving clips of {old_name} successfully")
    
for path in merged_df["path_y"].dropna().tolist():
    copy_no_overwrite(os.path.join(new_name, "wait_clips"), os.path.join("temp", "train_clips"), path)
print(f"Moving clips of {new_name} successfully")

merged_df["path"] = merged_df["path_y"].combine_first(merged_df["path_x"])
merged_df = merged_df.drop(columns=["path_x", "path_y"])
merged_df = merged_df[["path", "sentence"]]
merged_df.to_csv("temp/train.tsv", sep="\t", index=False)
print(f"Export train.tsv in temp dir successfully")


# filter dup files
df = pd.read_csv("temp/train.tsv", sep="\t", encoding="utf-8")
duplicates = df[df.duplicated(subset=['sentence'], keep="first")]

print("Duplicate rows:")
for i, row in duplicates.iterrows():
    os.remove(os.path.join("temp", "train_clips", row["path"]))
    print("Remove:", row["path"], row["sentence"])

df_clean = df.drop_duplicates(subset=["sentence"], keep="first")
df_clean.to_csv("temp/train.tsv", sep="\t", index=False, encoding="utf-8")
print("<-- Delete all duplicated files -->")


clip_dir = os.path.join("temp", "train_clips")

for clip in os.listdir(clip_dir):
    path = os.path.join(clip_dir, clip)

    if is_valid_wav(path):
        print(f"File {clip} is valid")
        continue

    sound = AudioSegment.from_file(path)
    resampled = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    file_name, _ = os.path.splitext(path)
    file_name = file_name + ".wav"
    shutil.move(path, file_name)
    resampled.export(file_name, format="wav")
    print(f"Change propertie of {clip} complete")


# Export to dataset dir
valid_rows = []
export_df = pd.read_csv(os.path.join("temp", "train.tsv"), sep="\t")

os.makedirs(os.path.join("dataset", "train_clips"), exist_ok=True)

for i, row in export_df.iterrows():
    src_path = os.path.join("temp", "train_clips", row["path"])
    dst_path = os.path.join("dataset", "train_clips", f"{i}.wav")

    if os.path.exists(src_path):
        shutil.copy(src_path, dst_path)
        export_df.at[i, "path"] = f"{i}.wav"
        valid_rows.append(i)
    else:
        print("Ignore (file not found):", row["path"])


export_df = export_df.loc[valid_rows].reset_index(drop=True)
export_df.to_csv(os.path.join("dataset", "train.tsv"), sep="\t", index=False)

shutil.copytree(os.path.join(old_name, "test_clips"), os.path.join("dataset", "test_clips"), dirs_exist_ok=True)
shutil.copy(os.path.join(old_name, "test.tsv"), os.path.join("dataset", "test.tsv"))

print("Done.")