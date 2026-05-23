#!/usr/bin/env zsh
# Wrapper invoked by com.croissanthology.archiver.plist.
# Runs the monthly archiver maintenance pass. Notifications go through
# Apple Mail + macOS notification center — no SMTP creds required.
set -euo pipefail

# Resolve the repo root (this script lives at <repo>/archiver/launchd/).
SCRIPT_DIR="${0:A:h}"
REPO_ROOT="${SCRIPT_DIR:h:h}"
cd "$REPO_ROOT"

# Pull latest first so we don't rehost against stale state.
git fetch --quiet origin
git pull --quiet --ff-only || true

BINARY="$REPO_ROOT/archiver/target/release/archiver"
if [[ ! -x "$BINARY" ]]; then
  echo "archiver binary not found at $BINARY — building it now..."
  (cd "$REPO_ROOT/archiver" && cargo build --release)
fi

"$BINARY" maintain

# Commit + push any rehosts / new state.
if ! git diff --quiet || ! git diff --cached --quiet; then
  git add archive/ .archiver/ _posts/ SUBSTACK_DEAD_LINKS.md 2>/dev/null || true
  git commit -m "archiver: monthly maintenance pass" || true
  git push --quiet origin "$(git rev-parse --abbrev-ref HEAD)" || true
fi
