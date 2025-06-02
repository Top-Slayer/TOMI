use tonic::{transport::Server, Request, Response, Status};
use audio::audio_service_server::{AudioService, AudioServiceServer};
use audio::{AudioData, AudioResponse};

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

        // You can write the audio to a file
        std::fs::write("output.wav", &data.audio_bytes)
            .expect("Failed to write audio file");

        let reply = AudioResponse {
            message: "Audio received successfully!".to_string(),
        };

        Ok(Response::new(reply))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    let service = MyAudioService::default();

    println!("AudioService server listening on {}", addr);

    Server::builder()
        .add_service(AudioServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}
