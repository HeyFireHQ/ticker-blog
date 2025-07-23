#!/usr/bin/env python3
"""
Standalone script to deploy the generated blog to a separate branch
Usage: python deploy_blog.py [branch_name]
"""

import os
import subprocess
import requests
import base64
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

def build_blog():
    """Build the blog using Pelican"""
    try:
        print("🔨 Building blog with Pelican...")
        subprocess.run(['cd', 'blog', '&&', 'pelican', 'content', '-s', 'pelicanconf.py'], 
                      shell=True, check=True)
        print("✅ Blog built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build blog: {e}")
        return False

def deploy_to_branch(branch_name='generated-site'):
    """Deploy the full generated blog to a separate branch"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("❌ GitHub token or repo not configured")
        print("Please set GITHUB_TOKEN and GITHUB_REPO in your .env file")
        return False
    
    try:
        # Build the blog first
        if not build_blog():
            return False
        
        # Get the current tree SHA for the target branch
        url = f"https://api.github.com/repos/{GITHUB_REPO}/branches/{branch_name}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            base_tree = response.json()['commit']['sha']
            print(f"📦 Found existing {branch_name} branch")
        else:
            # Branch doesn't exist, we'll create it from main
            main_response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/branches/main", headers=headers)
            if main_response.status_code == 200:
                base_tree = main_response.json()['commit']['sha']
                print(f"🆕 Will create new {branch_name} branch from main")
            else:
                print(f"❌ Could not find base branch for {branch_name}")
                return False
        
        # Create a new tree with all the generated files
        tree_items = []
        output_dir = 'blog/output'
        
        print("📁 Collecting generated files...")
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, output_dir)
                
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # Determine if content should be base64 encoded
                    if file.endswith(('.html', '.css', '.js', '.xml', '.txt', '.json')):
                        try:
                            file_content = content.decode('utf-8')
                        except UnicodeDecodeError:
                            # If UTF-8 fails, use base64
                            file_content = base64.b64encode(content).decode('utf-8')
                    else:
                        file_content = base64.b64encode(content).decode('utf-8')
                    
                    tree_items.append({
                        'path': relative_path,
                        'mode': '100644',
                        'type': 'blob',
                        'content': file_content
                    })
                except Exception as e:
                    print(f"⚠️ Skipping {file_path}: {e}")
                    continue
        
        print(f"📦 Creating tree with {len(tree_items)} files...")
        
        # Create the tree
        tree_data = {'tree': tree_items}
        tree_response = requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/git/trees", 
                                    headers=headers, json=tree_data)
        
        if tree_response.status_code != 201:
            print(f"❌ Failed to create tree: {tree_response.status_code}")
            print(f"Response: {tree_response.text}")
            return False
        
        tree_sha = tree_response.json()['sha']
        print("✅ Tree created successfully")
        
        # Create the commit
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_data = {
            'message': f'Deploy blog: {timestamp}',
            'tree': tree_sha,
            'parents': [base_tree]
        }
        
        print("💾 Creating commit...")
        commit_response = requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/git/commits", 
                                      headers=headers, json=commit_data)
        
        if commit_response.status_code != 201:
            print(f"❌ Failed to create commit: {commit_response.status_code}")
            print(f"Response: {commit_response.text}")
            return False
        
        commit_sha = commit_response.json()['sha']
        print("✅ Commit created successfully")
        
        # Update the branch reference
        ref_data = {'sha': commit_sha}
        ref_response = requests.patch(f"https://api.github.com/repos/{GITHUB_REPO}/git/refs/heads/{branch_name}", 
                                    headers=headers, json=ref_data)
        
        if ref_response.status_code == 200:
            print(f"✅ Successfully deployed blog to {branch_name} branch")
            return True
        else:
            # Try to create the branch if it doesn't exist
            ref_data = {'ref': f'refs/heads/{branch_name}', 'sha': commit_sha}
            create_response = requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/git/refs", 
                                          headers=headers, json=ref_data)
            
            if create_response.status_code == 201:
                print(f"✅ Successfully created and deployed blog to {branch_name} branch")
                return True
            else:
                print(f"❌ Failed to deploy to {branch_name}: {create_response.status_code}")
                print(f"Response: {create_response.text}")
                return False
        
    except Exception as e:
        print(f"❌ Error deploying blog to {branch_name}: {str(e)}")
        return False

if __name__ == "__main__":
    # Get branch name from command line argument, default to 'generated-site'
    branch_name = sys.argv[1] if len(sys.argv) > 1 else 'generated-site'
    
    print(f"🚀 Deploying blog to {branch_name} branch...")
    
    if deploy_to_branch(branch_name):
        print(f"🎉 Blog successfully deployed to {branch_name} branch!")
        print(f"🌐 You can now host this branch on GitHub Pages or any static hosting service")
    else:
        print("❌ Deployment failed")
        sys.exit(1) 