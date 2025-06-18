#!/bin/bash

export OLLAMA_NUM_GPU_LAYERS=128

NUM=0
LOCAL_PORT=50051
OUTPUT_FILE="config_tunnel.json"
LLM_MODEL="gemma3:12b-it-q4_K_M"

if ! which ngrok >/dev/null 2>&1; then
    echo "⬇️ Installing Ngrok..."
    curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
        | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
        && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
        | sudo tee /etc/apt/sources.list.d/ngrok.list \
        && sudo apt update \
        && sudo apt install ngrok
fi

ngrok tcp "$LOCAL_PORT" --region=ap > /dev/null &

echo "Waiting for ngrok tunnel to be ready..."
for i in {1..10}; do
    url=$(curl -s http://127.0.0.1:4040/api/tunnels)
    if [[ -n "$url" ]]; then
        break
    fi
    sleep 1
done

if [[ -z "$url" ]]; then
    echo "❌ Failed to get ngrok tunnel URL."
    exit 1
fi

url=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[].public_url')
hostport=${url#tcp://}
hostname=${hostport%%:*}
port=${hostport##*:}

json=$(jq -n --arg hostname "$hostname" --argjson port "$port" \
    '{hostname: $hostname, port: $port}')

echo -e "Export config tunnel:\n$json"
echo "$json" > "$OUTPUT_FILE"



if ! which ollama >/dev/null 2>&1; then
    echo "⬇️ Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

tmux new-session -d -s "tomi"

tmux select-pane -t $NUM
tmux send-keys "sudo systemctl stop ollama" C-m
tmux send-keys "sudo systemctl disable ollama" C-m
tmux send-keys "ollama serve" C-m

NUM=$((NUM + 1))
tmux split-window -v

tmux select-pane -t $NUM
tmux send-keys "cd core-process/ && python core.py" C-m

NUM=$((NUM + 1))
tmux split-window -v

sleep 3

tmux select-pane -t $NUM
tmux send-keys "ollama pull $LLM_MODEL" C-m
tmux send-keys "cd server/ && cargo run" C-m


tmux attach -t "tomi"