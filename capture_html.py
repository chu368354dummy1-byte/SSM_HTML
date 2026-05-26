"""
capture.py – fetch SSM waiting-time page without a headless browser.

Strategy (tries in order):
  1. curl_cffi  – Chrome TLS/HTTP2 impersonation (best Cloudflare bypass)
  2. requests   – plain HTTPS with realistic headers (fast fallback)

Install:
  pip install curl-cffi requests
"""

import os
import time
import random
from datetime import datetime, timezone, timedelta

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

HEADERS = {
    "Accept":           "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language":  "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding":  "gzip, deflate, br",
    "Cache-Control":    "no-cache",
    "Pragma":           "no-cache",
    "Referer":          BASE_URL + "/",
    "Sec-Fetch-Dest":   "document",
    "Sec-Fetch-Mode":   "navigate",
    "Sec-Fetch-Site":   "same-origin",
    "Sec-Fetch-User":   "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}


def log(msg: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    ts   = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def is_cloudflare_challenge(html: str) -> bool:
    return any(marker in html for marker in CLOUDFLARE_MARKERS)


# ── Strategy 1: curl_cffi (Chrome TLS impersonation) ─────────────────────────

def fetch_with_curl_cffi() -> str:
    from curl_cffi import requests as cffi_requests

    log("Trying curl_cffi (Chrome TLS impersonation) ...")
    session = cffi_requests.Session(impersonate="chrome124")

    # Warm-up: visit homepage first to get cookies
    session.get(BASE_URL, headers=HEADERS, timeout=20)
    time.sleep(random.uniform(1.5, 3.0))

    resp = session.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


# ── Strategy 2: plain requests ────────────────────────────────────────────────

def fetch_with_requests() -> str:
    import requests

    log("Trying requests (plain HTTPS) ...")
    session = requests.Session()

    # Warm-up: visit homepage first to get cookies
    session.get(BASE_URL, headers=HEADERS, timeout=20)
    time.sleep(random.uniform(1.5, 3.0))

    resp = session.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


# ── Orchestrator ──────────────────────────────────────────────────────────────

def fetch_html() -> str:
    strategies = [fetch_with_curl_cffi, fetch_with_requests]

    for strategy in strategies:
        try:
            html = strategy()
            if not is_cloudflare_challenge(html):
                log(f"Success with {strategy.__name__}.")
                return html
            log(f"{strategy.__name__} returned a Cloudflare challenge page.")
        except Exception as e:
            log(f"{strategy.__name__} failed: {e}")

    raise RuntimeError("All fetch strategies failed.")


def main() -> None:
    os.makedirs(HTML_DIR, exist_ok=True)

    try:
        html = fetch_html()
    except Exception as e:
        log(f"FATAL: {e}")
        raise SystemExit(1)

    now      = datetime.now(TZ)
    filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".html"
    filepath = os.path.join(HTML_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    log(f"OK  {filename} ({len(html)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
