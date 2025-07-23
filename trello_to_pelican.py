import os
import shutil
import re
import requests
import yaml
import json
import base64
from dotenv import load_dotenv
from datetime import datetime
from discord import SyncWebhook, File

# Load environment variables
load_dotenv('.env')

TRELLO_API_KEY = os.getenv('TRELLO_API_KEY')
TRELLO_TOKEN = os.getenv('TRELLO_TOKEN')
BOARD_ID = os.getenv('BOARD_ID')
DISCORD_PUBLIC = os.getenv('DISCORD_PUBLIC')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'your-username/ticker-blog')  # format: owner/repo
CLOUDFLARE_DEPLOY_HOOK = os.getenv('CLOUDFLARE_DEPLOY_HOOK')

CONTENT_DIR = 'blog/content'
IMAGES_DIR = os.path.join(CONTENT_DIR, 'imgs')
ALLOWED_LISTS = ["Ready to Publish", "Published"]

# Mapping of Trello label color names to HEX codes
TRELLO_COLOR_HEX = {
    'green': '#61BD4F',
    'yellow': '#F2D600',
    'orange': '#FF9F1A',
    'red': '#EB5A46',
    'purple': '#C377E0',
    'blue': '#0079BF',
    'sky': '#00C2E0',
    'pink': '#FF78CB',
    'black': '#344563',
    'lime': '#51e898',
    'null': ''
}


def send_message_to_discord(message, file_stream=None):
    try:
        discord_url = DISCORD_PUBLIC 
        webhook = SyncWebhook.from_url(discord_url) # Initializing webhook
        if file_stream:
            import io
            import base64
            file_stream = file_stream.split(',')[1]
            
            # Decode base64 image
            file_stream = base64.b64decode(file_stream)
            file_stream = io.BytesIO(file_stream)
            file = File(file_stream, filename=message+'.png')
            webhook.send(content=message, file=file)
        else:
            webhook.send(content=message)
    except:
        pass

# --- Helpers ---

def fetch_trello_cards():
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards?attachments=true&labels=all&key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def fetch_trello_lists():
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists?key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def slugify(value):
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-')

def extract_markdown_link(text):
    """Extract name and URL from markdown link [name](url)"""
    match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', text.strip())
    if match:
        return match.group(1), match.group(2)  # name, url
    return text.strip(), None

def parse_front_matter(text):
    front_matter = {}
    body = text

    if text.strip().startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            yaml_block = parts[1]
            body = parts[2].lstrip('\n')
            
            try:
                front_matter = yaml.safe_load(yaml_block) or {}
                
                # Post-process author field if it contains markdown
                if 'author' in front_matter:
                    author_text = str(front_matter['author'])
                    if '[' in author_text and '](' in author_text:
                        name, url = extract_markdown_link(author_text)
                        front_matter['author-name'] = name
                        front_matter['author-url'] = url
                        del front_matter['author']
                        
            except yaml.YAMLError as e:
                print(f"⚠️ YAML parsing error: {e}")
                front_matter = {}

    return front_matter, body

def download_image(url, save_path):
    headers = {
        "Accept": "application/json"
    }
    if "trello.com" in url:
        if '?' in url:
            url += f"&key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
        else:
            url += f"?key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    with open(save_path, 'wb') as f:
        f.write(response.content)

    return save_path

#os.makedirs(CONTENT_DIR)
#os.makedirs(IMAGES_DIR)

