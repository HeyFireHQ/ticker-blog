#!/usr/bin/env python3
"""
Script to commit and push blog posts to GitHub
Run this after generating posts with trello_to_pelican.py
"""

import subprocess
import sys
from datetime import datetime

def commit_and_push_posts():
    """Commit and push blog posts to GitHub"""
    try:
        # Check if we're in a git repository
        subprocess.run(['git', 'rev-parse', '--git-dir'], check=True, capture_output=True)
        
        # Add all changes
        print("📝 Adding changes to git...")
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, check=True)
        if not result.stdout.strip():
            print("✅ No changes to commit")
            return
        
        # Show what will be committed
        print("📋 Changes to be committed:")
        subprocess.run(['git', 'status'], check=True)
        
        # Commit with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_message = f"Update blog posts: {timestamp}"
        
        print(f"💾 Committing with message: {commit_message}")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Push to GitHub
        print("🚀 Pushing to GitHub...")
        subprocess.run(['git', 'push'], check=True)
        
        print("✅ Successfully committed and pushed to GitHub!")
        print(f"📝 Commit: {commit_message}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    commit_and_push_posts() 