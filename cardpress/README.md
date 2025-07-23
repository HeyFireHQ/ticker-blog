# CardPress - Cloudflare Blog Management System

**Admin-Only Blog Management with GitHub Pages Integration**

---

## 🎯 Overview

**CardPress** is a modern blog management system that combines a beautiful admin interface with automated GitHub Pages deployment. Built on Cloudflare's edge infrastructure for maximum performance and security.

### ✨ Key Features

- 🔐 **Admin-Only Access** - Secure authentication, no public registration
- 🌐 **Cloudflare-Powered** - D1 database, R2 storage, Workers API
- 🎨 **Beautiful Admin Interface** - Kanban board for blog post workflow
- 📱 **Responsive Design** - Works perfectly on desktop and mobile
- 🖼️ **Image Management** - R2 storage with automatic optimization
- 🏷️ **Tags & Labels** - Organize your content efficiently
- 📝 **Markdown Support** - Rich text editing with Markdown
- 🚀 **GitHub Pages Deploy** - Generate pages and push to GitHub → triggers Cloudflare Pages
- 📂 **GitHub Integration** - Load posts from GitHub repository (live view)
- 👥 **User Management** - Add/remove admin users securely
- ⚡ **Edge Performance** - Global CDN with sub-50ms response times

---

## 🏗️ Architecture

```
CardPress/
├── index.html                  # 🎨 Admin web interface
├── cloudflare_to_pelican.py   # 🔄 Static site generator
├── worker/
│   └── cardpress-api.js        # ⚡ Cloudflare Worker API
├── schema.sql                  # 🗄️ D1 database schema
├── wrangler.toml              # ⚙️ Cloudflare configuration
├── setup-cloudflare.sh       # 🚀 Automated setup script
├── deploy.sh                  # 🚀 Multi-platform deployment script
├── deploy-webhook.js          # 📡 Webhook server for UI deploys
├── .env_example               # 🔧 Environment variables template
└── README.md                  # 📖 This documentation
```

### Data Flow
```
Draft Posts: Admin Interface → Cloudflare Worker → D1 Database
                                     ↓
Deploy: D1 → Generate Markdown → Push to GitHub → Cloudflare Pages Deploy
                                     ↓
Live View: Admin Interface ← Load from GitHub Repository (deployed posts)
                                     ↓
                             R2 Storage (Images)
```

### Security Model
- ✅ **Admin-only authentication** - No public registration allowed
- ✅ **JWT-based sessions** - Secure token authentication  
- ✅ **CORS protection** - Domain-restricted API access
- ✅ **Input validation** - All data sanitized and validated
- ✅ **User management** - Only admins can add/remove users
- ✅ **GitHub integration** - Personal access tokens for repo access

---

## ⚡ Quick Start

**Get CardPress running in 5 minutes:**

### Prerequisites
```bash
# Install Node.js and Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Install Python dependencies (in project root)
pip install -r requirements.txt
```

### 1. Automated Setup
```bash
# Run the setup script
chmod +x setup-cloudflare.sh
./setup-cloudflare.sh

# Choose option 1 for full setup
```

### 2. GitHub Configuration
```bash
# 1. Create GitHub repository for your blog
# 2. Generate Personal Access Token with 'repo' permissions
# 3. Set up environment variables
cp .env_example .env
# Edit .env with your GitHub settings
```

### 3. Deploy Infrastructure
```bash
# Deploy Cloudflare Worker and create resources
wrangler deploy
```

### 4. Access Admin Interface
```bash
# Start local server (or deploy to hosting)
python -m http.server 8000

# Open admin interface
open http://localhost:8000/index.html
```

**Default Login:**
- Email: `admin@example.com`
- Password: `admin123`

---

## 🚀 Usage

### Admin Interface Features

#### 📝 **Posts Management**
- **Kanban Board**: Drag-and-drop workflow (Ideas → Drafting → Editing → Deployed)
- **Rich Editor**: Create/edit posts with Markdown support
- **Image Upload**: Drag-and-drop images with R2 storage
- **Tags & Categories**: Organize content with labels
- **GitHub Deploy**: Generate pages and push to GitHub

#### 👥 **User Management** 
- **Admin Users Only**: No public registration allowed
- **Add/Remove Users**: Manage admin access securely
- **Password Management**: Secure bcrypt password hashing
- **Last Admin Protection**: Cannot delete the final admin user

### Content Creation Workflow

1. **Login to Admin Interface**
   - Navigate to `/index.html`
   - Use admin credentials to login

2. **Create & Manage Posts**
   ```
   Ideas → Drafting → Editing → Deployed
   ```
   - **Ideas**: Initial post concepts (saved to database)
   - **Drafting**: Active writing (saved to database)
   - **Editing**: Review and polish (saved to database)
   - **Deployed**: Ready for publication (shows from GitHub)

3. **Deploy Posts**
   - **Click "🚀 Generate & Push to GitHub"**
   - Posts generated as Pelican markdown
   - Pushed to GitHub branch
   - Triggers Cloudflare Pages build
   - Admin interface shows live posts from GitHub

### GitHub Integration Benefits

- ✅ **Live View** - Admin interface shows exactly what's deployed
- ✅ **Version Control** - All published content tracked in Git
- ✅ **Automatic Deploy** - GitHub push triggers Cloudflare Pages
- ✅ **Backup** - Posts safely stored in GitHub repository
- ✅ **Collaboration** - Team can work with Git workflow if needed

---

## 🛠️ Configuration

