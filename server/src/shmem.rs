use bincode;
use libc::*;
use std::{ffi::CString, ptr, ptr::read_unaligned, sync::Mutex};

use crate::log_concat;

const IN_SHM: &str = "/in_shm";
const IN_SIZE: usize = 10 * 1024 * 1024;

const OUT_SHM: &str = "/out_shm";
const OUT_SIZE: usize = 100 * 1024 * 1024;

#[warn(unsafe_op_in_unsafe_fn)]
pub unsafe fn create_and_map_shm(name: &str, write: bool, size: usize) -> *mut u8 {
    let c_name = CString::new(name).unwrap();
    let flags = if write { O_CREAT | O_RDWR } else { O_RDONLY };
    let prot = if write {
        PROT_READ | PROT_WRITE
    } else {
        PROT_READ
    };

    let fd = unsafe { shm_open(c_name.as_ptr(), flags, S_IRUSR | S_IWUSR) };
    if fd == -1 {
        panic!("{}", log_concat!("shm_open failed: {}", name));
    }

    if write && unsafe { ftruncate(fd, size as i64) != 0 } {
        panic!("{}", log_concat!("ftruncate failed"));
    }

    let addr = unsafe { mmap(ptr::null_mut(), size, prot, MAP_SHARED, fd, 0) };
    if addr == MAP_FAILED {
        panic!("{}", log_concat!("mmap failed"));
    }

    unsafe { close(fd) };
    addr as *mut u8
}

pub unsafe fn clear_shm(name: &str) {
    let ptr = unsafe { create_and_map_shm(name, true, OUT_SIZE) };
    unsafe {
        ptr::write_bytes(ptr, 0, OUT_SIZE);
        libc::msync(ptr as *mut libc::c_void, OUT_SIZE, libc::MS_SYNC);
        munmap(ptr as *mut libc::c_void, OUT_SIZE);
    }
}

pub unsafe fn write_bytes_to_shm(bytes: &Vec<u8>) {
    let name = CString::new("/in_signal").expect(&log_concat!("CString failed"));
    let sem = unsafe { sem_open(name.as_ptr(), O_RDWR) };

    let ptr = unsafe { create_and_map_shm(IN_SHM, true, IN_SIZE) };
    let encoded = bincode::serialize(bytes).unwrap();
    assert!(encoded.len() <= IN_SIZE);
    unsafe { ptr.copy_from_nonoverlapping(encoded.as_ptr(), encoded.len()) };
    unsafe { munmap(ptr as *mut _, IN_SIZE) };

    unsafe { sem_post(sem) };
    println!(
        "{}",
        log_concat!("Release semaphore of '{}'", name.to_str().unwrap())
    );
    unsafe { sem_close(sem) };
}

fn vec_to_str(bytes: &[u8]) -> String {
    bytes
        .iter()
        .map(|b| format!("{:02X}", b))
        .collect::<Vec<_>>()
        .join(" ")
}

static OFFSET: Mutex<usize> = Mutex::new(8);

pub unsafe fn read_bytes_from_shm() -> Vec<u8> {
    let mut offset = OFFSET.lock().unwrap();
    let name = CString::new("/out_signal").expect(&log_concat!("CString failed"));
    let sem = unsafe { sem_open(name.as_ptr(), O_RDWR) };

    println!(
        "{}",
        log_concat!("Waiting for semaphore in '{}'", name.to_str().unwrap())
    );
    unsafe { sem_wait(sem) };
    println!(
        "{}",
        log_concat!("Semaphore acquired in '{}'", name.to_str().unwrap())
    );

    let ptr = unsafe { create_and_map_shm(OUT_SHM, false, OUT_SIZE) };
    if *offset + 5 > OUT_SIZE {
        println!(
            "{}",
            log_concat!(
                "Out of bounds while reading end-bytes at offset {}",
                *offset
            )
        );
        unsafe { munmap(ptr as *mut _, OUT_SIZE) };
        return vec![];
    }

    let slice = unsafe { std::slice::from_raw_parts(ptr.add(*offset), 5) };
    println!(
        "{}",
        log_concat!("Read end-bytes at {}-{} bytes", *offset, *offset + 5)
    );

    let result = String::from_utf8_lossy(slice).to_string();
    println!("{}", log_concat!("{:?}", result));
    if result == "<END>" {
        *offset = 8;
        println!("{}", log_concat!("Speech end"));
        unsafe { munmap(ptr as *mut _, OUT_SIZE) };
        return vec![];
    }

    let count = unsafe { read_unaligned(ptr as *const u64) };
    let mut wav_vec: Vec<u8> = Vec::new();

    if *offset + 8 > OUT_SIZE {
        println!("{}", log_concat!("Out of bounds while reading length"));
    }

    let length = unsafe { read_unaligned(ptr.add(*offset) as *const u64) as usize };
    *offset += 8;

    println!("{}", log_concat!("Lenght: {}", length));
    println!("{}", log_concat!("Offset: {}", *offset));

    if *offset + length > OUT_SIZE {
        println!(
            "{}",
            log_concat!("Out of bounds while reading bytes at entry {}", count)
        );
    }

    let wav_bytes = unsafe { std::slice::from_raw_parts(ptr.add(*offset), length) };
    wav_vec = wav_bytes.to_vec();

    println!("{}", log_concat!("Index: {}", count));
    println!("{}", log_concat!("Length: {} bytes", length));
    println!(
        "{}",
        log_concat!("Wav bytes: {}", {
            format!(
                "{} ... {}",
                vec_to_str(&wav_vec[..wav_vec.len().min(10)]),
                vec_to_str(&wav_vec[wav_vec.len().saturating_sub(10)..])
            )
        })
    );

    *offset += length;
    println!(
        "{}",
        log_concat!(
            "Used storage space in '{}': {:.2}%\n",
            OUT_SHM,
            *offset as f64 * 100.0 / OUT_SIZE as f64
        )
    );

    unsafe { munmap(ptr as *mut _, OUT_SIZE) };

    wav_vec
}
