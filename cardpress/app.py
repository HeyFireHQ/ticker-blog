#!/usr/bin/env python3
"""
CardPress - Local Python Backend
A modern blog content management system with SQLite storage
"""

import os
import sqlite3
import json
import uuid
import hashlib
import secrets
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import base64
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import jwt

# Configuration
BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "cardpress.db"
IMAGES_DIR = BASE_DIR / "images"
STATIC_OUTPUT_DIR = BASE_DIR / "static_output"
BLOG_CONTENT_DIR = BASE_DIR.parent / "blog" / "content"
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Ensure directories exist
IMAGES_DIR.mkdir(exist_ok=True)
STATIC_OUTPUT_DIR.mkdir(exist_ok=True)

# Flask App Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Enable CORS for local development
CORS(app)

# Database Setup
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Users table with encrypted authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            labels TEXT DEFAULT '[]',
            colors TEXT DEFAULT '',
            status TEXT DEFAULT 'ideas',
            image_url TEXT DEFAULT '',
            image_path TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create default admin user if none exists
    cursor.execute('SELECT COUNT(*) as count FROM users')
    if cursor.fetchone()['count'] == 0:
        admin_id = str(uuid.uuid4())
        password_hash = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO users (id, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (admin_id, 'admin@cardpress.local', password_hash, 'admin'))
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_jwt_token(user_id, email, role):
    """Generate JWT token for authentication"""
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token):
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_jwt_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.user = user_data
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

# API Routes

@app.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = generate_jwt_token(user['id'], user['email'], user['role'])
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'role': user['role']
        }
    })

@app.route('/auth/verify', methods=['GET'])
@require_auth
def verify_token():
    """Verify current token"""
    return jsonify({
        'user': {
            'id': request.user['user_id'],
            'email': request.user['email'],
            'role': request.user['role']
        }
    })

@app.route('/posts', methods=['GET'])
@require_auth
def get_posts():
    """Get all posts"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM posts 
        ORDER BY updated_at DESC
    ''')
    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(posts)

@app.route('/posts/<post_id>', methods=['GET'])
@require_auth
def get_post(post_id):
    """Get specific post"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()
    conn.close()
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    return jsonify(dict(post))

@app.route('/posts', methods=['POST'])
@require_auth
def create_post():
    """Create new post"""
    data = request.get_json()
    
    post_id = str(uuid.uuid4())
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO posts (id, user_id, title, content, labels, colors, status, image_url, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        post_id,
        request.user['user_id'],
        data.get('title', ''),
        data.get('content', ''),
        json.dumps(data.get('labels', [])),
        data.get('colors', ''),
        data.get('column', 'ideas'),
        data.get('imageUrl', ''),
        data.get('imagePath', '')
    ))
    
    conn.commit()
    
    # Get the created post
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = dict(cursor.fetchone())
    conn.close()
    
    return jsonify(post), 201

