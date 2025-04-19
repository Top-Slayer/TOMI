import numpy as np
from multiprocessing import shared_memory, Manager

shape = (100 * 1024 * 1024,)  # 100 MiB
dtype = np.int16
nbytes = shape[0] * np.dtype(dtype).itemsize

shm = shared_memory.SharedMemory(create=True, size=nbytes)
shared_array = np.ndarray(shape, dtype=dtype, buffer=shm.buf)
shared_array[:] = 0

manager = Manager()
offsets = manager.list()
cursor = manager.Value("i", 0)


def write_audio(data: np.ndarray):
    cur = cursor.value
    if cur + len(data) > shape[0]:
        print("❌ Not enough space")
        return
    shared_array[cur : cur + len(data)] = data
    offsets.append((cur, len(data)))
    cursor.value += len(data)


def get_shared_info():
    return shm.name, shape, dtype, offsets, cursor


def close():
    shm.close()
    shm.unlink()
