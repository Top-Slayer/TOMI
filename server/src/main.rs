use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    response::IntoResponse,
    routing::get,
    Router,
};
use std::net::SocketAddr;
use tower_http::trace::TraceLayer;
use tracing_subscriber;
use pyo3::prelude::*;
use pyo3::types::{PyModule, PyList};

#[tokio::main]
async fn main() {
    pyo3::prepare_freethreaded_python();

    let initial_response = Python::with_gil(|py| -> PyResult<String> {
        let module = PyModule::from_code(
            py,
            include_str!("../../TOMI-project/test.py"),
            "TOMI-project/test.py",
            "test",
        )?;
        let greeting: String = module.getattr("greeting")?.call0()?.extract()?;
        Ok(greeting)
    });

    // println!("{:#?}", initial_response);

    tracing_subscriber::fmt::init();

    let app = Router::new()
        .route("/connect-ws-tomi", get(websocket_handler))
        .layer(TraceLayer::new_for_http());

    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    println!("WebSocket server running on ws://{}", addr);

    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}

async fn websocket_handler(ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
}

async fn handle_socket(mut socket: WebSocket) {
    if let Err(e) = socket.send(Message::Text("Connected to echo server".into())).await {
        println!("Failed to send welcome message: {}", e);
        return;
    }

    while let Some(msg) = socket.recv().await {
        match msg {
            Ok(msg) => {
                match msg {
                    Message::Text(text) => {
                        if let Err(e) = socket.send(Message::Text(format!("Echo: {}", text))).await {
                            println!("Failed to send message: {}", e);
                            break;
                        }
                    }
                    Message::Close(_) => {
                        println!("Client disconnected");
                        break;
                    }
                    _ => {
                        println!("Received non-text message");
                    }
                }
            }
            Err(e) => {
                println!("Error receiving message: {}", e);
                break;
            }
        }
    }

    if let Err(e) = socket.close().await {
        println!("Failed to close socket: {}", e);
    }
}