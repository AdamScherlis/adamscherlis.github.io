#!/usr/bin/env bash
# Start the game server and its public tunnel as systemd user services.
# They keep running after this shell exits (but not across reboots or logouts).
set -euo pipefail
cd "$(dirname "$0")"
PORT="${NOMIC_PORT:-8787}"
UV="$(command -v uv)"

if [ ! -x bin/cloudflared ]; then
    mkdir -p bin
    curl -fsSL -o bin/cloudflared \
        https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
    chmod +x bin/cloudflared
fi
"$UV" sync -q

systemd-run --user --unit=nomic-server --collect -p Restart=on-failure -p RestartSec=3 \
    --working-directory="$PWD" -- "$UV" run python -m nomic_server serve --port "$PORT"
systemd-run --user --unit=nomic-tunnel --collect -p Restart=on-failure -p RestartSec=5 \
    --working-directory="$PWD" -- "$UV" run python tunnel.py --port "$PORT"

echo "Started. Check on it with ./status.sh; stop with ./stop.sh"
