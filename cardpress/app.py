#!/usr/bin/env python3
"""
TinaCMS Clone - GitHub-based Content Management System
A modern CMS that works directly with GitHub repositories
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import secrets

from flask import Flask, request, jsonify, send_file, redirect, url_for, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
import jwt

# Local imports
from github_service import GitHubService
from template_system import TemplateSystem
from oauth_service import GitHubOAuthService

# Configuration
BASE_DIR = Path(__file__).parent
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:8000/auth/callback')

# Flask App Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Session configuration for OAuth
app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP for localhost
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Enable CORS for local development
CORS(app, supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
oauth_service = None
template_system = TemplateSystem(config_path=BASE_DIR / "templates.yml")

# Initialize OAuth service if credentials are provided
if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
    oauth_service = GitHubOAuthService(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI)
else:
    logger.warning("GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables.")

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        # Check for session-based auth first
        if 'github_token' in session and 'user_info' in session:
            request.github_token = session['github_token']
            request.user_info = session['user_info']
            return f(*args, **kwargs)
        
        # Check for Bearer token auth
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                # Verify JWT token that contains GitHub info
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                request.github_token = payload['github_token']
                request.user_info = payload['user_info']
                return f(*args, **kwargs)
            except jwt.InvalidTokenError:
                pass
        
        return jsonify({'error': 'Authentication required'}), 401
    
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_github_service(token: str = None, repo: str = None) -> GitHubService:
    """Get GitHub service instance"""
    if not token:
        token = getattr(request, 'github_token', None)
    if not token:
        raise ValueError("GitHub token required")
    
    return GitHubService(token, repo)

# Authentication Routes

@app.route('/auth/login')
def login():
    """Initiate GitHub OAuth login"""
    if not oauth_service:
        return jsonify({'error': 'OAuth not configured'}), 500
    
    # Store repository info in session if provided
    repo = request.args.get('repo')
    if repo:
        session['target_repo'] = repo
    
    auth_url, state = oauth_service.get_authorization_url()
    session['oauth_state'] = state
    
    return redirect(auth_url)

@app.route('/auth/callback')
def oauth_callback():
    """Handle GitHub OAuth callback"""
    if not oauth_service:
        return jsonify({'error': 'OAuth not configured'}), 500
    
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    # Debug logging
    logger.info(f"OAuth callback - code: {'present' if code else 'missing'}, state: {'present' if state else 'missing'}, error: {error}")
    logger.info(f"Session oauth_state: {'present' if session.get('oauth_state') else 'missing'}")
    
    if error:
        logger.error(f"GitHub OAuth error: {error}")
        return jsonify({'error': f'OAuth error: {error}'}), 400
    
    if not code or not state:
        logger.error("Missing code or state parameter in OAuth callback")
        return jsonify({'error': 'Missing code or state parameter'}), 400
    
    # Verify state matches
    session_state = session.get('oauth_state')
    if state != session_state:
        logger.error(f"State mismatch - received: {state}, expected: {session_state}")
        return jsonify({'error': 'Invalid state parameter'}), 400
    
    try:
        # Exchange code for token
        token_data = oauth_service.exchange_code_for_token(code, state)
        access_token = token_data['access_token']
        
        # Get user info
        user_info = oauth_service.get_user_info(access_token)
        
        # Store in session
        session['github_token'] = access_token
        session['user_info'] = user_info
        
        # Generate JWT for API access
        jwt_payload = {
            'github_token': access_token,
            'user_info': user_info,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        jwt_token = jwt.encode(jwt_payload, SECRET_KEY, algorithm='HS256')
        
        # Redirect to admin interface
        return redirect(f'/?token={jwt_token}')
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/auth/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/')

@app.route('/api/auth/verify')
@require_auth
def verify_auth():
    """Verify current authentication"""
    return jsonify({
        'authenticated': True,
        'user': request.user_info
    })

# Repository Management Routes

@app.route('/api/repositories')
@require_auth
def get_repositories():
    """Get user's accessible repositories"""
    try:
        github_service = get_github_service()
        repos = github_service.get_user_repos()
        return jsonify(repos)
    except Exception as e:
        logger.error(f"Failed to get repositories: {e}")
        return jsonify({'error': 'Failed to fetch repositories'}), 500

@app.route('/api/repositories/<path:repo>/select', methods=['POST'])
@require_auth
def select_repository(repo):
    """Select a repository to work with"""
    try:
        github_service = get_github_service()
        github_service.set_repository(repo)
        
        # Store selected repo in session
        session['selected_repo'] = repo
        
        return jsonify({
            'success': True,
            'repository': repo
        })
    except Exception as e:
        logger.error(f"Failed to select repository: {e}")
        return jsonify({'error': 'Failed to select repository'}), 500

