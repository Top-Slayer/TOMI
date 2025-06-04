FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl1.1 \
    ca-certificates \

WORKDIR /app

COPY server/target/debug/server /app
COPY server/server.key /app
COPY server/server.pem /app

EXPOSE 1212

CMD ["./server"]
