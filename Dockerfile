FROM debian:bullseye-slim

RUN apt update && apt-get install -y \
    libssl1.1 \
    ca-certificates

WORKDIR /app

COPY server/target/debug/server /app
COPY server.crt /
COPY server.key /

EXPOSE 50051

CMD ["./server"]
