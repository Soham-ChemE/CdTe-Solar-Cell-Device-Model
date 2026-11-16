#!/usr/bin/env bash
# Run a SCAPS 3.3.11 script headless under Wine and copy its results back into the repo.
# Usage: scripts/run_scaps.sh scaps/scripts/NAME.script
# Env:   SCAPS_PREFIX  Wine prefix folder name under tools/ (default: wineprefix). Separate prefixes
#                      (wineprefix_1, wineprefix_2, ...) let several SCAPS instances run in parallel.
#        SCAPS_TIMEOUT seconds (default 900)
# Inputs are synced from scaps/defs (*.def), scaps/generation (*.gen) and scaps/absorption (*.abs) first.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PFX="$REPO/tools/${SCAPS_PREFIX:-wineprefix}"
SCAPS="$PFX/drive_c/Program Files (x86)/Scaps3311"
WINE="$HOME/Applications/Wine Devel.app/Contents/Resources/wine/bin/wine"
script="$1"; name="$(basename "$script")"
[ -x "$WINE" ] || { echo "Wine not found at $WINE"; exit 1; }
[ -f "$SCAPS/scaps3311.exe" ] || { echo "SCAPS not installed in $SCAPS"; exit 1; }
cp "$REPO"/scaps/defs/*.def "$SCAPS/def/" 2>/dev/null || true
cp "$REPO"/scaps/generation/*.gen "$SCAPS/generation/" 2>/dev/null || true
cp "$REPO"/scaps/absorption/*.abs "$SCAPS/absorption/" 2>/dev/null || true
sed 's/\r$//; s/$/\r/' "$script" > "$SCAPS/script/$name"
stamp="$PFX/.scaps_run_stamp_$$"; touch "$stamp"; rm -f "$SCAPS/SCAPSErrorLogFile.log"
export WINEPREFIX="$PFX" WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml="
(cd "$SCAPS" && timeout "${SCAPS_TIMEOUT:-900}" "$WINE" scaps3311.exe "C:\\Program Files (x86)\\Scaps3311\\script\\$name" >/dev/null 2>&1) || true
mkdir -p "$REPO/scaps/results"
find "$SCAPS/results" -type f -newer "$stamp" -exec cp {} "$REPO/scaps/results/" \;
rm -f "$stamp"
if [ -f "$SCAPS/SCAPSErrorLogFile.log" ]; then echo "SCAPS reported errors:"; tr -d '\r' < "$SCAPS/SCAPSErrorLogFile.log" | tail -15; exit 2; fi
echo "done: results in scaps/results"
