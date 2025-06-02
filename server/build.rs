fn main() {
    tonic_build::compile_protos("../protos/audio.proto").unwrap();
}
