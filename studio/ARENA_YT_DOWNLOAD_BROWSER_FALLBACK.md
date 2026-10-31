# Arena Runbook — Web, YouTube Downloads and Browser-Bot Fallback

Use this guide in another Arena workspace when a task needs web research, YouTube metadata, video/section downloads, or a browser-automation fallback.

## 1. Current tool roles

| Tool | Use it for | Important limitation |
|---|---|---|
| Web search / page fetch | Public pages, source research, community posts, titles and metadata | Dynamic or blocked pages may not render correctly |
| `yt-dlp` | YouTube formats, media URLs, full videos and timestamp sections | Direct access can return `LOGIN_REQUIRED`; formats and proxies vary per VOD |
| FFmpeg | Accurate cuts, re-encoding, audio/video merge, loudness and decode QA | Remote Googlevideo URLs can expire or be proxy/IP-bound |
| Playwright + Chromium | **Fallback** for JavaScript pages, sessions, bot checks, clicks, scrolling and network inspection | Not installed in the currently checked environment; set it up when required |

### Environment checked in the reference workspace

- `yt-dlp` and FFmpeg workflows are available and were used successfully.
- Playwright, Selenium and Pyppeteer were **not** installed.
- Chrome, Chromium and Firefox were **not** available.
- Do not claim browser automation was used unless it was actually installed and run.

Check again in each new/reset environment:

```bash
python3 - <<'PY'
import importlib.util, shutil, os
for p in ('playwright', 'selenium', 'pyppeteer'):
    print(p, bool(importlib.util.find_spec(p)))
for b in ('chromium', 'chromium-browser', 'google-chrome', 'firefox'):
    print(b, shutil.which(b))
print('playwright cache', os.path.isdir('/home/user/.cache/ms-playwright'))
PY

yt-dlp --version
/home/user/bin/ffmpeg -version | head -1
```

## 2. Restore FFmpeg if the sandbox reset removed the shortcut

```bash
mkdir -p /home/user/bin
FF=$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')
ln -sf "$FF" /home/user/bin/ffmpeg
/home/user/bin/ffmpeg -version | head -1
```

For new `yt-dlp` downloads, pass:

```bash
--ffmpeg-location /home/user/bin/ffmpeg
```

## 3. Normal YouTube workflow — try this first

### Inspect the VOD and available formats

```bash
yt-dlp --no-playlist -F "YOUTUBE_URL"
```

Format numbers are **not universal**. For example, `299` was 1080×1920/60 in one Don VOD, but another VOD can offer only `137`/`136`/`135` at those resolutions. Always inspect with `-F`.

### Download a full video with the best available audio

```bash
yt-dlp --no-playlist \
  --ffmpeg-location /home/user/bin/ffmpeg \
  -f "bestvideo[height<=1080]+bestaudio/best" \
  --merge-output-format mp4 \
  -o video.mp4 "YOUTUBE_URL"
```

### Download only a timestamp section

```bash
yt-dlp --no-playlist \
  --ffmpeg-location /home/user/bin/ffmpeg \
  -f 299 \
  --download-sections "*02:05:06.00-02:05:11.00" \
  --force-keyframes-at-cuts \
  -o section.mp4 "YOUTUBE_URL"
```

Use a format that actually exists. A small file such as 261 bytes is a failed download, not a usable video.

### Merge separate video and audio files

```bash
/home/user/bin/ffmpeg -y -v error \
  -i video_only.mp4 -i audio_only.m4a \
  -c copy -shortest final_av.mp4
```

When both sections start at the same absolute VOD timestamp, use the same start/end values for each download. Verify actual A/V alignment afterward; do not assume it.

## 4. Proxy rules for blocked YouTube access

If direct access returns `LOGIN_REQUIRED` or a bot check, a validated public proxy can be attempted:

```bash
yt-dlp --no-playlist \
  --proxy http://PROXY_IP:PORT \
  --ffmpeg-location /home/user/bin/ffmpeg \
  -f 299 \
  --download-sections "*START-END" \
  --force-keyframes-at-cuts \
  -o section.mp4 "YOUTUBE_URL"
```

Rules learned from real failures:

1. **Googlevideo URLs are usually proxy/IP-bound.** A URL extracted through one proxy can return 403/reset through another route.
2. Use the **same proxy** for URL extraction and subsequent FFmpeg/curl media access.
3. Proxy success can differ by VOD, Googlevideo host and format. A proxy that works for one file can fail for another.
4. If a request fails, obtain a fresh URL and/or change proxy or format. Do not blindly repeat an unchanged timed-out command.
5. Inspect partial output before retrying. A background `yt-dlp`/FFmpeg process can still be running after a tool timeout.
6. Avoid asking the user for another source merely because the first route failed. Try the documented fallback chain first.

A direct FFmpeg remote attempt can use:

```bash
/home/user/bin/ffmpeg -y -v error \
  -http_proxy http://PROXY_IP:PORT \
  -user_agent "Mozilla/5.0" \
  -ss START_SECONDS -t DURATION_SECONDS \
  -i "PROXY_BOUND_GOOGLEVIDEO_URL" \
  -c copy section.mp4
```

