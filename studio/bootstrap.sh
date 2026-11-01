#!/usr/bin/env bash
# Sandbox reset hone pe sab kuch wapas laao: ffmpeg + python packages (+ browser fallback).
#   bash bootstrap.sh          # ffmpeg + yt-dlp (default)
#   bash bootstrap.sh full     # + whisper, opencv, numpy stack
#   bash bootstrap.sh browser  # + Playwright + Chromium fallback
#   bash bootstrap.sh all      # full + browser dono
set -e
echo "== ffmpeg + ffprobe =="
if [ ! -x /tmp/vidtools/ffmpeg ] || [ ! -x /tmp/vidtools/ffprobe ]; then
  mkdir -p /tmp/vidtools
  curl -fsSL https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
    | tar -xJ -C /tmp/vidtools --strip-components=1 --wildcards '*/ffmpeg' '*/ffprobe'
  chmod +x /tmp/vidtools/ffmpeg /tmp/vidtools/ffprobe
fi
mkdir -p /home/user/bin
ln -sf /tmp/vidtools/ffmpeg /home/user/bin/ffmpeg
ln -sf /tmp/vidtools/ffprobe /home/user/bin/ffprobe
/tmp/vidtools/ffmpeg -version | head -1
/tmp/vidtools/ffprobe -version | head -1

echo "== core media + AI segmenter =="
python3 -c "import mediapipe" 2>/dev/null || pip3 install -q mediapipe soundfile scipy Pillow

echo "== yt-dlp =="
python3 -c "import yt_dlp" 2>/dev/null || pip3 install -q -U yt-dlp
python3 -c "import yt_dlp; print('yt-dlp', yt_dlp.version.__version__)"

if [ "${1:-}" = "full" ] || [ "${1:-}" = "all" ]; then
  echo "== full stack =="
  pip3 install -q "av==16.0.1" faster-whisper "opencv-python-headless==4.12.0.88" numpy librosa mediapipe soundfile scipy Pillow
fi

if [ "${1:-}" = "browser" ] || [ "${1:-}" = "all" ]; then
  echo "== playwright + chromium =="
  python3 -m pip install -q playwright
  sudo "$(which python3)" -m playwright install-deps chromium
  python3 -m playwright install chromium
fi
echo "== ready =="
