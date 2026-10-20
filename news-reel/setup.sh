#!/usr/bin/env bash
# One-time setup per session for the reel renderer: npm deps (playwright + fonts) and the node_modules link.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d logo-motion/node_modules/playwright ] || npm ci --prefix logo-motion --no-audit --no-fund
[ -e news-reel/node_modules ] || ln -s ../logo-motion/node_modules news-reel/node_modules
command -v ffmpeg >/dev/null || { echo "ffmpeg missing"; exit 1; }
ls /opt/pw-browsers/chromium-*/chrome-linux/chrome >/dev/null
echo "reel setup ok"
