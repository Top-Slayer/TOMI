FROM debian:bookworm-slim

WORKDIR /app

COPY src/.env .
COPY target/release/serve-config app

EXPOSE 3000

CMD ["./app"]
