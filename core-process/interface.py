from multiprocessing import Process, cpu_count, shared_memory
import time

# from function import EmotionalRecognition
# from function import PlaySound
from functions import chat2llm
from functions import tts, stt

# from functions import voice_changer as vc
from shared_datas import mem
import numpy as np
import mmap, struct, posix_ipc


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

            text = stt.transcript(mem.read_audio())
            print("stt output:", text)
            # tts.synthesize(text)
            chat2llm.chat(text)

    except KeyboardInterrupt:
        pass
    finally:
        # p.terminate()
        mem.close()

# threading.Thread(target=EmotionalRecognition.openCamera).start()

# while 1:
#     # print(
#     #     f"{EmotionalRecognition.play_sound_key} && {PlaySound.enabled} | Emotional: {EmotionalRecognition.text}"
#     # )

#     if EmotionalRecognition.play_sound_key and PlaySound.enabled:
#         threading.Thread(
#             target=PlaySound.playSound, args=(EmotionalRecognition.text,)
#         ).start()


########### test multitasking
# def heavy_task(n):
#     print(f"Starting task {n}")
#     result = 0
#     for i in range(1, 10_000_000):
#         result += math.sqrt(i)
#     print(f"Finished task {n}")

# if __name__ == "__main__":
#     start = time.time()

#     processes = []
#     for i in range(cpu_count()):  # Use all available cores
#         p = Process(target=heavy_task, args=(i,))
#         processes.append(p)
#         p.start()

#     for p in processes:
#         p.join()

#     print("Total time:", time.time() - start)
