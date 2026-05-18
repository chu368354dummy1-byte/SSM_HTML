import os
import requests
from datetime import datetime, timezone, timedelta

URL = "https://www.ssm.gov.mo/portal1/waitingsmy?lang=ch"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
HTML_DIR = "html"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "capture.log")
TZ = timezone(timedelta(hours=8))

def log(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def main():
    os.makedirs(HTML_DIR, exist_ok=True)
    now = datetime.now(TZ)
    filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".html"
    filepath = os.path.join(HTML_DIR, filename)

    try:
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        log(f"FAILED to fetch {URL}: {e}")
        return

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
