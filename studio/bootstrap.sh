#!/usr/bin/env bash
# Sandbox reset hone pe sab kuch wapas laao: ffmpeg + python packages (+ browser fallback).
#   bash bootstrap.sh          # ffmpeg + yt-dlp (default)
#   bash bootstrap.sh full     # + whisper, opencv, numpy stack
#   bash bootstrap.sh browser  # + Playwright + Chromium fallback
#   bash bootstrap.sh all      # full + browser dono
set -e
echo "== ffmpeg =="
if [ ! -x /tmp/vidtools/ffmpeg ]; then
  pip3 install -q imageio-ffmpeg
  mkdir -p /tmp/vidtools
  cp "$(python3 -c 'import imageio_ffmpeg,shutil;print(imageio_ffmpeg.get_ffmpeg_exe())')" /tmp/vidtools/ffmpeg
  chmod +x /tmp/vidtools/ffmpeg
fi
mkdir -p /home/user/bin
ln -sf /tmp/vidtools/ffmpeg /home/user/bin/ffmpeg
/tmp/vidtools/ffmpeg -version | head -1

echo "== yt-dlp =="
python3 -c "import yt_dlp" 2>/dev/null || pip3 install -q -U yt-dlp
python3 -c "import yt_dlp; print('yt-dlp', yt_dlp.version.__version__)"

if [ "${1:-}" = "full" ] || [ "${1:-}" = "all" ]; then
  echo "== full stack =="
  pip3 install -q "av==16.0.1" faster-whisper "opencv-python-headless==4.12.0.88" numpy librosa
fi

if [ "${1:-}" = "browser" ] || [ "${1:-}" = "all" ]; then
  echo "== playwright + chromium =="
  python3 -m pip install -q playwright
  sudo "$(which python3)" -m playwright install-deps chromium
  python3 -m playwright install chromium
fi
echo "== ready =="
