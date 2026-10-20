#!/usr/bin/env bash
# Upload one local file into a Drive resumable-upload session opened by
# workbench/drive_bridge.py (open_upload / open_update).
#   drive_put.sh FILE SESSION_URL [MIME]
# Prints the Drive file JSON and the local md5 so the caller can compare it
# with the md5Checksum Drive reports.
set -euo pipefail
file="$1"; url="$2"; mime="${3:-}"
if [ -z "$mime" ]; then
  case "$file" in
    *.jpg|*.jpeg) mime=image/jpeg ;;
    *.png) mime=image/png ;;
    *.json) mime=application/json ;;
    *) mime=application/octet-stream ;;
  esac
fi
for attempt in 1 2 3; do
  if resp=$(curl -sS --fail-with-body -X PUT -H "Content-Type: $mime" --data-binary @"$file" "$url"); then
    echo "$resp"
    echo "{\"local_md5\": \"$(md5sum "$file" | cut -d' ' -f1)\", \"bytes\": $(stat -c%s "$file")}"
    exit 0
  fi
  echo "upload attempt $attempt failed: $resp" >&2
  sleep $((attempt * 5))
done
exit 1
