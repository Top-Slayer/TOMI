use tonic::transport::{Server, ServerTlsConfig, Identity};
use tonic::{Request, Response, Status};
use audio::audio_service_server::{AudioService, AudioServiceServer};
use audio::{AudioData, AudioResponse};
use std::fs;
use std::{thread, time};

#[macro_use]
mod logging;

mod shmem;

pub mod audio {
    tonic::include_proto!("audio");
}

#[derive(Debug, Default)]
pub struct MyAudioService {}

#[tonic::async_trait]
impl AudioService for MyAudioService {
    async fn upload_audio(
        &self,
        request: Request<AudioData>,
    ) -> Result<Response<AudioResponse>, Status> {
        let data = request.into_inner();

        println!("{}", log_concat!("Format: {}, Sample rate: {}", data.format, data.sample_rate));
        println!("{}", log_concat!("Audio size: {} bytes", data.audio_bytes.len()));

        unsafe { shmem::write_bytes_to_shm(&data.audio_bytes); }

        let reply = AudioResponse {
            message: "Audio received successfully!".to_string(),
        };

        Ok(Response::new(reply))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cert = fs::read("server.pem")?;
    let key = fs::read("server.key")?;
    let identity = Identity::from_pem(cert, key);

    let addr = "[::]:50051".parse()?;
    let service = MyAudioService::default();

    tokio::spawn(async {
        loop {
            unsafe { shmem::read_bytes_from_shm(); }
            thread::sleep(time::Duration::from_secs(5));
        }
    });

    println!("{}", log_concat!("AudioService server listening on {}", addr));

    Server::builder()
        // .tls_config(tonic::transport::ServerTlsConfig::new()
        //     .identity(tonic::transport::Identity::from_pem(
        //         std::fs::read("server.pem")?,
        //         std::fs::read("server.key")?,
        //     ))
        // )?
        .add_service(AudioServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}