### Environment Variables (.env)
```bash
# Cloudflare Configuration
CLOUDFLARE_API_TOKEN=your_api_token
CLOUDFLARE_ACCOUNT_ID=your_account_id
D1_DATABASE_ID=your_database_id
R2_BUCKET_NAME=cardpress-storage

# Worker Configuration  
WORKER_URL=https://your-worker.workers.dev

# GitHub Configuration (Required for Pages deployment)
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_REPO=your-username/your-repo-name
GITHUB_DEPLOY_BRANCH=gh-pages

# Admin Authentication
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your_secure_password

# Optional: Webhook Configuration
DEPLOY_WEBHOOK_URL=http://your-server.com:3000/webhook/deploy
WEBHOOK_SECRET=your-webhook-secret
```

### GitHub Setup

#### 1. Create GitHub Repository
```bash
# Create new repository on GitHub
# Enable GitHub Pages in repository settings
# Set Pages source to deploy from branch (e.g., gh-pages)
```

#### 2. Generate Personal Access Token
```bash
# Go to GitHub Settings → Developer settings → Personal access tokens
# Generate token with 'repo' permissions
# Copy token to GITHUB_TOKEN in environment
```

#### 3. Configure Cloudflare Pages
```bash
# Connect Cloudflare Pages to your GitHub repository
# Set build command: pelican content -s publishconf.py
# Set build output directory: output
# Set root directory: / (or leave empty)
```

### Cloudflare Worker Secrets

Add sensitive configuration via Wrangler CLI:

```bash
# GitHub personal access token (Required)
wrangler secret put GITHUB_TOKEN

# Optional webhook configurations
wrangler secret put DEPLOY_WEBHOOK_URL
wrangler secret put REFRESH_SECRET_KEY
wrangler secret put DEPLOY_HOOK_URL
```

---

## 📈 Deployment Options

### Option 1: GitHub Pages Deploy (Recommended)
```bash
# 1. Move posts to "Deployed" column
# 2. Click "🚀 Generate & Push to GitHub" button  
# 3. Posts generated as Pelican markdown and pushed to GitHub
# 4. Cloudflare Pages automatically deploys from GitHub branch
# 5. Admin interface switches to show GitHub posts (live view)
```

### Option 2: Webhook-Triggered Deploy

Set up automatic deployment when UI deploy button is clicked:

```bash
# Start webhook server
node deploy-webhook.js 3000

# Configure webhook URL in Cloudflare Worker
wrangler secret put DEPLOY_WEBHOOK_URL
# Enter: http://your-server.com:3000/webhook/deploy
```

### Option 3: Command Line Deploy
```bash
# Interactive deployment menu
./deploy.sh

# Deploy to specific platform
./deploy.sh 4  # Cloudflare Pages (recommended)
```

---

## 🔧 Development

### Local Development
```bash
# Start local worker development
wrangler dev

# Run with remote D1/R2
wrangler dev --remote

# Start webhook server
node deploy-webhook.js 3000

# Local database for testing
wrangler d1 execute cardpress-blog --local --file=schema.sql
```

### Testing
```bash
# Test GitHub integration locally
# 1. Set up .env with GitHub credentials
# 2. Start worker: wrangler dev --remote
# 3. Test admin interface: python -m http.server 8000
```

---

## 🚨 Troubleshooting

### GitHub Integration Issues

**Deploy Button Not Working**
```bash
# Check GitHub configuration
wrangler secret list

# Test GitHub API access
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO

# Check worker logs
wrangler tail
```

**Posts Not Loading from GitHub**
```bash
# Verify repository exists and has content
# Check branch name in configuration
# Ensure GitHub token has 'repo' permissions
# Check browser console for API errors
```

### Authentication Issues
```bash
# Check admin user exists
wrangler d1 execute cardpress-blog --command="SELECT * FROM users WHERE is_admin=1"

# Reset admin password if needed
# Use setup script option 7
./setup-cloudflare.sh
```

### Performance Issues
```bash
# Check worker logs for errors
wrangler tail

# Monitor D1 database performance
wrangler d1 info cardpress-blog

# Check R2 storage usage
wrangler r2 bucket list
```

---

## 📊 API Reference

### Endpoints

```bash
# Authentication
POST /auth/login          # Admin login
POST /auth/verify         # Verify token

# Posts Management (Admin Only)
GET  /posts              # List posts (from GitHub if configured)
POST /posts              # Create new post (saved to database)
PUT  /posts/{id}         # Update post (saved to database)
DELETE /posts/{id}       # Delete post (from database)

# User Management (Admin Only)
GET  /users              # List admin users
POST /users              # Create admin user
PUT  /users/{id}         # Update user
DELETE /users/{id}       # Delete user

# Deployment (Admin Only)
POST /deploy             # Generate pages and push to GitHub

# Image Management (Admin Only)  
POST /images/upload      # Upload image to R2
GET  /images/{path}      # Serve image from R2
```

### Post Loading Logic
1. **First**: Try to load posts from GitHub repository
2. **Fallback**: If GitHub not configured, load from D1 database
3. **Admin View**: Shows live deployed posts from GitHub
4. **Editing**: Draft posts stored in database until deployed

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

```bash
# Fork the repository
git clone https://github.com/your-username/cardpress.git
cd cardpress

# Set up development environment
./setup-cloudflare.sh

# Make changes and test
wrangler dev --local

# Test deployment
./deploy.sh 6  # Generate only

# Submit pull request
```

---

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

---

## 🆘 Support

- 📖 **Documentation**: This README and inline code comments
- 🐛 **Bug Reports**: Create GitHub issues with detailed reproduction steps
- 💬 **Discussions**: Use GitHub Discussions for feature requests
- 📧 **Email**: Contact repository maintainers for security issues

---

**Built with ❤️ using Cloudflare's edge infrastructure and GitHub Pages**

