#!/bin/bash
# cleanup-screenshots.sh — Remove browser automation screenshots older than 3 days
# Keeps disk usage under control. Run periodically or from cron.
SCREENSHOT_DIR="OKComputer_职位搜索清单/screenshots"
cd "$(dirname "$0")" || exit 1

if [ -d "$SCREENSHOT_DIR" ]; then
  count=$(find "$SCREENSHOT_DIR" -name "*.png" -mtime +3 | wc -l | tr -d ' ')
  if [ "$count" -gt 0 ]; then
    find "$SCREENSHOT_DIR" -name "*.png" -mtime +3 -delete
    echo "Cleaned $count old screenshots from $SCREENSHOT_DIR"
  else
    echo "No old screenshots to clean"
  fi
else
  echo "Screenshot directory not found: $SCREENSHOT_DIR"
fi

# Also clean loose screenshots in workspace root
root_count=$(find . -maxdepth 1 -name "*.png" -mtime +3 | wc -l | tr -d ' ')
if [ "$root_count" -gt 0 ]; then
  find . -maxdepth 1 -name "*.png" -mtime +3 -delete
  echo "Cleaned $root_count loose PNG files from workspace root"
fi
