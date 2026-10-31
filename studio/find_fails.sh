#!/bin/bash
# find candidate fails shorts via yt-dlp search (metadata only)
python3 -m yt_dlp --flat-playlist --print "%(duration)s|%(view_count)s|%(id)s|%(title)s" \
  "ytsearch15:funny fails compilation shorts" --no-warnings 2>/dev/null | head -20
echo "=== 2 ==="
python3 -m yt_dlp --flat-playlist --print "%(duration)s|%(view_count)s|%(id)s|%(title)s" \
  "ytsearch15:instant regret fails shorts" --no-warnings 2>/dev/null | head -20
