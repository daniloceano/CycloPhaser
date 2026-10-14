#!/usr/bin/env bash
# A clean clone of COMMIT outside the repo, like the CI `checkout` step (only
# tracked files; nothing ignored, so tools/calibration_app/sample_tracks/ is
# absent exactly as on CircleCI). Prints the clone's path.
#
#   clone_at.sh <commit>
source "$(dirname "$0")/common.sh"
SHA="$(git -C "$REPO" rev-parse "$1")"
DEST="$WORK/checkout_${SHA:0:7}"
rm -rf "$DEST"
git clone -q --no-hardlinks "$REPO" "$DEST"
git -C "$DEST" checkout -q "$SHA"
echo "$DEST"
