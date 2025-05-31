fn main() {
    prost_build::compile_protos(&["../protos/audio.proto"], &["../protos"]).unwrap();
}
