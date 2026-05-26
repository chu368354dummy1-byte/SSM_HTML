"""
capture_html.py – fetch SSM waiting-time page via Cloudflare Worker proxy.

The Worker runs inside CF's network, so the SSM portal (also behind CF)
sees a trusted CF-to-CF request instead of a GitHub Actions datacenter IP.

Install:  pip install requests
Env vars: CF_WORKER_URL, CF_PROXY_SECRET
"""

import os
import time
import random
from datetime import datetime, timezone, timedelta

import requests

TARGET_URL = "https://www.ssm.gov.mo/portal1/waitingsmy?lang=ch"
HTML_DIR   = "html"
LOG_DIR    = "logs"
LOG_FILE   = os.path.join(LOG_DIR, "capture.log")
TZ         = timezone(timedelta(hours=8))

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
    worker_url = os.environ.get("CF_WORKER_URL", "").rstrip("/")
    secret     = os.environ.get("CF_PROXY_SECRET", "")

    if not worker_url:
        raise RuntimeError("CF_WORKER_URL environment variable is not set.")

    proxy_url = f"{worker_url}?url={TARGET_URL}"
    log(f"Fetching via CF Worker: {proxy_url}")

    time.sleep(random.uniform(1.0, 3.0))   # avoid thundering-herd on the hour

    resp = requests.get(
        proxy_url,
        headers={"x-proxy-secret": secret},
        timeout=30,
    )
    resp.raise_for_status()

    html = resp.text
    if is_cloudflare_challenge(html):
        raise RuntimeError("Response is still a Cloudflare challenge page.")

    return html


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
