use std::fs;

fn main() -> Result<(), Box<dyn std::error::Error>>{
    let proto_dir = "../protos";
    let mut protos = Vec::new();

    for entry in fs::read_dir(proto_dir).unwrap() {
        if let Ok(entry) = entry {
            let path = entry.path();
            if path.extension().map(|s| s == "proto").unwrap_or(false) {
                protos.push(path);
            }
        }
    }

    tonic_build::configure()
        .build_server(true)
        .compile(&protos, &[proto_dir])
        .expect("Failed to compile .proto files");
    Ok(())
}