In practice, `yt-dlp --download-sections` was sometimes more reliable than manually calling FFmpeg. Use the route that actually validates, not the route that merely looks simpler.

## 5. Mandatory fallback — install and use a browser bot when needed

**Fallback rule for future agents:** if page fetch plus reasonable `yt-dlp` proxy/format attempts cannot access the required page or stream, install and use **Playwright + Chromium**. Do not stop at the first block, and do not claim the browser route was used until it actually runs.

Useful triggers:

- The page needs JavaScript, scrolling, clicking or a session.
- YouTube returns a browser/bot challenge through the normal routes.
- A community post or dynamic page cannot be read with page fetch.
- Browser network inspection is needed to understand which media hosts the session uses.

### Install Playwright and Chromium

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

If OS dependencies are missing and system package installation is permitted:

```bash
python3 -m playwright install --with-deps chromium
```

Environment resets can remove installed packages and browser caches. Re-check and reinstall when necessary.

### Minimal browser/network probe

Save as `browser_probe.py`:

```python
import json
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
proxy = sys.argv[2] if len(sys.argv) > 2 else None
streams = []

with sync_playwright() as p:
    launch_args = {"headless": True}
    if proxy:
        launch_args["proxy"] = {"server": proxy}

    browser = p.chromium.launch(**launch_args)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
    )
    page = context.new_page()

    def on_response(response):
        if "googlevideo.com/videoplayback" in response.url:
            streams.append(response.url)

    page.on("response", on_response)
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(12000)

    print(json.dumps({
        "title": page.title(),
        "final_url": page.url,
        "googlevideo_streams": streams,
    }, indent=2))

    # Storage state is sensitive session material. Do not put it in deliverables.
    context.storage_state(path="browser_state.json")
    browser.close()
```

Run without a proxy:

```bash
python3 browser_probe.py "YOUTUBE_URL"
```

Or through the same proxy that will be used for media access:

```bash
python3 browser_probe.py "YOUTUBE_URL" "http://PROXY_IP:PORT"
```

### Browser-fallback rules

1. A `blob:` URL in the HTML video element is **not** a downloadable MP4 URL.
2. Googlevideo URLs can expire and can be bound to the browser/proxy IP. Use them promptly and through the same route.
3. Browser automation is primarily for **access and inspection**. The actual file transfer is usually more reliable with `yt-dlp`, FFmpeg or curl.
4. If an authorized browser session already exists, its cookies/session can be exported to a Netscape `cookies.txt` and passed to `yt-dlp --cookies cookies.txt`. Never invent credentials or include session files in delivered documents.
5. Browser screen recording is only a last resort; it can reduce quality and damage audio sync. Prefer the original media stream.

## 6. Common errors and the next useful action

| Error / symptom | Next action |
|---|---|
| `LOGIN_REQUIRED` / sign-in bot check | Try a validated proxy, then the Playwright fallback |
| `Requested format is not available` | Run `-F`; select an available format instead of repeating the same one |
| FFmpeg `152` / connection reset | Refresh the media URL; change proxy, host route or format |
| Direct Googlevideo returns `403` | Treat URL as proxy/IP-bound; reuse the extraction route |
| Output is only a few hundred bytes | Treat as failed; do not render or ship it |
| Video downloads but audio fails | Download audio separately through a validated route, then merge and check sync |
| `faster-whisper` fails at `av.open()` | Decode to NumPy PCM with FFmpeg and transcribe the PCM array |
| Tool timeout with no output | Check running processes and partial files before retrying |

FFmpeg PCM example for transcription:

```bash
/home/user/bin/ffmpeg -v error -i final.mp4 \
  -vn -ac 1 -ar 16000 -f f32le audio.f32
```

## 7. QA before delivery

### Full decode

```bash
/home/user/bin/ffmpeg -v error -i final.mp4 -f null -
```

A clean result has return code 0 and no decode errors.

### Loudness and true peak

```bash
/home/user/bin/ffmpeg -hide_banner -nostats -i final.mp4 \
  -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=summary \
  -f null -
```

Also verify:

- Actual spoken captions against source audio/final ASR.
- Opening starts on the intended hook, not the previous sentence/chat.
- Ending does not include the next unrelated word or chat.
- Correct dimensions, frame rate and audio sample rate.
- Local and Drive file sizes/checksums match after upload.
- Any browser/session artifacts remain private and out of deliverables.

## 8. Recommended order for a future agent

1. Use web search/page fetch for source and metadata.
2. Use `yt-dlp -F` and the best available native format.
3. Download only the required section and merge original audio.
4. If blocked, try fresh proxy-bound URLs and validated alternate routes.
5. **If access still fails, install Playwright + Chromium and use the browser fallback.**
6. Render, run visual/audio/decode QA, and document exactly which route succeeded.
7. Never record a check as passed unless it was actually executed and inspected.