@app.route('/posts/<post_id>', methods=['PUT'])
@require_auth
def update_post(post_id):
    """Update existing post"""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE posts 
        SET title = ?, content = ?, labels = ?, colors = ?, status = ?, 
            image_url = ?, image_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    ''', (
        data.get('title', ''),
        data.get('content', ''),
        json.dumps(data.get('labels', [])),
        data.get('colors', ''),
        data.get('column', 'ideas'),
        data.get('imageUrl', ''),
        data.get('imagePath', ''),
        post_id,
        request.user['user_id']
    ))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Post not found or unauthorized'}), 404
    
    conn.commit()
    
    # Get the updated post
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = dict(cursor.fetchone())
    conn.close()
    
    return jsonify(post)

@app.route('/posts/<post_id>', methods=['DELETE'])
@require_auth
def delete_post(post_id):
    """Delete post"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM posts WHERE id = ? AND user_id = ?', 
                   (post_id, request.user['user_id']))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Post not found or unauthorized'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Post deleted'})

@app.route('/images/upload', methods=['POST'])
@require_auth
def upload_image():
    """Upload image file"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Secure filename and add timestamp
    filename = secure_filename(file.filename)
    timestamp = int(datetime.now().timestamp())
    filename = f"{timestamp}_{filename}"
    
    # Save file
    file_path = IMAGES_DIR / filename
    file.save(file_path)
    
    # Return URL for local access
    image_url = f"/images/{filename}"
    
    return jsonify({
        'url': image_url,
        'path': filename
    })

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve uploaded images"""
    return send_from_directory(IMAGES_DIR, filename)

# Static file serving for the admin interface
@app.route('/')
def serve_admin():
    """Serve the admin interface"""
    return send_file('admin.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

# Deployment and static generation routes
def slugify(value):
    """Convert title to URL-friendly slug"""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

def write_markdown(post, blog_dir):
    """Convert post data to Pelican markdown file"""
    title = post.get("title", f"Untitled-{post.get('id', 'unknown')}")
    content = post.get("content", "")
    labels = json.loads(post.get("labels", "[]"))
    image_url = post.get("image_url", "")
    image_path = post.get("image_path", "")
    
    # Handle date conversion
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if post.get("updated_at"):
        try:
            # Try to parse the date string from SQLite
            date_obj = datetime.fromisoformat(post["updated_at"])
            date_str = date_obj.strftime("%Y-%m-%d")
        except:
            pass
    
    slug = slugify(title)
    
    # Handle image markdown
    image_markdown = ""
    if image_url and image_url.startswith('/images/'):
        # Convert local image URL to Pelican path
        image_name = image_url.replace('/images/', '')
        image_markdown = f"![{title}](/imgs/{image_name})\n\n"
    
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
    if image_markdown:
        image_name = image_url.replace('/images/', '') if image_url else ''
        if image_name:
            md_metadata.append(f"Image: /imgs/{image_name}")
    
    # Filter out empty metadata lines
    md_metadata = [line for line in md_metadata if line.strip() and not line.endswith(": ")]
    
    # Write the markdown file
    body = "\n".join(md_metadata) + "\n\n" + image_markdown + content
    
    # Write directly to blog/content directory
    content_dir = Path(blog_dir) / "content"
    file_path = content_dir / f"{slug}.md"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(body)
    
    return file_path

@app.route('/deploy', methods=['POST'])
@require_auth
def deploy_to_pages():
    """Generate markdown files from SQLite database"""
    try:
        # Ensure blog content directory exists
        BLOG_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create images directory in blog/content
        blog_imgs_dir = BLOG_CONTENT_DIR / "imgs"
        blog_imgs_dir.mkdir(exist_ok=True)
        
        # Get deployed posts from database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM posts 
            WHERE status = 'deployed' 
            ORDER BY updated_at DESC
        ''')
        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not posts:
            return jsonify({
                'error': 'No deployed posts found',
                'message': 'Move some posts to "Deployed" status first'
            }), 400
        
        # Convert posts to markdown
        generated_files = []
        for post in posts:
            file_path = write_markdown(post, BLOG_CONTENT_DIR.parent)
            generated_files.append(str(file_path))
            
            # Copy image if it exists locally
            if post.get('image_url') and post['image_url'].startswith('/images/'):
                image_name = post['image_url'].replace('/images/', '')
                source_image = IMAGES_DIR / image_name
                if source_image.exists():
                    dest_image = blog_imgs_dir / image_name
                    shutil.copy2(source_image, dest_image)
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(posts)} markdown posts to blog/content',
            'output_dir': str(BLOG_CONTENT_DIR),
            'posts_count': len(posts),
            'files': generated_files
        })
    
    except Exception as e:
        app.logger.error(f"Deploy error: {e}")
        return jsonify({
            'error': 'Deployment failed',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    print("🚀 CardPress Local Server Starting...")
    print(f"📁 Database: {DATABASE_PATH}")
    print(f"🖼️  Images: {IMAGES_DIR}")
    print(f"🌐 Admin Interface: http://localhost:8000")
    print(f"👤 Default Login: admin@cardpress.local / admin123")
    
    # Run Flask development server
    app.run(debug=True, host='0.0.0.0', port=8000) 