#!/bin/bash
# Git push with retry — handles intermittent GitHub connectivity in China.
# Usage: ./git-push-retry.sh [remote] [branch] [max_attempts]
set -euo pipefail

REMOTE="${1:-origin}"
BRANCH="${2:-main}"
MAX_ATTEMPTS="${3:-5}"
WAIT_BASE=10

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo "$HOME/.openclaw/workspace/career-os")"

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    echo "[attempt $attempt/$MAX_ATTEMPTS] git push $REMOTE $BRANCH..."
    if git push "$REMOTE" "$BRANCH" 2>&1; then
        echo "✅ Push succeeded on attempt $attempt"
        exit 0
    fi

    if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
        wait=$((WAIT_BASE * attempt))
        echo "⏳ Push failed. Retrying in ${wait}s..."
        sleep "$wait"
    fi
done

echo "❌ Push failed after $MAX_ATTEMPTS attempts. GitHub may be unreachable."
exit 1
