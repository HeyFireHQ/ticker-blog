import os
import yaml
import re
import requests
import shutil
import subprocess
from datetime import datetime
import sqlite3
import json
from dotenv import load_dotenv

# Get the script directory and project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BLOG_DIR = os.path.join(PROJECT_ROOT, "blog")

# Load environment variables
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# Configuration
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
D1_DATABASE_ID = os.getenv("D1_DATABASE_ID")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "cardpress-storage")
WORKER_URL = os.getenv("WORKER_URL", "https://cardpress-refresh.awesomehq.workers.dev")

# Use correct paths relative to blog directory
CONTENT_DIR = os.path.join(BLOG_DIR, "content")
IMAGES_DIR = os.path.join(CONTENT_DIR, "imgs")
OUTPUT_DIR = os.path.join(BLOG_DIR, "output")

# Ensure dirs exist
os.makedirs(CONTENT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

print(f"🏗️  CardPress - Cloudflare to Pelican Generator")
print(f"📁 Content directory: {CONTENT_DIR}")
print(f"🖼️  Images directory: {IMAGES_DIR}")
print(f"⚙️  Worker URL: {WORKER_URL}")

def slugify(value):
    """Convert title to URL-friendly slug"""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

def get_auth_token():
    """Get admin authentication token from Cloudflare Worker"""
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        response = requests.post(f"{WORKER_URL}/auth/login", json={
            "email": admin_email,
            "password": admin_password
        })
        
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        else:
            print(f"❌ Failed to authenticate: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def fetch_deployed_posts():
    """Fetch deployed posts from Cloudflare D1 via Worker API"""
    try:
        token = get_auth_token()
        if not token:
            raise Exception("Failed to get authentication token")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{WORKER_URL}/posts", headers=headers)
        
        if response.status_code == 200:
            all_posts = response.json()
            deployed_posts = [post for post in all_posts if post.get('column_status') == 'deployed']
            print(f"📝 Found {len(deployed_posts)} deployed posts")
            return deployed_posts
        else:
            print(f"❌ Failed to fetch posts: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error fetching posts: {e}")
        return []

def download_image_from_r2(image_path, save_path):
    """Download image from Cloudflare R2 via Worker"""
    try:
        if not image_path:
            return False
            
        print(f"🔽 Downloading image: {image_path} → {save_path}")
        
        # Use the worker API to fetch the image
        response = requests.get(f"{WORKER_URL}/images/{image_path}")
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Image downloaded successfully: {save_path}")
            return True
        else:
            print(f"❌ Failed to download image {image_path}: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to download image {image_path}: {e}")
        return False

def write_markdown(post):
    """Convert post data to Pelican markdown file"""
    title = post.get("title", f"Untitled-{post.get('id', 'unknown')}")
    content = post.get("content", "")
    labels = json.loads(post.get("labels", "[]"))
    image_url = post.get("image_url", "")
    image_path = post.get("image_path", "")
    
    # Handle date conversion
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    if post.get("updated_at"):
        try:
            # Try to parse the date string from D1
            date_obj = datetime.fromisoformat(post["updated_at"].replace('Z', '+00:00'))
            date_str = date_obj.strftime("%Y-%m-%d")
        except:
            pass
    
    slug = slugify(title)
    
    # Handle image download
    image_name = ""
    image_markdown = ""
    
    if image_path:
        try:
            image_name = os.path.basename(image_path)
            local_image_path = os.path.join(IMAGES_DIR, image_name)
            
            if download_image_from_r2(image_path, local_image_path):
                image_markdown = f"![{title}](/imgs/{image_name})\n\n"
            else:
                print(f"⚠️ Could not download image, using URL: {image_url}")
                if image_url:
                    image_markdown = f"![{title}]({image_url})\n\n"
                    
        except Exception as e:
            print(f"❌ Could not process image {image_path}: {e}")
    
    # Get colors from post or use defaults
    colors = post.get('colors', '#F97316, #0EA5E9, #8B5CF6, #10B981')
    if not colors or not colors.strip():
        colors = '#F97316, #0EA5E9, #8B5CF6, #10B981'
    
    # Create metadata for Pelican
    md_metadata = [
        f"Title: {title}",
        f"Date: {date_str}",
        f"Slug: {slug}",
        f"Tags: {', '.join(labels)}",
        f"Colors: {colors}",
        f"Summary: {content[:100]}..." if content else "",
    ]
    
    # Only add Image field if we have a local image
    if image_name:
        md_metadata.append(f"Image: imgs/{image_name}")
    
    # Filter out empty metadata lines
    md_metadata = [line for line in md_metadata if line.strip() and not line.endswith(": ")]
    
    # Write the markdown file
    body = "\n".join(md_metadata) + "\n\n" + image_markdown + content
    file_path = os.path.join(CONTENT_DIR, f"{slug}.md")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(body)
    
    print(f"✅ Wrote: {file_path}")

def clean_output():
    """Clean the output directory"""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
        print(f"🧹 Cleaned output directory: {OUTPUT_DIR}")

def build_pelican():
    """Build the static site with Pelican"""
    print("🛠️  Building Pelican site...")
    original_dir = os.getcwd()
    try:
        os.chdir(BLOG_DIR)
        result = subprocess.run(["pelican", "content"], check=True, capture_output=True, text=True)
        print("✅ Pelican build completed successfully")
        if result.stdout:
            print(f"📄 Pelican output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Pelican build failed: {e}")
        if e.stdout:
            print(f"📄 Stdout: {e.stdout}")
        if e.stderr:
            print(f"📄 Stderr: {e.stderr}")
        raise
    finally:
        os.chdir(original_dir)

def deploy_to_hosting():
    """Deploy the built site to hosting (Firebase or other)"""
    print("🚀 Deploying to hosting...")
    original_dir = os.getcwd()
    try:
        os.chdir(PROJECT_ROOT)
        
        # Check if firebase.json exists for Firebase hosting
        if os.path.exists("firebase.json"):
            print("📱 Deploying to Firebase Hosting...")
            subprocess.run(["firebase", "deploy", "--only", "hosting"], check=True)
            print("✅ Firebase deployment completed")
        else:
            print("⚠️  No firebase.json found, skipping hosting deployment")
            print("💡 Configure your hosting deployment method in this function")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Hosting deployment failed: {e}")
        raise
    finally:
        os.chdir(original_dir)

def main():
    """Main execution function"""
    try:
        print("🚀 Starting CardPress static site generation...")
        
        # Step 1: Clean output directory
        clean_output()
        
        # Step 2: Fetch deployed posts from Cloudflare D1
        posts = fetch_deployed_posts()
        if not posts:
            print("⚠️  No deployed posts found. Exiting.")
            return
        
        # Step 3: Convert posts to markdown
        print(f"📝 Converting {len(posts)} posts to markdown...")
        for post in posts:
            write_markdown(post)
        
        # Step 4: Build static site with Pelican
        build_pelican()
        
        # Step 5: Deploy to hosting
        deploy_to_hosting()
        
        print("🎉 Static site generation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during static site generation: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        exit(exit_code) 