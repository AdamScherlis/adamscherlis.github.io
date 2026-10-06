#!/usr/bin/env bash
# Show whether the server and tunnel are up, and the recent tunnel log.
systemctl --user --no-pager status nomic-server nomic-tunnel | grep -E "●|Active:"
echo
journalctl --user -u nomic-tunnel --no-pager -n 200 | grep -E "Tunnel URL|Published|already points|exited|failed" | tail -5
echo
echo "Server log (last 5 lines):"
journalctl --user -u nomic-server --no-pager -n 5 -o cat
