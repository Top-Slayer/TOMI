import numpy as np
import json
from multiprocessing import shared_memory, Manager
import mmap, struct, time, posix_ipc

SIZE_MB = 100
SIZE = SIZE_MB * 1024 * 1024

SHM_NAME = "/in_shm"
SEM_NAME = "/signal"

shm = posix_ipc.SharedMemory(SHM_NAME, posix_ipc.O_CREAT, size=SIZE)
sem = posix_ipc.Semaphore(SEM_NAME, posix_ipc.O_CREAT, initial_value=0)

mem = mmap.mmap(shm.fd, SIZE, mmap.MAP_SHARED, mmap.PROT_WRITE)


def write_audio(datas: bytes):
    # cur = cursor.value
    # if cur + len(data) > shape[0]:
    #     print("❌ Not enough space")
    #     return
    # shared_array[cur : cur + len(data)] = data
    # offsets.append((cur, len(data)))
    # cursor.value += len(data)

    # length_bytes = struct.pack("i", len(datas))
    mem[:len(datas)] = datas
    sem.release()


def close():
    mem.close()
    shm.close_fd()
    sem.close()
    posix_ipc.unlink_shared_memory(SHM_NAME)
    posix_ipc.unlink_semaphore(SEM_NAME)
