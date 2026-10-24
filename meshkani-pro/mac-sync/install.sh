#!/bin/bash
# Nightly local copy of meshkani.pro content (user request 2026-10-24).
# Run once on the Mac:  bash install.sh
# - installs rclone (own copy, no sudo) and connects it to Google Drive read-only (browser sign-in)
# - copies Reels / Posts / Stories / Map from Drive into DEST, sorted by category and date folder
# - schedules it every night at 23:45; if the Mac was asleep, it runs as soon as it wakes,
#   and if it was off, it runs at the next login
set -euo pipefail

DEST="/Users/mahdimeshkani/Documents/My Works/Meshkani.pro/Instagram"
APP="$HOME/Applications/MeshkaniSync"
RCLONE="$APP/rclone"
CONF="$APP/rclone.conf"
LABEL="pro.meshkani.instagram-sync"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/meshkani-instagram-sync.log"

# Drive folder ids (meshkani-pro/config.json)
REELS=1p_z_InykkRzQW5HD6GMNbJu_K3k959ki
POSTS=10o8f4dqZ7cT4_MLZHrluER0eLUlkc7Tn
STORIES=1AGGy6FdgvG3Aa1igu38RNN3m7Eb-wmJ0
MAP=1v5-Ml8y4pt85uah36NGyz2Jn8kIOB-rT

mkdir -p "$APP" "$DEST" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"

# 1. rclone: a real binary (not a Homebrew symlink) so the Full Disk Access grant survives upgrades
if [ ! -x "$RCLONE" ]; then
  case "$(uname -m)" in arm64) arch=arm64 ;; *) arch=amd64 ;; esac
  tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/rc.zip" "https://downloads.rclone.org/rclone-current-osx-$arch.zip"
  unzip -q "$tmp/rc.zip" -d "$tmp"
  cp "$tmp"/rclone-*/rclone "$RCLONE"; chmod +x "$RCLONE"
  xattr -d com.apple.quarantine "$RCLONE" 2>/dev/null || true
  rm -rf "$tmp"
fi

# 2. Drive connection, read-only. Opens the browser once for Google sign-in.
if ! "$RCLONE" --config "$CONF" listremotes | grep -qx 'meshkani:'; then
  echo "A browser window will open: sign in with mahdi.meshkani@gmail.com and allow read-only access."
  "$RCLONE" --config "$CONF" config create meshkani drive scope=drive.readonly
fi
"$RCLONE" --config "$CONF" config delete meshkani-ig 2>/dev/null || true
"$RCLONE" --config "$CONF" config create meshkani-ig combine \
  upstreams="Reels=meshkani,root_folder_id=$REELS: Posts=meshkani,root_folder_id=$POSTS: Stories=meshkani,root_folder_id=$STORIES: Map=meshkani,root_folder_id=$MAP:" >/dev/null

# 3. The copy itself: only dated content folders (YYYY-MM-DD_…) and the map; never deletes local files
cat > "$APP/filters.txt" <<'F'
+ /Reels/20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]*/**
+ /Posts/20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]*/**
+ /Stories/20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]*/**
+ /Map/**
- *
F
BASE=(copy meshkani-ig: "$DEST" --config "$CONF" --filter-from "$APP/filters.txt" --drive-skip-gdocs
      --transfers 4 --retries 5 --low-level-retries 20)
ARGS=("${BASE[@]}" --log-file "$LOG" --log-level INFO --stats-one-line)

# 4. launchd job: 23:45 nightly, catch-up on wake (launchd runs a missed calendar job after sleep) and at login
{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
  echo '<plist version="1.0"><dict>'
  echo "  <key>Label</key><string>$LABEL</string>"
  echo '  <key>ProgramArguments</key><array>'
  echo "    <string>$RCLONE</string>"
  for a in "${ARGS[@]}"; do
    a=${a//&/&amp;}; a=${a//</&lt;}; a=${a//>/&gt;}
    echo "    <string>$a</string>"
  done
  echo '  </array>'
  echo '  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>23</integer><key>Minute</key><integer>45</integer></dict>'
  echo '  <key>RunAtLoad</key><true/>'
  echo '  <key>ProcessType</key><string>Background</string>'
  echo '  <key>LowPriorityIO</key><true/>'
  echo '</dict></plist>'
} > "$PLIST"
plutil -lint "$PLIST" >/dev/null

# 5. Background jobs may not write into Documents without Full Disk Access for rclone.
echo
echo "One manual step: System Settings → Privacy & Security → Full Disk Access → + → add:"
echo "  $RCLONE"
echo "(Finder opens that folder; drag 'rclone' into the list and switch it on.)"
open "$APP"
open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles" || true
read -r -p "Press Enter after you have added it… "

# 6. First full copy now, in the foreground, then start the schedule
echo "First copy (may take a while for the videos)…"
"$RCLONE" "${BASE[@]}" --progress || echo "First copy had errors; the nightly job will retry. Log: $LOG"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo
echo "Done. Content: $DEST"
echo "Log: $LOG    Run now: launchctl kickstart -k gui/$(id -u)/$LABEL"
echo "Uninstall: launchctl bootout gui/$(id -u)/$LABEL; rm \"$PLIST\""
