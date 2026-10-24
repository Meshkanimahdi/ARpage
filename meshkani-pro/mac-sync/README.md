# Nightly local copy on Mahdi's Mac

The cloud sessions cannot reach the Mac, so the Mac copies from Drive itself.

- Install: on the Mac, `bash install.sh` (once). It installs rclone in `~/Applications/MeshkaniSync`,
  connects it to Drive read-only (browser sign-in), asks for Full Disk Access for that rclone, does
  a first full copy and schedules `pro.meshkani.instagram-sync` in launchd.
- When: every night at 23:45 Tehran. If the Mac is asleep then, launchd runs it on wake; if it was
  off, it runs at the next login. Each run copies only new or changed files (incremental), so a
  missed night is picked up by the next run. Local files are never deleted.
- Destination `/Users/mahdimeshkani/Documents/My Works/Meshkani.pro/Instagram`:
  - `Reels/YYYY-MM-DD_REEL-NNN/`: reel, cover, story cut (Drive `ریلز`)
  - `Posts/YYYY-MM-DD_POST-NNN_slug/`: slides and music versions (Drive `Media/Images`)
  - `Stories/YYYY-MM-DD_POST-NNN_slug/`: stories (Drive `استوری`)
  - `Map/content-map.html`: the content map (Drive `Map`, id `1v5-Ml8y4pt85uah36NGyz2Jn8kIOB-rT`)
  Only dated content folders are copied; loose working files and tests stay on Drive.
- Whoever republishes the content-map artifact also replaces Drive file
  `1GwwTT4iZ3dCd0uQxj5JmXHrTcATqN1bq` (standalone HTML: doctype + `lang="fa" dir="rtl"`) so the
  Mac gets the new version that night.
- Log: `~/Library/Logs/meshkani-instagram-sync.log`. Run now:
  `launchctl kickstart -k gui/$(id -u)/pro.meshkani.instagram-sync`.
