use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    response::IntoResponse,
    routing::get,
    Router,
};
use std::net::SocketAddr;
use tokio::fs::File;
use tokio::io::AsyncWriteExt;
use futures::{StreamExt};

pub mod audio {
    include!(concat!(env!("OUT_DIR"), "/audio.rs"));
}

#[tokio::main]
async fn main() {
    let audio = audio::AudioPacket{
        data: vec![1, 2, 3, 4],
        sample_rate: 16000,
        channels: 1,
        format: "wav".to_string(),
    };

    let app = Router::new().route("/ws", get(handle_ws_upgrade));

    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    println!("Listening on: {}", addr);
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}

async fn handle_ws_upgrade(ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
}

async fn handle_socket(mut socket: WebSocket) {
    let mut file = File::create("received_audio.wav")
        .await
        .expect("Failed to create file");

    while let Some(Ok(msg)) = socket.next().await {
        match msg {
            Message::Binary(data) => {
                if let Err(e) = file.write_all(&data).await {
                    eprintln!("Write error: {}", e);
                    break;
                }
            }
            Message::Close(_) => {
                println!("Connection closed");
                break;
            }
            _ => {}
        }
    }

    println!("Done receiving audio");
}
