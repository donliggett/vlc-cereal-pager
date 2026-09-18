#!/usr/bin/env bash
# Build Cereal Pager into dist/CerealPager.vlt
#
#   ./build.sh            regenerate art, sync, validate, render, package
#   ./build.sh --quick    package only (assets must already exist)
#
# A .vlt is just a gzipped tar (or a zip) whose root holds theme.xml.
set -euo pipefail
cd "$(dirname "$0")"

NAME=CerealPager
OUT=dist/$NAME.vlt

if [ "${1:-}" != "--quick" ]; then
  echo "==> artwork"
  python3 tools/generate_assets.py
  echo "==> bitmap declarations"
  python3 tools/sync_bitmaps.py
  echo "==> previews"
  python3 tools/preview.py
fi

echo "==> validating theme.xml"
python3 tools/validate_theme.py

echo "==> packaging"
mkdir -p dist
rm -f "$OUT"
tar --format=ustar -czf "$OUT" theme.xml assets fonts
echo "built $OUT  ($(du -h "$OUT" | cut -f1))"
echo
echo "Install: VLC > Tools > Preferences > Interface > Use custom skin > $PWD/$OUT"
