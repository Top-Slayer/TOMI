use bincode;
use hound::{SampleFormat, WavSpec, WavWriter};
use libc::*;
use serde::{Deserialize, Serialize};
use std::{ffi::CString, fs::File, io::BufWriter, ptr, slice};

#[derive(Serialize, Deserialize, Debug)]
pub struct Metadata {
    pub bytes: Vec<u8>,
}

const IN_SHM: &str = "/in_shm";
const IN_SIZE: usize = 10 * 1024 * 1024;

const OUT_SHM: &str = "/out_shm";
const OUT_SIZE: usize = 100 * 1024 * 1024;


pub unsafe fn create_and_map_shm(name: &str, write: bool, size: usize) -> *mut u8 {
    let c_name = CString::new(name).unwrap();
    let flags = if write { O_CREAT | O_RDWR } else { O_RDONLY };
    let prot = if write { PROT_READ | PROT_WRITE } else { PROT_READ };

    let fd = shm_open(c_name.as_ptr(), flags, S_IRUSR | S_IWUSR);
    if fd == -1 {
        panic!("shm_open failed: {}", name);
    }

    if write && ftruncate(fd, size as i64) != 0 {
        panic!("ftruncate failed");
    }

    let addr = mmap(ptr::null_mut(), size, prot, MAP_SHARED, fd, 0);
    if addr == MAP_FAILED {
        panic!("mmap failed");
    }

    close(fd);
    addr as *mut u8
}

pub unsafe fn write_metadata_to_shm(metadata: &Metadata) {
    let name = CString::new("/signal").expect("CString failed");
    let sem = sem_open(name.as_ptr(), O_RDWR);

    let ptr = create_and_map_shm(IN_SHM, true, IN_SIZE);
    let encoded = bincode::serialize(metadata).unwrap();
    assert!(encoded.len() <= IN_SIZE);
    ptr.copy_from_nonoverlapping(encoded.as_ptr(), encoded.len());
    munmap(ptr as *mut _, IN_SIZE);

    sem_post(sem);
    sem_close(sem);
}

pub unsafe fn read_metadata_from_shm() -> Metadata {
    let ptr = create_and_map_shm(OUT_SHM, false, OUT_SIZE);
    let data = slice::from_raw_parts(ptr, OUT_SIZE);
    let metadata: Metadata = bincode::deserialize(data).expect("Deserialization failed");
    munmap(ptr as *mut _, OUT_SIZE);
    metadata
}

pub fn read_audio() {
    let shm_name = CString::new("/out_shm").unwrap();
    let sem_name = CString::new("/signal").unwrap();
    let size = 100 * 1024 * 1024;

    unsafe {
        let shm_fd = shm_open(shm_name.as_ptr(), O_RDONLY, 0);
        if shm_fd == -1 {
            panic!("❌ Failed to open shared memory");
        }

        let mem_ptr = mmap(ptr::null_mut(), size, PROT_READ, MAP_SHARED, shm_fd, 0);
        if mem_ptr == libc::MAP_FAILED {
            panic!("❌ Failed to mmap");
        }

        let sem = sem_open(sem_name.as_ptr(), 0);
        if sem == libc::SEM_FAILED {
            panic!("❌ Failed to open semaphore");
        }

        loop {
            println!("🕐 Waiting for signal...");
            sem_wait(sem);
            println!("✅ Received signal");

            let len_ptr = mem_ptr as *const u32;
            let data_len = *len_ptr as usize;

            let sample_count = data_len / std::mem::size_of::<i16>();
            println!("{}", sample_count);
            let pcm_data = slice::from_raw_parts(mem_ptr.add(4) as *const i16, sample_count);

            let spec = WavSpec {
                channels: 1,
                sample_rate: 16000,
                bits_per_sample: 16,
                sample_format: SampleFormat::Int,
            };

            let file = File::create("output.wav").expect("❌ Failed to create file");
            let writer = BufWriter::new(file);

            let mut wav_writer = WavWriter::new(writer, spec).expect("❌ Failed to write header");

            for &sample in pcm_data {
                wav_writer
                    .write_sample(sample)
                    .expect("❌ Failed to write sample");
            }

            wav_writer.finalize().expect("❌ Failed to finalize WAV");
            println!("Success write")
        }
    }
}
