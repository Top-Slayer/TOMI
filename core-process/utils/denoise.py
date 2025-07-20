from df.enhance import enhance, init_df
import torch
import torchaudio
import io

model, df_state, _ = init_df()


def denoise_input_sound(audio_bytes: bytes, debug=False) -> bytes:
    buffer = io.BytesIO(audio_bytes)

    waveform, sample_rate = torchaudio.load(buffer)
    resampler = torchaudio.transforms.Resample(
        orig_freq=sample_rate, new_freq=df_state.sr()
    )
    waveform = resampler(waveform)
    sample_rate = df_state.sr()

    enhanced = enhance(model, df_state, waveform)

    audio_tensor = torch.as_tensor(enhanced)
    if audio_tensor.ndim == 1:
        audio_tensor = audio_tensor.unsqueeze_(0)

    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(
            orig_freq=sample_rate, new_freq=16000
        )
        audio_tensor = resampler(audio_tensor)
        sr = 16000

    if audio_tensor.dtype != torch.int16:
        audio_tensor = (audio_tensor * (1 << 15)).clamp(-32768, 32767).to(torch.int16)

    audio_buffer = io.BytesIO()
    torchaudio.save(audio_buffer, audio_tensor, sr, format="wav")
    audio_buffer.seek(0)

    if debug:
        torchaudio.save("./tmp/debug_denoise.wav", audio_tensor, sr, format="wav")

    return audio_buffer.getvalue()
