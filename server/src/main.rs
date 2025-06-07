use tonic::transport::{Server}; // ServerTlsConfig, Identity
use tonic::{Request, Response, Status};
use audio::audio_service_server::{AudioService, AudioServiceServer};
use audio::{AudioData, AudioResponse};
use tokio_stream::wrappers::ReceiverStream;
use tokio::sync::mpsc;
use std::pin::Pin;
use futures_core::Stream;

#[macro_use]
mod logging;

mod shmem;

pub mod audio {
    tonic::include_proto!("audio");
}

#[derive(Debug, Default)]
pub struct MyAudioService {}

type ResponseStream = Pin<Box<dyn Stream<Item = Result<AudioResponse, Status>> + Send>>;

#[tonic::async_trait]
impl AudioService for MyAudioService {
    type UploadAudioStream = ResponseStream;

    async fn upload_audio(
        &self,
        request: Request<AudioData>,
    ) -> Result<Response<Self::UploadAudioStream>, Status> {
        let data = request.into_inner();

        println!("{}", log_concat!("Format: {}, Sample rate: {}", data.format, data.sample_rate));
        println!("{}", log_concat!("Audio size: {} bytes", data.audio_bytes.len()));

        unsafe { shmem::write_bytes_to_shm(&data.audio_bytes); }

        let (tx, rx) = mpsc::channel(10);

        tokio::spawn(async move {
            loop {
                let audio = unsafe { shmem::read_bytes_from_shm() };

                let response = AudioResponse {
                    audio_bytes: audio,
                };

                if tx.send(Ok(response)).await.is_err() {
                    println!("{}", log_concat!("Client disconnected!"));
                    break; 
                }

                tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            }
        });

        Ok(Response::new(Box::pin(ReceiverStream::new(rx))))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // let cert = fs::read("server.pem")?;
    // let key = fs::read("server.key")?;
    // let identity = Identity::from_pem(cert, key);

    let addr = "[::]:50051".parse()?;
    let service = MyAudioService::default();

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