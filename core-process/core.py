from multiprocessing import Process, cpu_count, shared_memory
import time
from functions import tts, stt
from shared_datas import mem
import numpy as np
import mmap, struct, posix_ipc

model_name = "gemma3:12b"
system_prompt = """
      You are a helpful assistant specialized in Lao academic and historical knowledge.

      [System Instruction]
      - Only answer questions in the Lao language.
      - If asked about unrelated topics, politely refuse.
      - Respond in full sentences using formal language.
      - Your name is "ທູມິ"
"""


def audio_reader(name, shape, dtype, offsets):
    shm = shared_memory.SharedMemory(name=name)
    # shared_array = np.ndarray(shape, dtype=dtype, buffer=shm.buf)

    while True:
        print(len(offsets))
        for i, (start, length) in enumerate(offsets):
            audio = mem.shared_array[start : start + length]
            print(f"Audio[{i}] (length={length}) => {audio[:10]}...")
        time.sleep(1)


def view_mem():
    SHM_NAME = "/in_shm"
    SEM_NAME = "/signal"
    SIZE = 100 * 1024 * 1024

    shm = posix_ipc.SharedMemory(SHM_NAME)
    sem = posix_ipc.Semaphore(SEM_NAME)

    mem = mmap.mmap(shm.fd, SIZE, mmap.MAP_SHARED, mmap.PROT_READ)

    while True:
        print("⏳ Waiting for data...")
        sem.acquire()

        data_len_bytes = mem[0:4]
        data_len = struct.unpack("i", data_len_bytes)[0]

        data = mem[4:4+data_len]

        print(f"✅ Received {data_len} bytes: {data[:32]}...")


if __name__ == "__main__":
    try:
        while 1:
            # p = Process(target=view_mem)
            # p.start()

            # in_bytes = mem.read_audio()
            # text = stt.transcript(in_bytes)
            # print("stt output:", text)
            # tts.synthesize(text)
            # chat2llm.chat(text)

            with open("test_16k.wav", "rb") as f:
                mem.write_audio(f.read())
                print("Write datas successfully")

            in_bytes = mem.read_audio()
            time.sleep(10)

    except KeyboardInterrupt:
        pass
    finally:
        # p.terminate()
        mem.close()


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
