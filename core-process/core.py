import time
import os
from functions import tts, stt, chat2llm, voice_changer as vc
from utils import shmem, denoise
from utils import logging as lg

# model_name = "gemma3:12b-it-q4_K_M"
# system_prompt = """
#       You are a helpful assistant and friendly emotion.

#       [System Instruction]
#       - Only answer questions in the Lao language.
#       - If asked about unrelated topics, politely refuse.
#       - Respond in full sentences using formal language.
#       - Your name is "ທູມິ"
# """


if __name__ == "__main__":
    os.makedirs("tmp", exist_ok=True)

    try:
        while 1:
            in_bytes = shmem.read_bytes_from_shm()
            denoise_bytes = denoise.denoise_input_sound(in_bytes, debug=True)
            text = stt.transcript(denoise_bytes)
            print(lg.log_concat("STT output:", text))
            chat2llm.chat(text)
            shmem.add_end_to_shm()

            time.sleep(10)

    except KeyboardInterrupt:
        pass
    finally:
        # p.terminate()
        shmem.close()


# def chat(user_prompt: str, debug=False):
#     prompt = f"""
#       {system_prompt}
#       [User Question]
#       {user_prompt}
#       """

#     sentense = ""

#     try:
#         response = requests.post(
#             "http://localhost:11434/api/generate",
#             json={
#                 "model": model_name,
#                 "prompt": prompt,
#                 "num_predict": 100,
#                 "stream": True,
#             },
#             stream=True,
#         )
#     except Exception as e:
#         print(f"--- Have Something wrong with ollama server [try to open server again] ---\n{e}")
#         return

#     for line in response.iter_lines():
#         if line:
#             try:
#                 data = line.decode("utf-8")
#                 json_data = json.loads(data)
#                 sentense += json_data["response"]

#                 print(json_data["response"], end="", flush=True)

#                 if json_data["response"] in " ":
#                     tts.synthesize(sentense)
#                     sentense = ""

#             except json.JSONDecodeError as e:
#                 print(f"\nJSON Decode Error: {e}")

#     if sentense != "":
#         tts.synthesize(sentense)
