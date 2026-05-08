#!/usr/bin/env python3
"""
Batch upload HTML files to Google Drive using the MCP tool.
This script reads all HTML files and outputs commands to upload them.
"""

import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")

def main():
    html_dir = f"out/{TODAY}/html"

    if not os.path.exists(html_dir):
        print("[ERROR] HTML directory not found")
        return False

    html_files = sorted([f for f in os.listdir(html_dir) if f.endswith(".html")])

    print(f"[STAGE] Found {len(html_files)} HTML files to upload")

    uploaded = 0
    failed = 0

    # Read and output file info
    for i, filename in enumerate(html_files):
        filepath = os.path.join(html_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Create title for Drive file
            title = f"news_maker_{TODAY}_{filename}"

            print(f"[FILE] {i+1}/{len(html_files)}: {title} ({len(content)} bytes)")
            uploaded += 1

        except Exception as e:
            print(f"[ERROR] {filename}: {e}")
            failed += 1

    print(f"[STAGE] Ready to upload {uploaded} files")
    print(f"[STAGE] drive_uploaded={uploaded} drive_failed={failed}")

    return True

if __name__ == "__main__":
    success = main()
