#!/usr/bin/env bash
# Keep data/history.json on its own branch (linkedin-history) so daily posts don't need a PR.
#   ./history.sh pull   - before posting: fetch the latest history
#   ./history.sh push   - after posting: save the updated history
set -euo pipefail
cd "$(dirname "$0")"
BRANCH=linkedin-history
FILE=linkedin-autopost/data/history.json
case "${1:-}" in
  pull)
    if git fetch -q origin "$BRANCH" 2>/dev/null; then
      git show "FETCH_HEAD:$FILE" > data/history.json && echo "History loaded from $BRANCH"
    else
      echo "No $BRANCH branch yet; starting from the committed history"
    fi ;;
  push)
    tmp=$(mktemp -d)
    if git fetch -q origin "$BRANCH" 2>/dev/null; then
      git worktree add -q "$tmp" FETCH_HEAD
    else
      git worktree add -q --detach "$tmp" HEAD
    fi
    cp data/history.json "$tmp/$FILE"
    ( cd "$tmp" && git add "$FILE" \
      && { git diff --cached --quiet || git commit -q -m "LinkedIn: record post for $(TZ=Asia/Kolkata date +%F)"; } \
      && git push -q origin "HEAD:refs/heads/$BRANCH" )
    git worktree remove --force "$tmp"
    echo "History saved to $BRANCH" ;;
  *) echo "usage: $0 pull|push"; exit 2 ;;
esac
