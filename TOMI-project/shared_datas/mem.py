# shared_audio.py
import numpy as np
from multiprocessing import shared_memory

dtype = np.int16
nbytes = 1 * 1024 * 1024 * 1024 # 1 GiB
lists = []

shm = shared_memory.SharedMemory(create=True, size=nbytes)

def write_audio(data: np.ndarray):
    print(shm.buf)
    buffer = np.ndarray((len(data),), dtype=dtype, buffer=shm.buf)
    buffer[:] = 0
    buffer[:len(data)] = data
    lists.append(buffer.copy())

def get_shared_info():
    return shm.name, (nbytes,), dtype

def get_all_audio():
    return lists

def close():
    shm.close()

def unlink():
    shm.unlink()
