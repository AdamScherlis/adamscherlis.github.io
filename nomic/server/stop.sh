#!/usr/bin/env bash
# Stop the tunnel and the game server. Game state is kept in data/.
systemctl --user stop nomic-tunnel nomic-server
