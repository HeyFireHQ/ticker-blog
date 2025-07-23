import os
import yaml
import re
import requests
import shutil
import subprocess
from datetime import datetime
from google.cloud import firestore, storage
from dotenv import load_dotenv

# Get the script directory and project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BLOG_DIR = os.path.join(PROJECT_ROOT, "blog")

# Load environment variables
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# Load Firebase credentials from env
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("FIREBASE_SERVICE_ACCOUNT", 
                                                         os.path.join(PROJECT_ROOT, "serviceAccountKey.json"))

# Setup Firestore and Storage
db = firestore.Client()
bucket = storage.Client().bucket(os.getenv("FIREBASE_BUCKET_NAME"))

# Use correct paths relative to blog directory
CONTENT_DIR = os.path.join(BLOG_DIR, "content")
IMAGES_DIR = os.path.join(CONTENT_DIR, "imgs")
OUTPUT_DIR = os.path.join(BLOG_DIR, "output")

# Ensure dirs exist
os.makedirs(CONTENT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

def slugify(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

def download_image(firebase_path, save_path):
    blob = bucket.blob(firebase_path)
    blob.download_to_filename(save_path)
    return save_path

def write_markdown(post, doc_id):
    title = post.get("title", f"Untitled-{doc_id}")
    content = post.get("content", "")
    labels = post.get("labels", [])
    image_url = post.get("imageUrl", None)
    
    # Handle date conversion - Firebase returns datetime objects
    date_obj = post.get("updatedAt") or post.get("createdAt")
    if date_obj:
        if hasattr(date_obj, 'strftime'):
            # It's already a datetime object
            date_str = date_obj.strftime("%Y-%m-%d")
        else:
            # Try to parse as ISO string
            try:
                date_str = datetime.fromisoformat(str(date_obj)).strftime("%Y-%m-%d")
            except:
                date_str = datetime.utcnow().strftime("%Y-%m-%d")
    else:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    slug = slugify(title)

    image_name = ""
    image_markdown = ""
    if image_url and "firebase" in image_url:
        firebase_path = image_url.split("/o/")[1].split("?")[0].replace("%2F", "/")
        image_name = os.path.basename(firebase_path)
        local_image_path = os.path.join(IMAGES_DIR, image_name)
        try:
            download_image(firebase_path, local_image_path)
            image_markdown = f"![{title}](imgs/{image_name})\n\n"
        except Exception as e:
            print(f"Could not download image {firebase_path}: {e}")

    md_metadata = [
        f"Title: {title}",
        f"Date: {date_str}",
        f"Slug: {slug}",
        f"Tags: {', '.join(labels)}",
        f"Image: {image_name}",
    ]

    body = "\n".join(md_metadata) + "\n\n" + image_markdown + content
    path = os.path.join(CONTENT_DIR, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"✅ Wrote: {path}")

def fetch_blog_posts():
    # Fetch from the admin app's posts collection
    # Using the same structure as the admin interface
    app_id = "lastmachine-web"
    
    print(f"🔍 Fetching posts from Firebase for app: {app_id}")
    
    # Get all users and their posts (since we want all published posts)
    users_ref = db.collection(f"artifacts/{app_id}/users")
    
    try:
        users = list(users_ref.stream())
        print(f"📁 Found {len(users)} users")
        
        total_posts = 0
        for user in users:
            print(f"👤 Processing user: {user.id}")
            posts_ref = db.collection(f"artifacts/{app_id}/users/{user.id}/posts")
            posts = list(posts_ref.where("column", "==", "deployed").stream())
            
            print(f"📝 Found {len(posts)} deployed posts for user {user.id}")
            
            for doc in posts:
                write_markdown(doc.to_dict(), doc.id)
                total_posts += 1
        
        print(f"✅ Total posts processed: {total_posts}")
        
    except Exception as e:
        print(f"❌ Error fetching posts: {e}")
        raise

def build_pelican():
    print("🛠️ Building Pelican site...")
    # Change to blog directory and run pelican
    original_dir = os.getcwd()
    try:
        os.chdir(BLOG_DIR)
        subprocess.run(["pelican", "content"], check=True)
    finally:
        os.chdir(original_dir)

def deploy_to_firebase():
    print("🚀 Deploying to Firebase Hosting...")
    # Change to project root for Firebase deployment
    original_dir = os.getcwd()
    try:
        os.chdir(PROJECT_ROOT)
        subprocess.run(["firebase", "deploy"], check=True)
    finally:
        os.chdir(original_dir)

def clean_output():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

if __name__ == "__main__":
    clean_output()
    fetch_blog_posts()
    build_pelican()
    deploy_to_firebase()
