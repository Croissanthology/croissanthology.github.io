#!/bin/bash
# Daily Substack -> croissanthology.com sync. launchd runs this once a day (see install-mac.sh).
# It works in its own copy of the repo, so it never touches the folder you edit in.
# Then, if the archiver is set up, it archives every outbound link of each post it just fetched.
set -euo pipefail
# launchd starts jobs with a bare PATH; the archiver needs monolith from Homebrew.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

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

NEW="$STATE/new-posts.txt"
"$VENV/bin/python" scripts/substack/sync.py --report "$NEW"

git add -A subslop images/subslop _data/subslop.json _substack
if git diff --cached --quiet; then
  echo "Nothing new on Substack."
else
  git -c user.name="Croissanthology" -c user.email="croissanthology@gmail.com" \
    commit --quiet -m "Sync Substack posts"
  git push --quiet origin main
  echo "Pushed."
fi

# Archive the outbound links of every post fetched today (new posts, plus edits and anything
# under two weeks old). Links the archiver already has are skipped, so repeats are cheap.
# The archive lives in your own checkout (archive/ and .archiver/ are gitignored, so
# nothing here gets committed).
ARCHIVER="$STATE/archiver"
if [ -x "$ARCHIVER" ] && [ -f "$STATE/archiver-repo" ] && [ -s "$NEW" ]; then
  export ARCHIVER_REPO="$(cat "$STATE/archiver-repo")"
  while read -r url; do
    [ -n "$url" ] || continue
    echo "-- archiving the links in $url"
    "$ARCHIVER" post "$url" </dev/null || echo "   (the archiver hit an error on this post; see above)"
  done < "$NEW"
fi
