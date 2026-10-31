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
    context.storage_state(path="/tmp/browser_state.json")
    browser.close()