def get_github_file_sha(path):
    """Get the SHA of a file in GitHub"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()['sha']
        return None
    except Exception as e:
        print(f"⚠️ Error getting file SHA: {e}")
        return None

def commit_to_github(file_path, content, message):
    """Commit a file to GitHub using the API"""
    try:
        # Get current file SHA if it exists
        sha = get_github_file_sha(file_path)
        
        # Prepare the commit data
        commit_data = {
            'message': message,
            'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
            'branch': 'main'
        }
        
        if sha:
            commit_data['sha'] = sha
        
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.put(url, headers=headers, json=commit_data)
        
        if response.status_code in [200, 201]:
            print(f"✅ Successfully committed {file_path}")
            return True
        else:
            print(f"❌ Failed to commit {file_path}: {response.status_code}")
            if response.status_code == 403:
                print("   This usually means the GitHub token doesn't have write permissions")
            elif response.status_code == 404:
                print("   This usually means the repository path is incorrect")
            return False
            
    except Exception as e:
        print(f"❌ Error committing to GitHub: {e}")
        return False

def delete_from_github(file_path, message):
    """Delete a file from GitHub using the API"""
    try:
        sha = get_github_file_sha(file_path)
        if not sha:
            print(f"⚠️ File {file_path} not found in GitHub")
            return True
        
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'message': message,
            'sha': sha
        }
        
        response = requests.delete(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"✅ Successfully deleted {file_path}")
            return True
        else:
            print(f"❌ Failed to delete {file_path}: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting from GitHub: {e}")
        return False

def sync_posts_to_github():
    """Sync all posts to GitHub and handle deletions"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("⚠️ GitHub token or repo not configured, skipping GitHub sync")
        return
    
    try:
        # Test GitHub API access first
        test_url = f"https://api.github.com/repos/{GITHUB_REPO}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        test_response = requests.get(test_url, headers=headers)
        if test_response.status_code != 200:
            print(f"❌ Cannot access GitHub repository: {test_response.status_code}")
            print("Please check your GITHUB_TOKEN and GITHUB_REPO settings")
            return
        
        # Get list of current files in GitHub
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/blog/content"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            github_files = {item['name'] for item in response.json() if item['type'] == 'file'}
        else:
            github_files = set()
        
        # Get list of local files
        local_files = set()
        if os.path.exists(CONTENT_DIR):
            for file in os.listdir(CONTENT_DIR):
                if file.endswith('.md'):
                    local_files.add(file)
        
        # Files to add/update
        files_to_commit = []
        for file in local_files:
            file_path = os.path.join(CONTENT_DIR, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            files_to_commit.append((f"blog/content/{file}", content))
        
        # Files to delete
        files_to_delete = github_files - local_files
        
        # Commit changes
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add/update files
        success_count = 0
        for file_path, content in files_to_commit:
            message = f"Update blog posts: {timestamp}"
            if commit_to_github(file_path, content, message):
                success_count += 1
        
        # Delete removed files
        for file in files_to_delete:
            message = f"Remove deleted post: {timestamp}"
            delete_from_github(f"blog/content/{file}", message)
        
        if success_count > 0:
            print(f"✅ Successfully synced {success_count} posts to GitHub")
            
            # Trigger Cloudflare deploy
            if CLOUDFLARE_DEPLOY_HOOK:
                try:
                    deploy_response = requests.post(CLOUDFLARE_DEPLOY_HOOK)
                    if deploy_response.ok:
                        print("✅ Cloudflare deploy triggered")
                        send_message_to_discord("✅ Blog updated and deploy triggered!")
                    else:
                        print("⚠️ Failed to trigger Cloudflare deploy")
                except Exception as e:
                    print(f"⚠️ Error triggering deploy: {e}")
        else:
            print("⚠️ No posts were successfully synced to GitHub")
        
        print("✅ GitHub sync completed!")
        
    except Exception as e:
        error_msg = f"❌ Error syncing to GitHub: {str(e)}"
        print(error_msg)
        send_message_to_discord(error_msg)

def push_generated_blog_to_branch(branch_name='generated-site'):
    """Push the full generated blog to a separate branch for hosting"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("⚠️ GitHub token or repo not configured, skipping blog deployment")
        return
    
    try:
        # First, build the blog if not already built
        import subprocess
        print("🔨 Building blog with Pelican...")
        subprocess.run(['cd', 'blog', '&&', 'pelican', 'content', '-s', 'pelicanconf.py'], 
                      shell=True, check=True)
        
        # Get the current tree SHA for the target branch
        url = f"https://api.github.com/repos/{GITHUB_REPO}/branches/{branch_name}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            base_tree = response.json()['commit']['sha']
        else:
            # Branch doesn't exist, we'll create it from main
            main_response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/branches/main", headers=headers)
            if main_response.status_code == 200:
                base_tree = main_response.json()['commit']['sha']
            else:
                print(f"❌ Could not find base branch for {branch_name}")
                return
        
        # Create a new tree with all the generated files
        tree_items = []
        output_dir = 'blog/output'
        
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, output_dir)
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                tree_items.append({
                    'path': relative_path,
                    'mode': '100644',
                    'type': 'blob',
                    'content': content.decode('utf-8') if file.endswith(('.html', '.css', '.js', '.xml', '.txt')) else base64.b64encode(content).decode('utf-8')
                })
        
        # Create the tree
        tree_data = {'tree': tree_items}
        tree_response = requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/git/trees", 
                                    headers=headers, json=tree_data)
        
        if tree_response.status_code != 201:
            print(f"❌ Failed to create tree: {tree_response.status_code}")
            return
        
        tree_sha = tree_response.json()['sha']
        
        # Create the commit
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_data = {
            'message': f'Deploy blog: {timestamp}',
            'tree': tree_sha,
            'parents': [base_tree]
        }
        
        commit_response = requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/git/commits", 
                                      headers=headers, json=commit_data)
        
        if commit_response.status_code != 201:
            print(f"❌ Failed to create commit: {commit_response.status_code}")
            return
        
        commit_sha = commit_response.json()['sha']
        
        # Update the branch reference
        ref_data = {'sha': commit_sha}
        ref_response = requests.patch(f"https://api.github.com/repos/{GITHUB_REPO}/git/refs/heads/{branch_name}", 
                                    headers=headers, json=ref_data)
        
        if ref_response.status_code == 200:
            print(f"✅ Successfully deployed blog to {branch_name} branch")
            send_message_to_discord(f"✅ Blog deployed to {branch_name} branch")
        else:
            # Try to create the branch if it doesn't exist
            ref_data = {'ref': f'refs/heads/{branch_name}', 'sha': commit_sha}
            create_response = requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/git/refs", 
                                          headers=headers, json=ref_data)
            
            if create_response.status_code == 201:
                print(f"✅ Successfully created and deployed blog to {branch_name} branch")
                send_message_to_discord(f"✅ Blog deployed to new {branch_name} branch")
            else:
                print(f"❌ Failed to deploy to {branch_name}: {create_response.status_code}")
        
    except Exception as e:
        error_msg = f"❌ Error deploying blog to {branch_name}: {str(e)}"
        print(error_msg)
        send_message_to_discord(error_msg)

# --- Main build ---

cards = fetch_trello_cards()
lists = fetch_trello_lists()
list_mapping = {lst['id']: lst['name'] for lst in lists}

for card in cards:
    try:
        card_list_name = list_mapping.get(card['idList'], "")

        if card_list_name not in ALLOWED_LISTS:
            continue  # Skip drafts etc

        original_title = card['name']
        description_full = card['desc']
        attachments = card.get('attachments', [])
        labels = [label['name'] for label in card['labels']]

        # NEW: capture label colors
        label_colors = []
        for label in card['labels']:
            color_name = label.get('color')
            if color_name and color_name in TRELLO_COLOR_HEX:
                label_colors.append(TRELLO_COLOR_HEX[color_name])

        # Parse front matter
        front_matter, description_md = parse_front_matter(description_full)

        # Get date - priority: front matter > card creation date
        custom_date = front_matter.get('date', None)
        if custom_date:
            article_date = custom_date
        else:
            # Extract date from card ID (creation date)
            card_id = card['id']
            timestamp = int(card_id[:8], 16)
            card_date = datetime.fromtimestamp(timestamp)
            article_date = card_date.strftime('%Y-%m-%d')

        slug = front_matter.get('slug') or slugify(original_title)
        author = front_matter.get('author-name', None)
        author_url = front_matter.get('author-url', None)
        description = front_matter.get('description', None)
        keywords = front_matter.get('keywords', None)
        custom_image_name = front_matter.get('image', None)

        image_markdown = ""

        # If attachment exists, download properly
        if attachments:
            image_url = attachments[0]['url']
            if not custom_image_name:
                custom_image_name = os.path.basename(image_url.split('?')[0])

            image_save_path = os.path.join(IMAGES_DIR, custom_image_name)
            
            try:
                result = download_image(image_url, image_save_path)
                image_markdown = f"![{original_title}](imgs/{custom_image_name})\n\n"
            except Exception as e:
                print(f"⚠️ Failed to download {image_url}: {e}")
                image_markdown = f"![{original_title}]({image_url})\n\n"

        # Prepare metadata
        metadata = [
            f"Title: {original_title}",
            f"Date: {article_date}",  # Use the extracted date
            f"Slug: {slug}",
            f"Image: {image_url}"
        ]
        if author:
            metadata.append(f"Author: {author}")
        if author_url:
            metadata.append(f"Authorurl: {author_url}")
        if description:
            metadata.append(f"Description: {description}")
        if keywords:
            metadata.append(f"Keywords: {keywords}")
        if labels:
            metadata.append(f"Tags: {', '.join(labels)}")
        if label_colors:
            metadata.append(f"Colors: {', '.join(label_colors)}")
        else:
            metadata.append(f"Colors: #F97316")

        # Full file content
        file_content = '\n'.join(metadata) + '\n\n' + description_md

        # Write to file
        post_filename = f"{slug}.md"
        post_path = os.path.join(CONTENT_DIR, post_filename)

        with open(post_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        send_message_to_discord(f"New post: {original_title}")
    
    except Exception as e:
        error_message = f"❌ Error processing card '{card.get('name', 'Unknown')}': {str(e)}"
        print(error_message)
        send_message_to_discord(error_message)

print("✅ Markdown files with downloaded images and colors generated successfully!")

# Sync to GitHub
sync_posts_to_github()

# Deploy full blog to separate branch (commented out to prevent errors)
push_generated_blog_to_branch('generated-site') 
