#!/usr/bin/env bash
# Keep post history on its own branch (linkedin-history) so daily posts don't need a PR.
#   ./history.sh pull           - before posting: fetch the latest history files
#   ./history.sh push           - after a Company Page post: save data/history.json
#   ./history.sh push-profile   - after a personal-profile post: save data/history_profile.json
set -euo pipefail
cd "$(dirname "$0")"
BRANCH=linkedin-history
DIR=linkedin-autopost/data

save() {   # save <file in data/> <commit message>
  local name=$1 msg=$2 tmp
  tmp=$(mktemp -d)
  if git fetch -q origin "$BRANCH" 2>/dev/null; then
    git worktree add -q "$tmp" FETCH_HEAD
  else
    git worktree add -q --detach "$tmp" HEAD
  fi
  mkdir -p "$tmp/$DIR"
  cp "data/$name" "$tmp/$DIR/$name"
  ( cd "$tmp" && git add "$DIR/$name" \
    && { git diff --cached --quiet || git commit -q -m "$msg"; } \
    && git push -q origin "HEAD:refs/heads/$BRANCH" )
  git worktree remove --force "$tmp"
  echo "$name saved to $BRANCH"
}

case "${1:-}" in
  pull)
    if git fetch -q origin "$BRANCH" 2>/dev/null; then
      for name in history.json history_profile.json; do
        if git cat-file -e "FETCH_HEAD:$DIR/$name" 2>/dev/null; then
          git show "FETCH_HEAD:$DIR/$name" > "data/$name" && echo "$name loaded from $BRANCH"
        fi
      done
    else
      echo "No $BRANCH branch yet; starting from the committed history"
    fi ;;
  push)         save history.json "LinkedIn: record post for $(TZ=Asia/Kolkata date +%F)" ;;
  push-profile) save history_profile.json "LinkedIn profile: record post for $(TZ=Asia/Kolkata date +%F)" ;;
  *) echo "usage: $0 pull|push|push-profile"; exit 2 ;;
esac
