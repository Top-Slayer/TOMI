import threading
from multiprocessing import Process, cpu_count, shared_memory
import math
import time

# from function import EmotionalRecognition
# from function import PlaySound
from functions import chat2llm
from shared_datas import mem
import numpy as np


def audio_reader(name, shape, dtype):
    shm = shared_memory.SharedMemory(name=name)
    while True:
        print(mem.get_all_audio())
        time.sleep(1)



if __name__ == "__main__":
    try:
        shm_name, shape, dtype = mem.get_shared_info()
        p = Process(target=audio_reader, args=(shm_name, shape, dtype))
        p.start()

        chat2llm.chat("ສະບາຍດີທູມິ")

        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        p.terminate()
        mem.close()
        mem.unlink()

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
