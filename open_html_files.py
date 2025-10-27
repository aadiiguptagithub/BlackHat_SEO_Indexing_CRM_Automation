#!/usr/bin/env python3
"""Open HTML files in browser for verification"""

import os
import webbrowser
from pathlib import Path

def open_html_files():
    artifacts_dir = Path("./artifacts")
    
    if not artifacts_dir.exists():
        print("❌ No artifacts directory found!")
        return
    
    html_files = list(artifacts_dir.glob("**/*.html"))
    
    if not html_files:
        print("❌ No HTML files found!")
        return
    
    print(f"Found {len(html_files)} HTML files\n")
    
    for i, html_file in enumerate(html_files, 1):
        rel_path = html_file.relative_to(artifacts_dir)
        print(f"{i}. {rel_path}")
    
    print("\n" + "="*60)
    choice = input("Enter file number to open (or 'all' to open all): ").strip()
    
    if choice.lower() == 'all':
        for html_file in html_files:
            print(f"Opening: {html_file.name}")
            webbrowser.open(html_file.absolute().as_uri())
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(html_files):
                html_file = html_files[idx]
                print(f"Opening: {html_file}")
                webbrowser.open(html_file.absolute().as_uri())
            else:
                print("Invalid number!")
        except ValueError:
            print("Invalid input!")

if __name__ == "__main__":
    open_html_files()
