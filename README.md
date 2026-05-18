# SSM HTML Archive with GitHub Actions

This project automatically downloads the raw HTML source (`Ctrl+U` equivalent) of the Macau Health Bureau waiting-time webpage every hour and stores each snapshot as a timestamped `.html` file in a GitHub repository. GitHub Actions runs the job in the cloud, so the archive continues even when your computer is turned off.

---

## 1. Project Objective

Target URL:

```text
https://www.ssm.gov.mo/portal1/waitingsmy?lang=ch
```

Requirements:

* Download the original HTML source returned by the server
* No browser rendering or JavaScript execution required
* Run automatically every hour
* Save files using timestamp-based filenames
* Keep all historical snapshots indefinitely
* Commit each snapshot back to the repository

Example output:

```text
html/2026-05-18_14-00-00.html
html/2026-05-18_15-00-00.html
html/2026-05-18_16-00-00.html
```

---

## 2. System Architecture

```text
GitHub Actions (hourly cron)
        ↓
capture_html.py
        ↓
requests.get(URL)
        ↓
Save timestamped HTML file
        ↓
Append to logs/capture.log
        ↓
git add / commit / push
        ↓
Permanent archive in GitHub repository
```

Yes, **1.7 GB of new HTML files per year is technically possible**, but using GitHub as a permanent archive at that growth rate is **not the best long-term design** if you commit every hourly snapshot directly into the repository.

The better production approach is:

> **GitHub Actions for scheduling + automatic monthly ZIP archives + GitHub Releases (or a secondary storage location)**

This keeps the Git repository small and responsive while still preserving all historical files indefinitely.

---

# Executive Summary

| Question                                       | Answer                                                                    |
| ---------------------------------------------- | ------------------------------------------------------------------------- |
| Can GitHub Actions generate 1.7 GB/year?       | Yes                                                                       |
| Can a Git repository store 1.7 GB/year?        | Technically yes, but not ideal                                            |
| Will repository performance degrade over time? | Yes, especially for clones and pushes                                     |
| Recommended long-term design                   | Archive monthly ZIP files instead of individual HTML files in Git history |

---

# Why Committing Every File to Git Is Problematic

Git stores the full history of every committed file. Even though HTML compresses well, a repository with:

* 8,760 new files/year
* Frequent commits
* Continuously growing history

will eventually become:

* Slow to clone
* Slow to push
* Harder to maintain

GitHub also imposes practical limits (for example, a recommended repository size around a few GB, and a 100 MB limit per individual file).

Your snapshots are small, but the cumulative history grows indefinitely.

---

# Recommended Production Architecture

```text id="k13yqy"
GitHub Actions (hourly)
        ↓
capture_html.py
        ↓
html/YYYY-MM-DD_HH-MM-SS.html
        ↓
At month end:
    zip html/YYYY-MM/*.html
        ↓
archive/2026-05.zip
        ↓
Upload to GitHub Release or external storage
        ↓
Delete raw HTML files from repository workspace
```

This design keeps the repository compact while preserving complete archives.

---

# Storage Math

Assuming 200 KB per snapshot:

* 24 files/day = 4.8 MB/day
* ~144 MB/month
* ~1.7 GB/year

After ZIP compression, HTML often compresses significantly because pages are highly repetitive. Actual ZIP sizes are often much smaller than the raw total.

---

# Option 1: Monthly ZIP Files Committed to Repository (Recommended)

Repository contents:

```text id="l1xkgi"
archive/
├── 2026-01.zip
├── 2026-02.zip
├── 2026-03.zip
```

Advantages:

* Only 12 new archive files per year
* Much fewer commits
* Easier download and backup

---

# Option 2: GitHub Releases (Best for Large Archives)

GitHub Actions can create a Release and attach `2026-05.zip`.

Advantages:

* Keeps repository size small
* Release assets are easy to download
* Good for long-term archival

---

# Option 3: External Cloud Storage

Actions can upload ZIP files to:

* OneDrive
* Google Drive
* AWS S3
* Azure Blob Storage

Best if you expect multi-year retention.

---

# My Recommended Strategy

## Short Term (First 3–6 Months)

Commit snapshots directly to the repository to validate the process.

## Production

Move to:

* Hourly capture
* Monthly ZIP compression
* Upload ZIP to GitHub Releases
* Optional deletion of raw files after archival

This gives:

* Reliable scheduling
* Off-site backup
* Compact repository
* Indefinite retention

---

# Estimated Multi-Year Storage

| Years | Raw HTML | Approximate ZIP Size (varies) |
| ----: | -------: | ----------------------------: |
|     1 |   1.7 GB |   Often substantially smaller |
|     3 |   5.1 GB |   Often substantially smaller |
|     5 |   8.5 GB |   Often substantially smaller |

---

# Recommended Final Architecture

```text id="pkf90u"
GitHub Actions
   ├── Hourly HTML capture
   ├── Monthly ZIP compression
   ├── Upload ZIP to GitHub Release
   └── Keep repository source code small
```

This is the most robust and scalable design for your project.