# CardPress - Cloudflare Blog Management System

**Cloudflare-powered Blog Admin Interface + Static Site Generator**

---

## 🎯 Overview

**CardPress** is a modern blog management system that combines a beautiful admin interface with automated static site generation. Built on Cloudflare's edge infrastructure for maximum performance and security.

### ✨ Key Features

- 🔐 **Admin-Only Access** - Secure admin authentication, no public registration
- 🌐 **Cloudflare-Powered** - D1 database, R2 storage, Workers API
- 🎨 **Beautiful Admin Interface** - Kanban board for blog post workflow
- 📱 **Responsive Design** - Works on desktop and mobile
- 🖼️ **Image Management** - R2 storage with automatic optimization
- 🏷️ **Tags & Labels** - Organize your content
- 📝 **Markdown Support** - Rich text editing with Markdown
- 🚀 **Auto-Deploy** - Converts posts to Pelican static site
- ⚡ **Edge Performance** - Global CDN with sub-50ms response times

---

## 🏗️ Architecture

```
CardPress/
├── cardpress/
│   ├── index.html               # 🎨 Admin web interface
│   ├── cloudflare_to_pelican.py # 🔄 Static site generator
│   └── README.md               # 📖 Documentation
├── worker/
│   └── cardpress-api.js        # ⚡ Cloudflare Worker API
├── schema.sql                  # 🗄️ D1 database schema
├── wrangler.toml              # ⚙️ Cloudflare configuration
├── setup-cloudflare.sh       # 🚀 Automated setup script
└── .env                       # 🔧 Environment variables
```

### Data Flow
```
Admin Interface → Cloudflare Worker → D1 Database → Pelican → Static Site
                              ↓
                         R2 Storage (Images)
```

### Security Model
- ✅ **Admin-only authentication** - No public registration
- ✅ **JWT-based sessions** - Secure token authentication  
- ✅ **CORS protection** - Domain-restricted API access
- ✅ **Input validation** - All data sanitized and validated

---

## ⚡ Quick Start

**Get CardPress running in 5 minutes:**

### Prerequisites
```bash
# Install Node.js and Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Install Python dependencies
pip install -r requirements.txt
```

### 1. Automated Setup
```bash
# Run the magic setup script
chmod +x setup-cloudflare.sh
./setup-cloudflare.sh

# Choose option 1 for full setup
```

### 2. Manual Setup (Alternative)
```bash
# 1. Create Cloudflare resources
wrangler d1 create cardpress-blog
wrangler r2 bucket create cardpress-storage

# 2. Initialize database
wrangler d1 execute cardpress-blog --file=schema.sql

# 3. Deploy worker
wrangler deploy

# 4. Configure environment
cp .env_example .env
# Edit .env with your settings
```

### 3. Access Admin Interface
```bash
# Start local server
python -m http.server 8000

# Open admin interface
open http://localhost:8000/cardpress/index.html
```

**Default Login:**
- Email: `admin@example.com`
- Password: `admin123`

---

## 🛠️ Configuration

### Environment Variables (.env)
```bash
# Cloudflare Configuration
CLOUDFLARE_API_TOKEN=your_api_token
CLOUDFLARE_ACCOUNT_ID=your_account_id
D1_DATABASE_ID=your_database_id

# Worker Configuration  
WORKER_URL=https://your-worker.workers.dev

# Admin Authentication
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your_secure_password
```

### Cloudflare Resources Setup

#### 1. D1 Database
```bash
# Create database
wrangler d1 create cardpress-blog

# Initialize schema
wrangler d1 execute cardpress-blog --file=schema.sql

# View data (for debugging)
wrangler d1 execute cardpress-blog --command="SELECT * FROM posts"
```

#### 2. R2 Bucket
```bash
# Create bucket
wrangler r2 bucket create cardpress-storage

# List buckets
wrangler r2 bucket list
```

#### 3. Worker Deployment
```bash
# Deploy worker
wrangler deploy

# View logs
wrangler tail
```

---

## 🚀 Usage

### Admin Workflow

1. **Login to Admin Interface**
   - Navigate to `/cardpress/index.html`
   - Use admin credentials to login
   - Start managing your blog posts

2. **Content Creation Workflow**
   ```
   Ideas → Drafting → Editing → Deployed
   ```
   - **Ideas**: Initial post concepts and outlines
   - **Drafting**: Active writing and content creation
   - **Editing**: Review, polish, and finalize posts
   - **Deployed**: Published posts ready for static site

3. **Post Management**
   - ✍️ Create/edit posts with Markdown support
   - 🖼️ Upload and manage images
   - 🏷️ Add tags and categories
   - 🎨 Customize colors and styling
   - 🗑️ Delete posts (admin-only)

### Static Site Generation

