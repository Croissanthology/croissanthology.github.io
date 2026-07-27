#!/usr/bin/env bash
# Build Roussette and drop it into your Minecraft mods folder.
#
#   ./install.sh              build, then install to the default .minecraft
#   ./install.sh /path/to/mc  build, then install to a specific instance
#
# Needs: Java 21+, and an internet connection the first time (Gradle downloads
# NeoForge). Everything after that is offline.

set -euo pipefail
cd "$(dirname "$0")"

say() { printf '\033[35m%s\033[0m\n' "$*"; }
die() { printf '\033[31merror: %s\033[0m\n' "$*" >&2; exit 1; }

# --- java ---------------------------------------------------------------------
command -v java >/dev/null 2>&1 || die "Java not found. Install Java 21 or newer."
JV=$(java -version 2>&1 | head -1 | sed -E 's/.*"([0-9]+).*/\1/')
[ "${JV:-0}" -ge 21 ] 2>/dev/null || die "Java 21+ required, found $JV."
say "Java $JV ok"

# --- build --------------------------------------------------------------------
if [ -x ./gradlew ]; then
  GRADLE=./gradlew
elif command -v gradle >/dev/null 2>&1; then
  say "No wrapper here; generating one with your local Gradle."
  gradle wrapper --gradle-version 8.14.3 >/dev/null
  GRADLE=./gradlew
else
  die "Neither ./gradlew nor gradle found. Install Gradle 8.x, or copy the
  gradle/ folder and gradlew from any NeoForge MDK into this directory."
fi

say "Building. First run downloads NeoForge and takes a few minutes."
$GRADLE build

JAR=$(ls -1 build/libs/*.jar 2>/dev/null | grep -v -- '-sources' | head -1 || true)
[ -n "$JAR" ] || die "Build produced no jar. Scroll up for the compile errors."
say "Built $JAR"

# --- find minecraft -----------------------------------------------------------
if [ $# -ge 1 ]; then
  MC="$1"
else
  case "$(uname -s)" in
    Darwin) MC="$HOME/Library/Application Support/minecraft" ;;
    Linux)  MC="$HOME/.minecraft" ;;
    *)      MC="$APPDATA/.minecraft" ;;
  esac
fi
[ -d "$MC" ] || die "No Minecraft folder at: $MC
  Pass the path explicitly:  ./install.sh '/path/to/.minecraft'"

mkdir -p "$MC/mods"
cp "$JAR" "$MC/mods/"
say "Installed to $MC/mods/$(basename "$JAR")"
cat <<'EOF'

Next:
  1. Launch the NeoForge 26.2 profile (not vanilla).
  2. Everyone on the LAN world needs this same jar in their mods folder.
  3. In the world, once ever:   /roussette-temples
  4. She hunts anyone whose name contains "rousset" automatically.
     To aim her by hand:        /new-target <name>
     To make someone safe:      /roussette-spare <name>
EOF
