#!/usr/bin/env python3
"""
Deploy generated markdown files to GitHub 'md' branch for Cloudflare deployment.
This script will:
1. Copy only the markdown files from blog/content/
2. Push to GitHub 'md' branch using GitHub API
3. Trigger Cloudflare deployment via webhook
"""

import os
import requests
import base64
import json
import shutil
import glob
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'your-username/ticker-blog')  # format: owner/repo
CLOUDFLARE_DEPLOY_HOOK = os.getenv('CLOUDFLARE_DEPLOY_HOOK')

def get_github_headers():
    """Get headers for GitHub API requests."""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    return {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }

def get_file_content_base64(file_path):
    """Read file and return base64 encoded content."""
    with open(file_path, 'rb') as f:
        content = f.read()
    return base64.b64encode(content).decode('utf-8')

def get_branch_sha(branch_name):
    """Get the SHA of the latest commit on a branch."""
    url = f'https://api.github.com/repos/{GITHUB_REPO}/git/refs/heads/{branch_name}'
    response = requests.get(url, headers=get_github_headers())
    
    if response.status_code == 404:
        return None  # Branch doesn't exist
    elif response.status_code == 200:
        return response.json()['object']['sha']
    else:
        print(f"❌ Error getting branch SHA: {response.status_code}")
        print(response.text)
        return False

def create_or_update_file(file_path, content, commit_message):
    """Create or update a file in the GitHub repository."""
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}'
    
    # Check if file exists to get its SHA
    response = requests.get(url, headers=get_github_headers(), params={'ref': 'md'})
    
    data = {
        'message': commit_message,
        'content': content,
        'branch': 'md'
    }
    
    if response.status_code == 200:
        # File exists, include SHA for update
        data['sha'] = response.json()['sha']
    
    # Create or update the file
    response = requests.put(url, headers=get_github_headers(), json=data)
    
    if response.status_code in [200, 201]:
        return True
    else:
        print(f"❌ Error creating/updating {file_path}: {response.status_code}")
        print(response.text)
        return False

def delete_file(file_path, commit_message):
    """Delete a file from the GitHub repository."""
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}'
    
    # Get file SHA
    response = requests.get(url, headers=get_github_headers(), params={'ref': 'md'})
    
    if response.status_code != 200:
        return True  # File doesn't exist, nothing to delete
    
    file_sha = response.json()['sha']
    
    data = {
        'message': commit_message,
        'sha': file_sha,
        'branch': 'md'
    }
    
    response = requests.delete(url, headers=get_github_headers(), json=data)
    
    if response.status_code == 200:
        return True
    else:
        print(f"❌ Error deleting {file_path}: {response.status_code}")
        print(response.text)
        return False

def get_existing_files():
    """Get list of existing files in the md branch."""
    url = f'https://api.github.com/repos/{GITHUB_REPO}/git/trees/md?recursive=1'
    response = requests.get(url, headers=get_github_headers())
    
    if response.status_code == 404:
        return []  # Branch doesn't exist yet
    elif response.status_code == 200:
        tree = response.json().get('tree', [])
        return [item['path'] for item in tree if item['type'] == 'blob']
    else:
        print(f"❌ Error getting existing files: {response.status_code}")
        return []

def trigger_cloudflare_deployment():
    """Trigger Cloudflare deployment via webhook."""
    if not CLOUDFLARE_DEPLOY_HOOK:
        print("ℹ️  No Cloudflare deploy hook configured, skipping...")
        return True
    
    print("🌐 Triggering Cloudflare deployment...")
    try:
        response = requests.post(CLOUDFLARE_DEPLOY_HOOK)
        if response.status_code == 200:
            print("✅ Cloudflare deployment triggered successfully!")
            return True
        else:
            print(f"❌ Failed to trigger Cloudflare deployment: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error triggering Cloudflare deployment: {e}")
        return False

def deploy_md_files():
    """Deploy markdown files to md branch using GitHub API."""
    print("🚀 Starting deployment to 'md' branch via GitHub API...")
    
    # Validate environment variables
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN environment variable is required!")
        return False
    
    if not GITHUB_REPO or GITHUB_REPO == 'your-username/ticker-blog':
        print("❌ GITHUB_REPO environment variable must be set (format: owner/repo)!")
        return False
    
    # Check if blog/content directory exists
    content_dir = "blog/content"
    if not os.path.exists(content_dir):
        print(f"❌ Content directory {content_dir} not found!")
        return False
    
    # Get markdown files
    print("📄 Collecting markdown files...")
    md_files = glob.glob(f"{content_dir}/*.md")
    
    if not md_files:
        print("❌ No markdown files found to deploy!")
        return False
    
    # Get existing files to know what to delete
    existing_files = get_existing_files()
    files_to_keep = set()
    
    # Upload markdown files
    commit_message = "Auto-deploy: Update markdown content"
    
    for md_file in md_files:
        filename = os.path.basename(md_file)
        github_path = f"content/{filename}"
        files_to_keep.add(github_path)
        
        content_base64 = get_file_content_base64(md_file)
        
        if create_or_update_file(github_path, content_base64, commit_message):
            print(f"✅ Uploaded {filename}")
        else:
            print(f"❌ Failed to upload {filename}")
            return False
    
    # Upload images if they exist
    images_dir = f"{content_dir}/imgs"
    if os.path.exists(images_dir):
        print("🖼️  Uploading images...")
        for root, dirs, files in os.walk(images_dir):
            for file in files:
                local_path = os.path.join(root, file)
                # Get relative path from imgs directory
                rel_path = os.path.relpath(local_path, images_dir)
                github_path = f"content/imgs/{rel_path}".replace('\\', '/')
                files_to_keep.add(github_path)
                
                content_base64 = get_file_content_base64(local_path)
                
                if create_or_update_file(github_path, content_base64, commit_message):
                    print(f"✅ Uploaded image {rel_path}")
                else:
                    print(f"❌ Failed to upload image {rel_path}")
                    return False
    
    # Create README
    readme_content = """# Markdown Content Branch

This branch contains only the generated markdown files for deployment.

- `content/` - Blog post markdown files
- `content/imgs/` - Associated images

This branch is automatically updated by the deployment script.
"""
    
    readme_base64 = base64.b64encode(readme_content.encode('utf-8')).decode('utf-8')
    files_to_keep.add("README.md")
    
    if create_or_update_file("README.md", readme_base64, commit_message):
        print("✅ Updated README.md")
    else:
        print("❌ Failed to update README.md")
        return False
    
    # Delete files that are no longer needed
    files_to_delete = set(existing_files) - files_to_keep
    for file_path in files_to_delete:
        if delete_file(file_path, "Auto-deploy: Remove outdated files"):
            print(f"🗑️  Deleted {file_path}")
        else:
            print(f"❌ Failed to delete {file_path}")
    
    print("✅ Successfully deployed to 'md' branch!")
    
    # Trigger Cloudflare deployment
    trigger_cloudflare_deployment()
    
    print("🎉 Deployment complete!")
    return True

if __name__ == "__main__":
    success = deploy_md_files()
    if not success:
        exit(1) 