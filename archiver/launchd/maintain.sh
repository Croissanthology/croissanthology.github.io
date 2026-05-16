#!/usr/bin/env zsh
# Wrapper invoked by com.croissanthology.archiver.plist.
# Sources SMTP credentials, then runs the monthly archiver maintenance pass.
set -euo pipefail

# Resolve the repo root (this script lives at <repo>/archiver/launchd/).
SCRIPT_DIR="${0:A:h}"
REPO_ROOT="${SCRIPT_DIR:h:h}"
cd "$REPO_ROOT"

# Pull latest first so we don't rehost against stale state.
git fetch --quiet origin
git pull --quiet --ff-only || true

# Load SMTP credentials. Expects ~/.archiver.env with lines like:
#   export ARCHIVER_SMTP_USER="you@gmail.com"
#   export ARCHIVER_SMTP_PASS="abcd efgh ijkl mnop"   # gmail app password
if [[ -f "$HOME/.archiver.env" ]]; then
  source "$HOME/.archiver.env"
fi

BINARY="$REPO_ROOT/archiver/target/release/archiver"
if [[ ! -x "$BINARY" ]]; then
  echo "archiver binary not found at $BINARY — building it now..."
  (cd "$REPO_ROOT/archiver" && cargo build --release)
fi

"$BINARY" maintain

# Commit + push any rehosts / new state.
if ! git diff --quiet || ! git diff --cached --quiet; then
  git add archive/ .archiver/ _posts/ || true
  git commit -m "archiver: monthly maintenance pass" || true
  git push --quiet origin "$(git rev-parse --abbrev-ref HEAD)" || true
fi
