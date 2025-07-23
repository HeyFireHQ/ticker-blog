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
bucket_name = os.getenv("FIREBASE_BUCKET_NAME", "lastmachine-web.firebasestorage.app")
bucket = storage.Client().bucket(bucket_name)
print(f"🪣 Using storage bucket: {bucket_name}")

# Debug: Print which project we're connected to
try:
    project_id = db._client._project
    print(f"🔗 Connected to Firebase project: {project_id}")
except:
    print(f"🔗 Connected to Firebase (project ID unknown)")

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
    try:
        print(f"🔽 Downloading image: {firebase_path} → {save_path}")
        blob = bucket.blob(firebase_path)
        blob.download_to_filename(save_path)
        print(f"✅ Image downloaded successfully: {save_path}")
        return save_path
    except Exception as e:
        print(f"❌ Failed to download image {firebase_path}: {e}")
        return None

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
        try:
            # Extract the file path from Firebase Storage URL
            firebase_path = image_url.split("/o/")[1].split("?")[0].replace("%2F", "/")
            image_name = os.path.basename(firebase_path)
            local_image_path = os.path.join(IMAGES_DIR, image_name)
            
            # Download the image
            if download_image(firebase_path, local_image_path):
                image_markdown = f"![{title}](/imgs/{image_name})\n\n"
            else:
                print(f"⚠️ Using original image URL as fallback: {image_url}")
                image_markdown = f"![{title}]({image_url})\n\n"
                image_name = ""  # Clear image_name if download failed
                
        except Exception as e:
            print(f"❌ Could not process image {image_url}: {e}")
            image_name = ""

    # Get colors from post or use defaults for theme compatibility
    colors = post.get('colors', '#F97316, #0EA5E9, #8B5CF6, #10B981')
    if not colors or not colors.strip():
        colors = '#F97316, #0EA5E9, #8B5CF6, #10B981'
    
    # Create metadata 
    md_metadata = [
        f"Title: {title}",
        f"Date: {date_str}",
        f"Slug: {slug}",
        f"Tags: {', '.join(labels)}",
        f"Colors: {colors}",
        f"Summary: {post.get('content', '')[:100]}..." if post.get('content') else "",
    ]
    
    # Only add Image field if we have a local image
    if image_name:
        md_metadata.append(f"Image: imgs/{image_name}")
    
    # Filter out empty metadata lines
    md_metadata = [line for line in md_metadata if line.strip() and not line.endswith(": ")]

    body = "\n".join(md_metadata) + "\n\n" + image_markdown + content
    path = os.path.join(CONTENT_DIR, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"✅ Wrote: {path}")

def test_firebase_connection():
    """Test if we can read/write to Firebase"""
    print(f"🧪 Testing Firebase connection...")
    
    try:
        # Try to write a test document
        test_ref = db.collection("test").document("connection_test")
        test_ref.set({
            "timestamp": datetime.utcnow(),
            "message": "Connection test from Python script"
        })
        print(f"✅ Write test: SUCCESS")
        
        # Try to read it back
        doc = test_ref.get()
        if doc.exists:
            print(f"✅ Read test: SUCCESS - {doc.to_dict()}")
        else:
            print(f"❌ Read test: FAILED - Document not found")
            
        # Clean up
        test_ref.delete()
        print(f"✅ Cleanup: SUCCESS")
        
    except Exception as e:
        print(f"❌ Firebase connection test FAILED: {e}")
        return False
    
    return True

def fetch_blog_posts():
    # Fetch from the admin app's posts collection
    app_id = "lastmachine-web"
    
    print(f"🔍 Fetching posts from Firebase for app: {app_id}")
    
    try:
        
        # Try to find all users with posts by checking known patterns
        # This approach works even when user documents don't exist
        print(f"🔍 Searching for all users with posts...")
        
        # Start with the known user, then we can expand this list
        known_user_ids = ["pUGcoHniwgbgyFXpUzZxgI1uJKD2"]
        # In the future, you could add: Auth.listUsers() or maintain a user list
        
        total_posts = 0
        for user_id in known_user_ids:
            print(f"👤 Checking user: {user_id}")
            posts_ref = db.collection(f"artifacts/{app_id}/users/{user_id}/posts")
            
            try:
                deployed_posts = list(posts_ref.where("column", "==", "deployed").stream())
                print(f"📝 Found {len(deployed_posts)} deployed posts for user {user_id}")
                
                for post_doc in deployed_posts:
                    post_data = post_doc.to_dict()
                    title = post_data.get('title', 'No title')
                    print(f"📝 Processing post: '{title}'")
                    write_markdown(post_data, post_doc.id)
                    total_posts += 1
                    
            except Exception as e:
                print(f"❌ Error processing user {user_id}: {e}")
        
        print(f"✅ Total posts processed: {total_posts}")
        
        # Note: For new users, add their user IDs to the known_user_ids list above
        
    except Exception as e:
        print(f"❌ Error fetching posts: {e}")
        import traceback
        traceback.print_exc()
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