# Template Management Routes

@app.route('/api/templates')
def get_templates():
    """Get available content templates"""
    templates = template_system.get_all_templates()
    return jsonify({
        template_name: {
            'name': template.name,
            'label': template.label,
            'description': template.description,
            'fields': [field.dict() for field in template.fields],
            'path': template.path,
            'format': template.format
        }
        for template_name, template in templates.items()
    })

@app.route('/api/templates/<template_name>')
def get_template(template_name):
    """Get specific template definition"""
    template = template_system.get_template(template_name)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    return jsonify({
        'name': template.name,
        'label': template.label,
        'description': template.description,
        'fields': [field.dict() for field in template.fields],
        'path': template.path,
        'format': template.format
    })

# Content Management Routes

@app.route('/api/content')
@require_auth
def list_content():
    """List content files from repository"""
    repo = session.get('selected_repo')
    if not repo:
        return jsonify({'error': 'No repository selected'}), 400
    
    try:
        logger.info(f"Listing content for repo: {repo}")
        
        # Get GitHub token from request
        github_token = getattr(request, 'github_token', None)
        logger.info(f"GitHub token present: {'yes' if github_token else 'no'}")
        
        github_service = get_github_service(repo=repo)
        logger.info(f"GitHub service created successfully")
        
        # Get directory parameter (default to root)
        directory = request.args.get('dir', '')
        branch = request.args.get('branch')
        logger.info(f"Directory: '{directory}', Branch: {branch}")
        
        items = github_service.list_directory(directory, branch)
        logger.info(f"Found {len(items)} items")
        return jsonify(items)
        
    except Exception as e:
        logger.error(f"Failed to list content: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to list content'}), 500

@app.route('/api/content/<path:file_path>')
@require_auth
def get_content(file_path):
    """Get content file"""
    repo = session.get('selected_repo')
    if not repo:
        return jsonify({'error': 'No repository selected'}), 400
    
    try:
        github_service = get_github_service(repo=repo)
        branch = request.args.get('branch')
        
        content, sha = github_service.get_file_content(file_path, branch)
        
        if content is None:
            return jsonify({'error': 'File not found'}), 404
        
        # Try to parse with template system
        template_name = request.args.get('template')
        if template_name:
            try:
                parsed_content = template_system.parse_file_content(template_name, content)
                return jsonify({
                    'path': file_path,
                    'content': content,
                    'parsed_content': parsed_content,
                    'sha': sha,
                    'template': template_name
                })
            except Exception as e:
                logger.warning(f"Failed to parse content with template: {e}")
        
        return jsonify({
            'path': file_path,
            'content': content,
            'sha': sha
        })
        
    except Exception as e:
        logger.error(f"Failed to get content: {e}")
        return jsonify({'error': 'Failed to get content'}), 500

@app.route('/api/content/<path:file_path>', methods=['PUT'])
@require_auth
def update_content(file_path):
    """Update content file"""
    repo = session.get('selected_repo')
    if not repo:
        return jsonify({'error': 'No repository selected'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        github_service = get_github_service(repo=repo)
        
        # Handle both raw content and template-based content
        if 'template' in data and 'content_data' in data:
            # Template-based content
            template_name = data['template']
            content_data = data['content_data']
            
            # Validate content
            is_valid, errors = template_system.validate_content(template_name, content_data)
            if not is_valid:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            
            # Format content for file
            content = template_system.format_content_for_file(template_name, content_data)
        else:
            # Raw content
            content = data.get('content', '')
        
        message = data.get('message', f'Update {file_path}')
        sha = data.get('sha')
        branch = data.get('branch')
        
        result = github_service.create_or_update_file(file_path, content, message, sha, branch)
        
        return jsonify({
            'success': True,
            'commit_sha': result['commit_sha'],
            'content_sha': result['content_sha']
        })
        
    except Exception as e:
        logger.error(f"Failed to update content: {e}")
        return jsonify({'error': 'Failed to update content'}), 500

@app.route('/api/content', methods=['POST'])
@require_auth
def create_content():
    """Create new content file"""
    repo = session.get('selected_repo')
    if not repo:
        return jsonify({'error': 'No repository selected'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        github_service = get_github_service(repo=repo)
        
        if 'template' in data:
            # Template-based content creation
            template_name = data['template']
            content_data = data.get('content_data', {})
            
            # Validate content
            is_valid, errors = template_system.validate_content(template_name, content_data)
            if not is_valid:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            
            # Generate file path
            file_path = template_system.generate_file_path(template_name, content_data)
            
            # Format content for file
            content = template_system.format_content_for_file(template_name, content_data)
        else:
            # Manual file creation
            file_path = data.get('path')
            content = data.get('content', '')
            
            if not file_path:
                return jsonify({'error': 'File path required'}), 400
        
        message = data.get('message', f'Create {file_path}')
        branch = data.get('branch')
        
        result = github_service.create_or_update_file(file_path, content, message, None, branch)
        
        return jsonify({
            'success': True,
            'path': file_path,
            'commit_sha': result['commit_sha'],
            'content_sha': result['content_sha']
        })
        
    except Exception as e:
        logger.error(f"Failed to create content: {e}")
        return jsonify({'error': 'Failed to create content'}), 500

@app.route('/api/content/<path:file_path>', methods=['DELETE'])
@require_auth
def delete_content(file_path):
    """Delete content file"""
    repo = session.get('selected_repo')
    if not repo:
        return jsonify({'error': 'No repository selected'}), 400
    
    data = request.get_json() or {}
    
    try:
        github_service = get_github_service(repo=repo)
        
        # Get current file to get SHA
        current_content, sha = github_service.get_file_content(file_path)
        if not sha:
            return jsonify({'error': 'File not found'}), 404
        
        message = data.get('message', f'Delete {file_path}')
        branch = data.get('branch')
        
        result = github_service.delete_file(file_path, message, sha, branch)
        
        return jsonify({
            'success': True,
            'commit_sha': result['commit_sha']
        })
        
    except Exception as e:
        logger.error(f"Failed to delete content: {e}")
        return jsonify({'error': 'Failed to delete content'}), 500

# Image Management Routes

@app.route('/api/images/upload', methods=['POST'])
@require_auth
def upload_image():
    """Upload image to repository"""
    repo = session.get('selected_repo')
    if not repo:
        return jsonify({'error': 'No repository selected'}), 400
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        github_service = get_github_service(repo=repo)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        timestamp = int(datetime.now().timestamp())
        filename = f"images/{timestamp}_{filename}"
        
        # Read file data
        image_data = file.read()
        
        # Get additional parameters
        message = request.form.get('message', f'Upload image: {file.filename}')
        branch = request.form.get('branch')
        
        result = github_service.upload_image(image_data, filename, message, branch)
        
        return jsonify({
            'success': True,
            'path': result['path'],
            'url': result['raw_url'],
            'commit_sha': result['commit_sha']
        })
        
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        return jsonify({'error': 'Failed to upload image'}), 500

# Branch Management Routes

@app.route('/api/branches')
@require_auth
def get_branches():
    """Get repository branches"""
    repo = session.get('selected_repo')
    if not repo:
        return jsonify({'error': 'No repository selected'}), 400
    
    try:
        github_service = get_github_service(repo=repo)
        branches = github_service.get_branches()
        return jsonify(branches)
        
    except Exception as e:
        logger.error(f"Failed to get branches: {e}")
        return jsonify({'error': 'Failed to get branches'}), 500

@app.route('/api/branches', methods=['POST'])
@require_auth
def create_branch():
    """Create new branch"""
    repo = session.get('selected_repo')
    if not repo:
        return jsonify({'error': 'No repository selected'}), 400
    
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Branch name required'}), 400
    
    try:
        github_service = get_github_service(repo=repo)
        
        branch_name = data['name']
        source_branch = data.get('source_branch')
        
        result = github_service.create_branch(branch_name, source_branch)
        
        return jsonify({
            'success': True,
            'branch': result
        })
        
    except Exception as e:
        logger.error(f"Failed to create branch: {e}")
        return jsonify({'error': 'Failed to create branch'}), 500

# Static file serving
@app.route('/')
def serve_admin():
    """Serve the admin interface"""
    return send_file('admin.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    try:
        return send_file(filename)
    except:
        return send_file('admin.html')  # SPA fallback

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 TinaCMS Clone Starting...")
    print(f"🌐 Admin Interface: http://localhost:8000")
    print(f"🔐 GitHub OAuth: {'Configured' if oauth_service else 'Not Configured'}")
    print(f"📝 Templates: {len(template_system.get_all_templates())} available")
    
    # Create default templates file if it doesn't exist
    if not (BASE_DIR / "templates.yml").exists():
        template_system.save_templates()
        print(f"📄 Created default templates.yml")
    
    # Run Flask development server
    app.run(debug=True, host='0.0.0.0', port=8000) 