```bash
# Generate static site from deployed posts
python cardpress/cloudflare_to_pelican.py

# What it does:
# 1. ✅ Fetches all "Deployed" posts from D1
# 2. ✅ Downloads images from R2 to local storage
# 3. ✅ Converts to Pelican markdown format
# 4. ✅ Builds static site with Pelican
# 5. ✅ Deploys to hosting platform
```

### API Endpoints

The Cloudflare Worker provides these admin-only endpoints:

```bash
# Authentication
POST /auth/login          # Admin login
POST /auth/verify         # Verify token

# Posts Management (Admin Only)
GET  /posts              # List all posts
POST /posts              # Create new post
PUT  /posts/{id}         # Update post
DELETE /posts/{id}       # Delete post

# Image Management (Admin Only)  
POST /images/upload      # Upload image to R2
GET  /images/{path}      # Serve image from R2
```

---

## 🔐 Admin-Only Security

### No Public Registration
- Only admins can access the system
- No user registration endpoint
- Admins must be added manually to the database

### Authentication Flow
1. Admin logs in with email/password
2. System verifies against D1 database (admin users only)
3. JWT token issued for session management
4. All API calls require valid admin token

### Adding New Admins
```sql
-- Connect to D1 database
wrangler d1 execute cardpress-blog --command="
INSERT INTO users (id, email, password_hash, is_admin) 
VALUES (
    'admin-002',
    'newadmin@example.com',
    '$2b$12$hashed_password_here',
    1
)"
```

---

## 🌐 Deployment Options

### Static Site Hosting

**Cloudflare Pages (Recommended)**
```bash
# Connect your GitHub repo to Cloudflare Pages
# Automatic deployments on blog updates
```

**Firebase Hosting**
```bash
# Configure firebase.json in project root
firebase deploy --only hosting
```

**Netlify**
```bash
# Deploy output directory
netlify deploy --dir=blog/output --prod
```

**GitHub Pages**
```bash
# Push blog/output to gh-pages branch
git subtree push --prefix blog/output origin gh-pages
```

---

## 📊 Performance & Monitoring

### Cloudflare Analytics
- ⚡ **Response Times**: Sub-50ms globally
- 🌍 **Edge Locations**: 200+ data centers
- 📈 **Request Volume**: Unlimited scalability
- 💰 **Cost Efficiency**: Pay-per-use pricing

### Monitoring Commands
```bash
# Worker logs
wrangler tail

# D1 database stats
wrangler d1 info cardpress-blog

# R2 bucket usage
wrangler r2 bucket list
```

---

## 🔧 Development

### Local Development
```bash
# Start local worker development
wrangler dev

# Run with remote D1/R2
wrangler dev --remote

# Local database for testing
wrangler d1 execute cardpress-blog --local --file=schema.sql
```

### Database Management
```bash
# View database schema
wrangler d1 execute cardpress-blog --command=".schema"

# Export data
wrangler d1 export cardpress-blog --output=backup.sql

# Import data  
wrangler d1 execute cardpress-blog --file=backup.sql
```

---

## 🚨 Troubleshooting

### Common Issues

**Authentication Errors**
```bash
# Check admin user exists
wrangler d1 execute cardpress-blog --command="SELECT * FROM users WHERE is_admin=1"

# Reset admin password
wrangler d1 execute cardpress-blog --command="UPDATE users SET password_hash='$2b$12$new_hash' WHERE email='admin@example.com'"
```

**Worker Deployment Issues**
```bash
# Check wrangler authentication
wrangler whoami

# Verify D1 database binding
wrangler d1 list

# Check R2 bucket access
wrangler r2 bucket list
```

**Image Upload Problems**
```bash
# Test R2 bucket permissions
wrangler r2 object put cardpress-storage/test.txt --file=README.md

# Check worker logs
wrangler tail --format=pretty
```

### Debug Mode
```bash
# Enable debug logging in worker
wrangler dev --compatibility-date=2024-04-27 --log-level=debug
```

---

## 🔄 Migration from Firebase

### Data Migration
```bash
# 1. Export Firebase data
python cardpress/firebase_to_pelican.py --export-only

# 2. Import to Cloudflare D1
python migration/firebase_to_d1.py

# 3. Transfer images to R2
python migration/firebase_to_r2.py
```

### Configuration Updates
```bash
# Update frontend API endpoints
# Replace Firebase SDK with fetch() calls to Worker API
# Update authentication flow
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

```bash
# Fork the repository
git clone https://github.com/your-username/cardpress.git

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
wrangler dev --local

# Submit pull request
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🆘 Support

- 📖 **Documentation**: [GitHub Wiki](https://github.com/your-repo/wiki)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📧 **Email**: support@cardpress.dev

---

**Built with ❤️ using Cloudflare's edge infrastructure**

