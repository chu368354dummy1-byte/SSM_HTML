import os
import time
import random
import requests
from datetime import datetime, timezone, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://www.ssm.gov.mo/portal1/waitingsmy?lang=ch"
BASE_URL = "https://www.ssm.gov.mo"

HTML_DIR = "html"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "capture.log")
TZ = timezone(timedelta(hours=8))

# Rotate through realistic Chrome User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def log(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def make_session() -> requests.Session:
    """Build a session with retry logic and a connection pool."""
    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=2,          # waits 2s, 4s, 8s between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def build_headers() -> dict:
    """Return headers that closely mimic a real browser visit."""
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",        # first visit has no referrer
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        # Referer is set dynamically after the homepage visit (see fetch())
    }


def fetch(session: requests.Session) -> requests.Response:
    """
    Two-step fetch:
      1. Visit the site homepage to pick up any cookies / establish a session.
      2. Wait a short random delay, then request the target page with Referer set.
    This mimics normal browser navigation and satisfies most basic bot-detection.
    """
    headers = build_headers()

    # Step 1 – homepage warm-up
    try:
        log(f"Warming up session on {BASE_URL} …")
        session.get(BASE_URL, headers=headers, timeout=15)
        time.sleep(random.uniform(1.5, 3.5))   # human-like pause
    except Exception as e:
        log(f"Homepage warm-up failed (non-fatal): {e}")

    # Step 2 – real request with Referer
    headers["Referer"] = BASE_URL + "/"
    headers["Sec-Fetch-Site"] = "same-origin"
    resp = session.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp


def main():
    os.makedirs(HTML_DIR, exist_ok=True)
    session = make_session()

    try:
        resp = fetch(session)
    except requests.HTTPError as e:
        log(f"FAILED HTTP {e.response.status_code} for {URL}: {e}")
        return
    except Exception as e:
        log(f"FAILED to fetch {URL}: {e}")
        return

    now = datetime.now(TZ)
    filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".html"
    filepath = os.path.join(HTML_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(resp.text)
    except Exception as e:
        log(f"FAILED to write {filepath}: {e}")
        return

    size_kb = len(resp.text) / 1024
    log(f"OK  {filename} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
