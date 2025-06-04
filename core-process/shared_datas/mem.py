import numpy as np
import json
from multiprocessing import shared_memory, Manager
import mmap, struct, time, posix_ipc

MB = 1024 * 1024

IN_SIZE = 10 * MB
OUT_SIZE = 100 * MB

IN_SHM_NAME = "/in_shm"
OUT_SHM_NAME = "/out_shm"

IN_SEM_NAME = "/in_signal"
OUT_SEM_NAME = "/out_signal"


in_shm = posix_ipc.SharedMemory(IN_SHM_NAME, posix_ipc.O_CREAT, size=IN_SIZE)
out_shm = posix_ipc.SharedMemory(OUT_SHM_NAME, posix_ipc.O_CREAT, size=OUT_SIZE)

in_sem = posix_ipc.Semaphore(IN_SEM_NAME, posix_ipc.O_CREAT, initial_value=0)
out_sem = posix_ipc.Semaphore(OUT_SEM_NAME, posix_ipc.O_CREAT, initial_value=0)


def read_audio():
    print("Waiting for semaphore...")
    in_sem.acquire()
    print("Semaphore acquired!")

    with mmap.mmap(in_shm.fd, IN_SIZE, mmap.MAP_SHARED, mmap.PROT_READ) as mem:
        mem.seek(0)

        lengths = struct.unpack("<Q", mem.read(8))[0]
        data = mem.read(lengths)

        # print(f"lengths: {lengths}")
        # print(f"bytes: {data[:100]}...")

        return data


write_offset = 8
write_count = 0


def write_audio(wav_bytes: bytes):
    with mmap.mmap(out_shm.fd, OUT_SIZE, mmap.MAP_SHARED, mmap.PROT_WRITE) as mem:
        global write_offset, write_count

        write_count += 1
        length = len(wav_bytes)

        header = struct.pack("Q", length)
        entry = header + wav_bytes
        entry_size = len(entry)

        if write_offset + entry_size > OUT_SIZE:
            raise ValueError("Shared memory full")

        mem.seek(0)
        mem.write(struct.pack("Q", write_count))

        mem.seek(write_offset)
        mem.write(entry)
        mem.flush()

        write_offset += entry_size
        out_sem.release()


def close():
    in_shm.close_fd()
    out_shm.close_fd()
    in_sem.close()
    out_sem.close()
    posix_ipc.unlink_shared_memory(IN_SHM_NAME)
    posix_ipc.unlink_shared_memory(OUT_SHM_NAME)
    posix_ipc.unlink_semaphore(IN_SEM_NAME)
    posix_ipc.unlink_semaphore(OUT_SEM_NAME)
