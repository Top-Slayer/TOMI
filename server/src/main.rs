use tonic::transport::{Server, ServerTlsConfig, Identity};
use tonic::{Request, Response, Status};
use futures_core::Stream;
use tokio_stream::wrappers::ReceiverStream;
use tokio::sync::mpsc;
use std::pin::Pin;
use std::sync::Arc;
use tokio::sync::Mutex;

pub mod audio {
    tonic::include_proto!("audio");
}

use audio::audio_service_server::{AudioService, AudioServiceServer};
use audio::{AudioData, AudioResponse};

#[macro_use]
mod logging;

mod shmem;

#[derive(Debug, Default)]
pub struct MyAudioService {
    pub state: Arc<Mutex<()>>,
}

type ResponseStream = Pin<Box<dyn Stream<Item = Result<AudioResponse, Status>> + Send>>;

#[tonic::async_trait]
impl AudioService for MyAudioService {
    type StreamAudioStream = ResponseStream;

    async fn stream_audio(
        &self,
        request: Request<tonic::Streaming<AudioData>>,
    ) -> Result<Response<Self::StreamAudioStream>, Status> {
        let mut stream = request.into_inner();
        let (tx, rx) = mpsc::channel(10);
        // let state = self.state.clone();

        tokio::spawn(async move {
            while let Ok(Some(data)) = stream.message().await {
                println!("{}", log_concat!("Format: {}, Sample rate: {}", data.format, data.sample_rate));
                println!("{}", log_concat!("Audio size: {} bytes", data.audio_bytes.len()));
                unsafe { shmem::write_bytes_to_shm(&data.audio_bytes); }
            }
            println!("{}", log_concat!("Client stopped sending audio."));
        });

        tokio::spawn(async move {
            loop {
                let processed = tokio::task::spawn_blocking(|| unsafe { shmem::read_bytes_from_shm() })
                .await
                .expect(&log_concat!("Blocking task panicked"));

                if processed.is_empty() || tx.send(Ok(AudioResponse { audio_bytes: processed })).await.is_err() {
                    unsafe { shmem::clear_shm("/out_shm"); }
                    println!("{}", log_concat!("Clear share memory"));
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
    let addr = "[::]:50051".parse()?;
    let service = MyAudioService::default();

    println!("{}", log_concat!("AudioService server listening on {}", addr));

    Server::builder()
        // .tls_config(ServerTlsConfig::new()
        //     .identity(Identity::from_pem(
        //         tokio::fs::read("../server.crt").await?,
        //         tokio::fs::read("../server.key").await?,
        //     ))
        // )?
        .add_service(AudioServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}