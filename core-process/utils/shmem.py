import mmap, struct, posix_ipc
from . import logging as lg

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


def read_bytes_from_shm():
    print(lg.log_concat(f"Waiting for semaphore in '{IN_SEM_NAME}'"))
    in_sem.acquire()
    print(lg.log_concat(f"Semaphore acquired in '{IN_SEM_NAME}'"))

    with mmap.mmap(in_shm.fd, IN_SIZE, mmap.MAP_SHARED, mmap.PROT_READ) as mem:
        mem.seek(0)

        lengths = struct.unpack("<Q", mem.read(8))[0]
        data = mem.read(lengths)
        # print(lg.log_concat(f"Used storage space in '{IN_SEM_NAME}: {}%'"))

        return data


write_offset = 8
write_count = 0


def write_bytes_to_shm(wav_bytes: bytes):
    with mmap.mmap(out_shm.fd, OUT_SIZE, mmap.MAP_SHARED, mmap.PROT_WRITE) as mem:
        global write_offset, write_count

        write_count += 1

        length = struct.pack("Q", len(wav_bytes))
        entry = length + wav_bytes
        entry_size = len(entry)

        if write_offset + entry_size > OUT_SIZE:
            raise ValueError(lg.log_concat("Shared memory full"))

        mem.seek(0)
        mem.write(struct.pack("Q", write_count))

        mem.seek(write_offset)
        mem.write(entry)
        mem.flush()

        write_offset += entry_size
        out_sem.release()
        print(lg.log_concat(f"Release semaphore of '{OUT_SEM_NAME}'"))


def add_end_to_shm():
    with mmap.mmap(out_shm.fd, OUT_SIZE, mmap.MAP_SHARED, mmap.PROT_WRITE) as mem:
        global write_offset, write_count
        mem.seek(write_offset)
        mem.write(b"<END>")
        mem.flush()

        mem.seek(write_offset)
        print(lg.log_concat(f"Read at {write_offset + 5} bytes"))
        data = mem.read(5)
        print(data)

        write_offset = 8
        write_count = 0


def close():
    in_shm.close_fd()
    out_shm.close_fd()
    in_sem.close()
    out_sem.close()
    posix_ipc.unlink_shared_memory(IN_SHM_NAME)
    posix_ipc.unlink_shared_memory(OUT_SHM_NAME)
    posix_ipc.unlink_semaphore(IN_SEM_NAME)
    posix_ipc.unlink_semaphore(OUT_SEM_NAME)
