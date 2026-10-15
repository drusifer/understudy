#!/bin/sh
# `bobp make push MSG="..." [ARGS="--dry-run"]` - the one way changes leave this machine
# (docs/SDLC.md §6). The Makefile runs the full gate (`check`) before this script.
#
#   1. uncommitted changes? stage everything, scan the staged files for secrets,
#      and commit them with $MSG (required when there is anything to commit);
#   2. push the current branch and the annotated tags on it to origin.
#
# Never forces. With --dry-run nothing is committed and the push is only previewed.
set -eu

dry_run=0
for argument in "$@"; do
  [ "$argument" = "--dry-run" ] && dry_run=1
done

branch=$(git branch --show-current)
[ -n "$branch" ] || { echo "push: not on a branch (detached HEAD) - check out a branch first" >&2; exit 1; }

if [ -n "$(git status --porcelain)" ]; then
  if [ "$dry_run" = 1 ]; then
    echo "push: would commit these changes to $branch:"
    git status --short
  else
    [ -n "${MSG:-}" ] || { echo 'push: there are uncommitted changes - give a commit message: bobp make push MSG="..."' >&2; exit 1; }
    git add -A
    # `check` scanned history and tracked changes; new files are only visible once staged.
    gitleaks git --no-banner --redact --pre-commit --staged . || {
      echo "push: gitleaks found a secret in the staged changes - nothing was committed (still staged; fix and rerun)" >&2
      exit 1
    }
    printf '%s\n' "$MSG" | git commit -q -F -
    git log --oneline -1
  fi
fi

git push --follow-tags origin "$branch" "$@"
