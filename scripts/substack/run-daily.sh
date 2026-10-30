#!/bin/bash
# Daily Substack -> croissanthology.com sync. launchd runs this once a day (see install-mac.sh).
# It works in its own copy of the repo, so it never touches the folder you edit in.
set -euo pipefail

STATE="$HOME/Library/Application Support/croissanthology-sync"
REPO="$STATE/repo"
VENV="$STATE/venv"
LOG="$HOME/Library/Logs/croissanthology-sync.log"
mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "== $(date '+%Y-%m-%d %H:%M')"

ORIGIN="$(cat "$STATE/origin")"
if [ ! -d "$REPO/.git" ]; then
  git clone --quiet "$ORIGIN" "$REPO"
fi
cd "$REPO"
git fetch --quiet origin main
git checkout --quiet main
git reset --quiet --hard origin/main

if [ ! -f scripts/substack/sync.py ]; then
  echo "The sync isn't on main yet (the pull request hasn't been merged). Nothing to do."
  exit 0
fi

"$VENV/bin/python" scripts/substack/sync.py

git add -A subslop images/subslop _data/subslop.json _substack
if git diff --cached --quiet; then
  echo "Nothing new on Substack."
  exit 0
fi
git -c user.name="Croissanthology" -c user.email="croissanthology@gmail.com" \
  commit --quiet -m "Sync Substack posts"
git push --quiet origin main
echo "Pushed."
