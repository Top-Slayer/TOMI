use byteorder::{ByteOrder, LittleEndian};
use ndarray::ArrayView;
use shared_memory::*;
use std::fs;
use std::slice;
use std::{thread, time::Duration};
use memmap2::{MmapMut, MmapOptions};
use std::fs::OpenOptions;

// try to access via share memory that allocate specific only

pub fn write() {
   let file = OpenOptions::new()
        .read(true)
        .write(true)
        .open("/dev/shm/in_shm")
        .expect("Could not open");

    let mut mmap = unsafe {
        MmapOptions::new()
            .len(100 * 1024 * 1024) // 100 MiB
            .map_mut(&file)
            .expect("Failed to mmap")
    };

    // Write a few i16 values (2 bytes each)
    let buffer: &mut [i16] = unsafe {
        std::slice::from_raw_parts_mut(mmap.as_mut_ptr() as *mut i16, 100 * 1024 * 1024 / 2)
    };

    buffer[0..5].copy_from_slice(&[1, 2, 3, 4, 5]);

    println!("✅ Wrote to shared memory!");
}

pub fn read() -> Result<(), Box<dyn std::error::Error>> {
    let offsets: &Vec<(usize, usize)> = &vec![];
    let shape: &[usize] = &[];

    let shm = ShmemConf::new().os_id("out_shm").open()?;
    let total_elements: usize = shape.iter().product();
    let audio_data: &[f32] = unsafe {
        let ptr = shm.as_ptr() as *const f32;
        slice::from_raw_parts(ptr, total_elements)
    };

    loop {
        println!("Offsets len: {}", offsets.len());
        for (i, (start, length)) in offsets.iter().enumerate() {
            let end = start + length;
            if end > audio_data.len() {
                println!("Invalid offset range: {} to {}", start, end);
                continue;
            }

            let segment = &audio_data[*start..end];
            let preview: Vec<f32> = segment.iter().take(10).cloned().collect();
            println!("Audio[{}] (length={}) => {:?}...", i, length, preview);
        }

        thread::sleep(Duration::from_secs(1));
    }
}

// pub fn name() {
//     pyo3::prepare_freethreaded_python();

//     Python::with_gil(|py| {
//         let module = PyModule::from_code(
//             py,
//             include_str!("../../TOMI-project/interface.py"),
//             "interface.py",
//             "interface",
//         )
//         .unwrap();

//         let val: i32 = module.getattr("shm_name").unwrap().extract().unwrap();
//         println!("my_value: {}", val);
//     });
// }
