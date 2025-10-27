#!/usr/bin/env python3
"""Quick verification script for submissions"""

import os
import glob
from pathlib import Path

def verify_submissions():
    artifacts_dir = Path("./artifacts")
    
    if not artifacts_dir.exists():
        print("No artifacts directory found!")
        return
    
    print("=" * 60)
    print("SUBMISSION VERIFICATION REPORT")
    print("=" * 60)
    
    job_folders = [f for f in artifacts_dir.iterdir() if f.is_dir()]
    
    for job_folder in job_folders:
        print(f"\n📁 Job: {job_folder.name}")
        
        submission_folders = [f for f in job_folder.iterdir() if f.is_dir()]
        
        for sub_folder in submission_folders:
            print(f"  └─ Submission: {sub_folder.name}")
            
            # Check for evidence files
            html_files = list(sub_folder.glob("*.html"))
            png_files = list(sub_folder.glob("*.png"))
            
            if html_files:
                print(f"     ✓ HTML Response: {len(html_files)} file(s)")
                for html in html_files:
                    size = html.stat().st_size
                    print(f"       - {html.name} ({size} bytes)")
            
            if png_files:
                print(f"     ✓ Screenshots: {len(png_files)} file(s)")
                for png in png_files:
                    print(f"       - {png.name}")
            
            if not html_files and not png_files:
                print(f"     ⚠ No evidence files found!")
    
    print("\n" + "=" * 60)
    print(f"Total Jobs: {len(job_folders)}")
    print("=" * 60)

if __name__ == "__main__":
    verify_submissions()
