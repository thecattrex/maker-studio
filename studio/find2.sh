#!/bin/bash
cd /tmp
q() {
  python3 -m yt_dlp --flat-playlist --print "%(duration)s|%(id)s|%(title)s" "ytsearch12:$1" --no-warnings 2>/dev/null | sort -n | awk -F'|' '$1<=70 && $1>=6' | head -6
}
echo "### trampoline"; q "trampoline fail caught on camera short"
echo "### skate"; q "skateboard bail fail short vertical"
echo "### bike"; q "bike fail crash funny short"
echo "### stairs"; q "fall down stairs fail short"
echo "### ladder"; q "ladder fail funny short"
