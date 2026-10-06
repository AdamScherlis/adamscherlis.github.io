"""Expose the local game server through a cloudflared quick tunnel, and publish
the tunnel's URL to nomic/backend.json on GitHub so the frontend at
adam.scherl.is/nomic can find the server.

Quick-tunnel URLs change whenever cloudflared restarts; each new URL is
committed to the default branch via the GitHub API (no local git changes).
GitHub Pages picks it up within a minute or two, and open pages re-read
backend.json when they lose contact with the server.

    uv run python tunnel.py [--port 8787] [--no-publish]
"""

import argparse
import base64
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLOUDFLARED = HERE / "bin" / "cloudflared"
URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
FILE_PATH = "nomic/backend.json"


def gh(*args, input=None):
    return subprocess.run(["gh", *args], input=input, capture_output=True, text=True, check=True).stdout


def repo_slug():
    url = subprocess.run(["git", "-C", str(HERE), "remote", "get-url", "origin"],
                         capture_output=True, text=True, check=True).stdout.strip()
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
    return m.group(1)


def publish(api_url):
    repo = repo_slug()
    branch = json.loads(gh("api", f"repos/{repo}"))["default_branch"]
    sha, current = None, None
    try:
        meta = json.loads(gh("api", f"repos/{repo}/contents/{FILE_PATH}?ref={branch}"))
        sha = meta["sha"]
        current = json.loads(base64.b64decode(meta["content"])).get("api")
    except subprocess.CalledProcessError:
        pass  # file doesn't exist yet
    if current == api_url:
        print(f"backend.json already points at {api_url}", flush=True)
        return
    content = json.dumps({"api": api_url, "updated": time.strftime("%Y-%m-%dT%H:%M:%S%z")},
                         indent=2) + "\n"
    body = {"message": "nomic: point frontend at the current game server tunnel",
            "content": base64.b64encode(content.encode()).decode(), "branch": branch}
    if sha:
        body["sha"] = sha
    gh("api", "-X", "PUT", f"repos/{repo}/contents/{FILE_PATH}", "--input", "-",
       input=json.dumps(body))
    print(f"Published {api_url} to {repo}:{branch}/{FILE_PATH}", flush=True)


def wait_until_reachable(url, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url + "/api/health", timeout=10) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(3)
    return False


def run_once(port, do_publish):
    proc = subprocess.Popen(
        [str(CLOUDFLARED), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    url = None
    for line in proc.stderr:
        sys.stderr.write(line)
        if url is None and (m := URL_RE.search(line)):
            url = m.group(0)
            print(f"Tunnel URL: {url}", flush=True)
            if wait_until_reachable(url):
                if do_publish:
                    for attempt in range(5):
                        try:
                            publish(url)
                            break
                        except subprocess.CalledProcessError as e:
                            print(f"Publishing failed ({e.stderr.strip()}); retrying", flush=True)
                            time.sleep(10 * (attempt + 1))
            else:
                print("Tunnel never became reachable; restarting it", flush=True)
                proc.terminate()
    return proc.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--no-publish", action="store_true")
    args = ap.parse_args()
    while True:
        code = run_once(args.port, not args.no_publish)
        print(f"cloudflared exited ({code}); restarting in 5s", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
