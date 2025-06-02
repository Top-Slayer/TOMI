from grpc_tools import protoc
import os

proto_dir = os.path.join("..", "protos")

proto_file = os.path.join(proto_dir, "audio.proto")

protoc.main([
    "",
    f"-I{proto_dir}",
    f"--python_out=.",
    f"--grpc_python_out=.",
    proto_file,
])

print("Build protobuf is successful")
