use tonic::transport::{Server, ServerTlsConfig, Identity};
use tonic::{Request, Response, Status};
use audio::audio_service_server::{AudioService, AudioServiceServer};
use audio::{AudioData, AudioResponse};
use std::fs;

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

        println!("Format: {}, Sample rate: {}", data.format, data.sample_rate);
        println!("Audio size: {} bytes", data.audio_bytes.len());

        let bytes_metadata = shmem::Metadata {
            bytes: data.audio_bytes,
        };

        unsafe { shmem::write_metadata_to_shm(&bytes_metadata); }

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

    // tokio::spawn(async {
    //     shmem::read_audio();
    // });

    println!("AudioService server listening on {}", addr);

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