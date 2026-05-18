"""
capture.py – fetch SSM waiting-time page, bypassing Cloudflare Turnstile.
Requires: pip install playwright playwright-stealth
          playwright install chromium --with-deps
"""

import os
import random
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from playwright_stealth import stealth_sync

URL      = "https://www.ssm.gov.mo/portal1/waitingsmy?lang=ch"
BASE_URL = "https://www.ssm.gov.mo"

HTML_DIR = "html"
LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "capture.log")
TZ       = timezone(timedelta(hours=8))

CLOUDFLARE_MARKERS = [
    "challenges.cloudflare.com",
    "cf-turnstile",
    "正在執行安全驗證",
    "Just a moment",
    "Enable JavaScript and cookies to continue",
]


def log(msg: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    ts   = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def is_cloudflare_challenge(html: str) -> bool:
    return any(marker in html for marker in CLOUDFLARE_MARKERS)


def fetch_html() -> str:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--single-process",
            ],
        )

        ctx = browser.new_context(
            viewport=random.choice([
                {"width": 1920, "height": 1080},
                {"width": 1440, "height": 900},
                {"width": 1366, "height": 768},
            ]),
            locale="zh-TW",
            timezone_id="Asia/Macau",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            java_script_enabled=True,
        )

        page = ctx.new_page()

        # Apply deep stealth patches (disables all Playwright fingerprint leaks)
        stealth_sync(page)

        # Step 1 – homepage warm-up
        log(f"Warming up on {BASE_URL} ...")
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(random.randint(2000, 4000))
        except PWTimeout:
            log("Homepage timed-out; continuing.")

        # Step 2 – target page
        log(f"Fetching {URL} ...")
        page.goto(URL, wait_until="load", timeout=30_000)

        # Wait up to 20s for Cloudflare to auto-resolve the managed challenge
        log("Waiting for Cloudflare challenge to resolve ...")
        for i in range(20):
            page.wait_for_timeout(1000)
            html = page.content()
            if not is_cloudflare_challenge(html):
                log(f"Challenge passed after {i + 1}s.")
                browser.close()
                return html
            if i % 5 == 4:
                log(f"  Still on challenge page ({i + 1}s elapsed) ...")

        # Final content — return whatever we have and let the caller detect failure
        html = page.content()
        browser.close()
        return html


def main() -> None:
    os.makedirs(HTML_DIR, exist_ok=True)

    try:
        html = fetch_html()
    except Exception as e:
        log(f"FAILED to fetch {URL}: {e}")
        return

    if is_cloudflare_challenge(html):
        log("FAILED – still on Cloudflare challenge page after timeout.")
        return

    now      = datetime.now(TZ)
    filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".html"
    filepath = os.path.join(HTML_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        log(f"FAILED to write {filepath}: {e}")
        return

    size_kb = len(html) / 1024
    log(f"OK  {filename} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
