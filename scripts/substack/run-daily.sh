#!/bin/bash
# The morning job (launchd runs it once a day; see install-mac.sh). In its own clone of main, so it
# never touches the folder you edit in, it:
#   1. copies new and edited Substack posts onto the site, and pushes them;
#   2. runs the archiver: archives every outbound link it hasn't seen yet (new posts included),
#      checks the old ones for rot, and for dead ones puts the archived copy on the site and adds
#      an [archived] link beside the original (or a line in SUBSTACK_DEAD_LINKS.md for Substack
#      posts, which can only be fixed by hand). Then pushes that too.
# The archive itself (.archiver/ and archive/) stays in your usual checkout.
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

commit_and_push() {
  if git diff --cached --quiet; then
    echo "$2"
  else
    git -c user.name="Croissanthology" -c user.email="croissanthology@gmail.com" \
      commit --quiet -m "$1"
    git push --quiet origin main
    echo "Pushed: $1"
  fi
}

# 1. Substack
"$VENV/bin/python" scripts/substack/sync.py || echo "(the Substack sync failed; see above)"
git add -A subslop images/subslop _data/subslop.json _substack
commit_and_push "Sync Substack posts" "Nothing new on Substack."

# 2. Archiver
ARCHIVER="$STATE/archiver"
if [ -x "$ARCHIVER" ] && [ -f "$STATE/archiver-data" ]; then
  export ARCHIVER_REPO="$REPO" ARCHIVER_DATA="$(cat "$STATE/archiver-data")"
  "$ARCHIVER" scan </dev/null || echo "(archiver scan hit an error; see above)"
  "$ARCHIVER" maintain </dev/null || echo "(archiver maintain hit an error; see above)"
  # Only the archiver has touched tracked files since the reset; the archive dirs that back
  # rehosted links were already staged by the archiver itself.
  git add -u
  [ -f SUBSTACK_DEAD_LINKS.md ] && git add SUBSTACK_DEAD_LINKS.md
  commit_and_push "archiver: daily maintenance" "No dead links to rehost."
fi
