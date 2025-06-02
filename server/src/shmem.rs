use hound::{SampleFormat, WavSpec, WavWriter};
use libc::{close, mmap, sem_open, sem_wait, shm_open, MAP_SHARED, O_RDONLY, PROT_READ};
use std::{ffi::CString, fs::File, io::BufWriter, ptr, slice};

pub fn read_audio() {
    let shm_name = CString::new("/in_shm").unwrap();
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

            let sample_count = 60 * 1024 / std::mem::size_of::<i16>();
            let pcm_data = slice::from_raw_parts(mem_ptr as *const i16, sample_count);

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
