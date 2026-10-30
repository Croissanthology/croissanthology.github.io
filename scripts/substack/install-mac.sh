#!/bin/bash
# One-time setup on your Mac. Run it from inside your croissanthology.github.io folder:
#
#     bash scripts/substack/install-mac.sh
#
# It (1) makes a small Python environment for the sync, (2) copies your Substack posts into the
# branch you're on right now and pushes them, (3) builds the archiver from this checkout, and
# (4) installs the morning job: every day at 09:41 (or when the Mac next wakes up, if it was
# asleep) it syncs Substack onto main and runs the archiver's scan + maintenance pass. That
# replaces the archiver's old 3am job, which this turns off.
# Run it again whenever you want the morning job to use a newer archiver.
# Undo: launchctl bootout "gui/$(id -u)/com.croissanthology.substack-sync"
#       rm ~/Library/LaunchAgents/com.croissanthology.substack-sync.plist
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
STATE="$HOME/Library/Application Support/croissanthology-sync"
LABEL="com.croissanthology.substack-sync"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
mkdir -p "$STATE" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "python3 isn't installed. Install it (e.g. 'brew install python') and run this again."
  exit 1
fi

echo "1/4  Python environment"
"$PY" -m venv "$STATE/venv"
"$STATE/venv/bin/pip" install --quiet --upgrade pip
"$STATE/venv/bin/pip" install --quiet beautifulsoup4 pillow

echo "2/4  Copying your Substack posts into this branch ($(git branch --show-current))"
git remote get-url origin > "$STATE/origin"
cp scripts/substack/run-daily.sh "$STATE/run-daily.sh"
"$STATE/venv/bin/python" scripts/substack/sync.py --refresh
git add -A subslop images/subslop _data/subslop.json _substack
if ! git diff --cached --quiet; then
  git -c user.name="Croissanthology" -c user.email="croissanthology@gmail.com" \
    commit --quiet -m "Sync Substack posts"
  git push --quiet origin "HEAD:$(git branch --show-current)"
  echo "     pushed"
fi

echo "3/4  Archiver"
# The archive itself (archive/, .archiver/config.toml and index.json) lives in your main checkout,
# even when you run this from a worktree.
MAIN="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
CARGO="$(command -v cargo || echo "$HOME/.cargo/bin/cargo")"
rm -f "$STATE/archiver-repo"  # from an earlier version of this script
if [ ! -f "$MAIN/.archiver/config.toml" ]; then
  echo "     no .archiver/config.toml in $MAIN, so the morning job won't run the archiver"
  rm -f "$STATE/archiver" "$STATE/archiver-data"
elif [ -f archiver/Cargo.toml ] && [ -x "$CARGO" ] && (cd archiver && "$CARGO" build --release --quiet); then
  cp archiver/target/release/archiver "$STATE/archiver"
  echo "$MAIN" > "$STATE/archiver-data"
  echo "     built; it will keep archiving into $MAIN/archive"
else
  echo "     couldn't build the archiver (is Rust installed?), so the morning job won't run it"
  rm -f "$STATE/archiver" "$STATE/archiver-data"
fi
command -v monolith >/dev/null || echo "     (monolith isn't installed, so only Wayback and archive.is copies: brew install monolith)"
OLD="$HOME/Library/LaunchAgents/com.croissanthology.archiver.plist"
if [ -f "$STATE/archiver-data" ] && [ -f "$OLD" ]; then
  launchctl bootout "gui/$(id -u)/com.croissanthology.archiver" 2>/dev/null || true
  mv "$OLD" "$STATE/old-3am-archiver.plist"
  echo "     turned off the old 3am archiver job (its plist is saved in $STATE)"
fi

echo "4/4  Daily job"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$STATE/run-daily.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>41</integer></dict>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/croissanthology-sync.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/croissanthology-sync.log</string>
</dict>
</plist>
PLIST
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Done. The morning job runs every day at 09:41; the log is ~/Library/Logs/croissanthology-sync.log"
