#!/bin/bash

# sh <(curl --proto '=https' --tlsv1.2 -L https://nixos.org/nix/install) --daemon --yes   # Install nix packages. manager
# mkdir -p ~/.config/nix
# echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf


export OLLAMA_NUM_GPU_LAYERS=128

NUM=0
LOCAL_PORT=50051
VC_DIR="core-process/mikuAI"
OUTPUT_FILE="config_tunnel.json"
LLM_MODEL="gemma3:12b-it-q4_K_M"
URL=""
PASS=""

for arg in "$@"
do
    case $arg in
        URL=*)
            URL="${arg#*=}"
            shift
        ;;
        PASS=*)
            PASS="${arg#*=}"
            shift
        ;;
    esac
done

if [[ -z "$URL" || -z "$PASS" ]]; then
    echo "Error: Required URL and PASS args."
    echo "Usage: $0 URL=url_path PASS=password"
    exit 1
fi

if [ ! -d "$VC_DIR" ] || [ -z "$(ls -A "$VC_DIR")" ]; then
    echo "Directory not found: $VC_DIR"
    mkdir -p "$VC_DIR"
    echo "Created directory: $VC_DIR"
    curl -L https://huggingface.co/yaniroo/YanAI/resolve/main/MikuAI.zip -o "$VC_DIR/MikuAI.zip"
    unzip "$VC_DIR/MikuAI.zip" -d "$VC_DIR" && rm "$VC_DIR/MikuAI.zip"
else 
    echo "Directory exists: $VC_DIR"
fi

if ! which ngrok >/dev/null 2>&1; then
    echo "⬇️ Installing Ngrok..."
    curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
    | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
    && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
    | sudo tee /etc/apt/sources.list.d/ngrok.list \
    && sudo apt update \
    && sudo apt install ngrok
fi

if pgrep ngrok > /dev/null; then
    echo "Restarting ngrok..."
    pkill ngrok
fi

ngrok tcp "$LOCAL_PORT" --region=ap > /dev/null &

echo "Waiting for ngrok tunnel to be ready..."
for i in {1..10}; do
    url=$(curl -s http://127.0.0.1:4040/api/tunnels)
    if [[ -n "$url" ]]; then
        break
    fi
    sleep 3
done

if [[ -z "$url" ]]; then
    echo "❌ Failed to get ngrok tunnel URL."
    exit 1
fi

if ! which jq >/dev/null 2>&1; then
    echo "⬇️ Installing jq command..."
    sudo apt install jq
fi

url=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[].public_url')
hostport=${url#tcp://}
hostname=${hostport%%:*}
port=${hostport##*:}

curl -X POST "$URL" \
-H "Content-Type: application/json" \
-d "{\"hostname\": \"$hostname\", \"port\": $port, \"password\": \"$PASS\"}"

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
tmux send-keys "cd core-process" C-m
tmux send-keys "python core.py" C-m

NUM=$((NUM + 1))
tmux split-window -v

sleep 3

tmux select-pane -t $NUM
tmux send-keys "ollama pull $LLM_MODEL" C-m
tmux send-keys "cd server/" C-m
tmux send-keys "cargo run" C-m


tmux attach -t "tomi"