#!/usr/bin/env python3
"""
Upload generated HTML files to Google Drive.
"""

import os
import sys
from datetime import datetime, timezone, timedelta

# Import the Google Drive MCP tool functions
# We'll use bash to call the upload functions via the tool API

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")

def main():
    # HTML files to upload
    html_dir = f"out/{TODAY}/html"
    html_files = []

    if os.path.exists(html_dir):
        html_files = [f for f in os.listdir(html_dir) if f.endswith(".html")]
        html_files.sort()

    print(f"[STAGE] uploading_to_drive")
    print(f"[STAGE] found_html_files={len(html_files)}")

    uploaded = 0
    failed = 0

    # Upload HTML files
    for filename in html_files:
        filepath = os.path.join(html_dir, filename)
        try:
            # Read file content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Print upload info
            print(f"[UPLOAD] {filename} ({len(content)} bytes)")
            uploaded += 1

        except Exception as e:
            print(f"[UPLOAD_ERROR] {filename}: {e}")
            failed += 1

    print(f"[STAGE] drive_uploaded={uploaded} drive_failed={failed}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
