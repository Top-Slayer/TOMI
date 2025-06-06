use bincode;
use hound::{SampleFormat, WavSpec, WavWriter};
use libc::*;
use serde::{Deserialize, Serialize};
use std::{ffi::CString, fs::File, io::BufWriter, ptr, ptr::read_unaligned, slice};

use std::io::Write;

use crate::log_concat;

const IN_SHM: &str = "/in_shm";
const IN_SIZE: usize = 10 * 1024 * 1024;

const OUT_SHM: &str = "/out_shm";
const OUT_SIZE: usize = 100 * 1024 * 1024;

pub unsafe fn create_and_map_shm(name: &str, write: bool, size: usize) -> *mut u8 {
    let c_name = CString::new(name).unwrap();
    let flags = if write { O_CREAT | O_RDWR } else { O_RDONLY };
    let prot = if write {
        PROT_READ | PROT_WRITE
    } else {
        PROT_READ
    };

    let fd = shm_open(c_name.as_ptr(), flags, S_IRUSR | S_IWUSR);
    if fd == -1 {
        panic!("{}", log_concat!("shm_open failed: {}", name));
    }

    if write && ftruncate(fd, size as i64) != 0 {
        panic!("{}", log_concat!("ftruncate failed"));
    }

    let addr = mmap(ptr::null_mut(), size, prot, MAP_SHARED, fd, 0);
    if addr == MAP_FAILED {
        panic!("{}", log_concat!("mmap failed"));
    }

    close(fd);
    addr as *mut u8
}

pub unsafe fn write_bytes_to_shm(bytes: &Vec<u8>) {
    let name = CString::new("/in_signal").expect(&log_concat!("CString failed"));
    let sem = sem_open(name.as_ptr(), O_RDWR);

    let ptr = create_and_map_shm(IN_SHM, true, IN_SIZE);
    let encoded = bincode::serialize(bytes).unwrap();
    assert!(encoded.len() <= IN_SIZE);
    ptr.copy_from_nonoverlapping(encoded.as_ptr(), encoded.len());
    munmap(ptr as *mut _, IN_SIZE);

    sem_post(sem);
    sem_close(sem);
}

fn vec_to_str(bytes: &[u8]) -> String {
    bytes
        .iter()
        .map(|b| format!("{:02X}", b))
        .collect::<Vec<_>>()
        .join(" ")
}

pub unsafe fn read_bytes_from_shm() -> std::io::Result<()> {
    let ptr = create_and_map_shm(OUT_SHM, false, OUT_SIZE);
    let count = read_unaligned(ptr as *const u64);
    let mut offset: usize = 8;
    let mut wav_vec: Vec<u8> = Vec::new();

    for i in 0..count {
        if offset + 8 > OUT_SIZE {
            println!("{}", log_concat!("Out of bounds while reading length"));
            break;
        }

        let length = read_unaligned(ptr.add(offset) as *const u64) as usize;
        offset += 8;

        if offset + length > OUT_SIZE {
            println!(
                "{}",
                log_concat!("Out of bounds while reading bytes at entry {}", i)
            );
            break;
        }

        let wav_bytes = std::slice::from_raw_parts(ptr.add(offset), length);
        wav_vec = wav_bytes.to_vec();

        println!("{}", log_concat!("Index: {}", i));
        println!("{}", log_concat!("Length: {}", length));
        println!(
            "{}",
            log_concat!("Wav_bytes: {}\n", {
                format!(
                    "{} ... {}",
                    vec_to_str(&wav_vec[..wav_vec.len().min(10)]),
                    vec_to_str(&wav_vec[wav_vec.len().saturating_sub(10)..])
                )
            })
        );

        offset += length;
        println!("{}", log_concat!("Used storage space in '{}': {:.2} %", OUT_SHM, offset as f64 * 100.0 / OUT_SIZE as f64));
    }

    munmap(ptr as *mut _, OUT_SIZE);

    let mut file = File::create("output.wav")?;
    file.write_all(&wav_vec)?;
    Ok(())
}
