import numpy as np
import json
from multiprocessing import shared_memory, Manager
import mmap, struct, time, posix_ipc

MB = 1024 * 1024

IN_SIZE = 10 * MB
OUT_SIZE = 100 * MB

IN_SHM_NAME = "/in_shm"
OUT_SHM_NAME = "/out_shm"
SEM_NAME = "/signal"

# metadata = {
#     lengths
#     da
# }

in_shm = posix_ipc.SharedMemory(IN_SHM_NAME, posix_ipc.O_CREAT, size=IN_SIZE)
out_shm = posix_ipc.SharedMemory(OUT_SHM_NAME, posix_ipc.O_CREAT, size=OUT_SIZE)

sem = posix_ipc.Semaphore(SEM_NAME, posix_ipc.O_CREAT, initial_value=0)

out_mem = mmap.mmap(out_shm.fd, OUT_SIZE, mmap.MAP_SHARED, mmap.PROT_WRITE)


def read_audio():
    print("Waiting for semaphore...")
    sem.acquire()
    print("Semaphore acquired!")

    with mmap.mmap(in_shm.fd, IN_SIZE, mmap.MAP_SHARED, mmap.PROT_READ) as mem:
        mem.seek(0)

        lengths = struct.unpack("<Q", mem.read(8))[0]
        data = mem.read(lengths)

        print(f"lengths: {lengths}")
        print(f"bytes: {data[:100]}")

        return data


def write_audio(datas: bytes):
    length = len(datas)
    header = struct.pack("I", length)
    print(len(header))
    out_mem.seek(0)
    out_mem.write(header + datas)
    sem.release()

    # out_mem[: len(datas)] = datas
    # sem.release()


def close():
    in_shm.close_fd()
    out_mem.close()
    out_shm.close_fd()
    sem.close()
    posix_ipc.unlink_shared_memory(IN_SHM_NAME)
    posix_ipc.unlink_shared_memory(OUT_SHM_NAME)
    posix_ipc.unlink_semaphore(SEM_NAME)
