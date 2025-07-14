use axum::{
    routing::{get, post},
    Json, Router,
};

use once_cell::sync::Lazy;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::sync::RwLock;

use argon2::{
    password_hash::{PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
    Argon2,
};
use rand::rngs::OsRng;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Config {
    hostname: String,
    port: i32,
    password: Option<String>,
}

static CONFIG: Lazy<RwLock<Config>> = Lazy::new(|| {
    RwLock::new(Config {
        hostname: "xxxxxxxxxxxxx".to_string(),
        port: 0,
        password: Some({
            let salt = SaltString::generate(&mut OsRng);
            let argon2 = Argon2::default();
            argon2
                .hash_password(b"super_secret", &salt)
                .unwrap()
                .to_string()
        }),
    })
});

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/", get(root))
        .route("/get-config", get(get_config))
        .route("/set-config", post(set_config));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    println!("Server running on: http://{:?}", listener.local_addr().unwrap());

    axum::serve(listener, app).await.unwrap();
}

async fn root() -> &'static str {
    "Welcome to TOMI's config-file Server"
}

async fn get_config() -> Json<serde_json::Value> {
    let config = CONFIG.read().unwrap();

    Json(json!({
        "hostname": config.hostname,
        "port": config.port
    }))
}

async fn set_config(Json(payload): Json<Config>) -> &'static str {
    let argon2 = Argon2::default();

    let user_password = match &payload.password {
        Some(p) => p,
        None => return "❌ No password provided.",
    };

    let config = CONFIG.read().unwrap();
    let stored_hash = match &config.password {
        Some(h) => h,
        None => return "❌ No stored password to verify.",
    };

    let parsed_hash = PasswordHash::new(stored_hash).unwrap();

    if argon2
        .verify_password(user_password.as_bytes(), &parsed_hash)
        .is_err()
    {
        return "❌ Wrong password.";
    }

    drop(config);

    let mut config = CONFIG.write().unwrap();
    config.hostname = payload.hostname.clone();
    config.port = payload.port;

    "✅ Config updated."
}
