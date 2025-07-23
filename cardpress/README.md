# CardPress - Firebase Blog Management System

**Firebase-powered Blog Admin Interface + Static Site Generator**

---

## 🎯 Overview

**CardPress** is a modern blog management system that combines a beautiful web admin interface with automated static site generation. Write and organize your blog posts through a Kanban-style interface, then automatically deploy them to a Pelican-powered static blog.

### ✨ Features

- 🎨 **Beautiful Admin Interface** - Kanban board for blog post workflow
- 🔐 **Firebase Authentication** - Secure user management
- 📱 **Responsive Design** - Works on desktop and mobile
- 🖼️ **Image Upload** - Firebase Storage integration
- 🏷️ **Tags & Labels** - Organize your content
- 📝 **Markdown Support** - Rich text editing with Markdown
- 🚀 **Auto-Deploy** - Converts Firebase posts to Pelican static site
- 👥 **Multi-User** - Collaborative blog management

---

## 🏗️ Architecture

```
CardPress/
├── index.html              # 🎨 Admin web interface
├── firebase_to_pelican.py  # 🔄 Static site generator
├── firestore.rules         # 🔐 Database security rules
├── storage.rules           # 🔐 File storage security rules
├── deploy.sh               # 🚀 Automated deployment script
└── README.md              # 📖 This documentation
```

### Data Structure
```
/artifacts/{appId}/users/{userId}/posts/{postId}
```

### Workflow Columns
- **Ideas** - Initial post concepts
- **Drafting** - Posts being written
- **Editing** - Posts being reviewed/edited
- **Deployed** - Published posts (exported to static site)

---

## ⚡ Quick Start

**Get CardPress running in 5 minutes:**

1. **Clone and Setup**
   ```bash
   # Make sure you're in the project root
   cd your-project-directory
   
   # Copy environment file
   cp .env_example .env
   
   # Edit .env with your Firebase settings
   nano .env
   ```

2. **Firebase Setup**
   ```bash
   # Install Firebase CLI if not installed
   npm install -g firebase-tools
   
   # Login to Firebase
   firebase login
   
   # Initialize project (if not done)
   firebase init
   ```

3. **Deploy Everything**
   ```bash
   # Run the magic deployment script
   ./cardpress/deploy.sh
   
   # Or run step by step:
   cd cardpress
   ./deploy.sh 5  # Full setup option
   ```

4. **Access Admin Interface**
   ```
   Open: http://localhost:8000/cardpress/index.html
   ```

**That's it! 🎉 Start creating blog posts in your Kanban board!**

---

## 🛠️ Detailed Setup Instructions

### 1. Firebase Project Setup

1. **Create Firebase Project**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create new project: `your-project-name`
   - Enable Google Analytics (optional)

2. **Enable Firebase Services**
   ```bash
   # Authentication
   Authentication > Sign-in method > Email/Password: Enable
   
   # Firestore Database
   Firestore Database > Create database > Start in test mode
   
   # Storage
   Storage > Get started > Start in test mode
   ```

3. **Get Web App Configuration**
   - Project Settings > General > Your apps
   - Add app > Web app icon
   - Copy the `firebaseConfig` object

### 2. Configure Admin Interface

CardPress uses **automatic environment detection** with separate configs for development and production:

1. **Production Config**: Already configured in `index.html` (safe to commit)
2. **Development Config**: For localhost only (gitignored, not committed)

**Setup for Localhost Development:**
```bash
# Copy the development template
cp cardpress/firebase-config-dev.js.template cardpress/firebase-config-dev.js

# Edit with your LOCALHOST Firebase API key
nano cardpress/firebase-config-dev.js
```

**Get your Firebase API keys:**
1. Firebase Console → Project Settings → General → Your apps → Web app
2. **Important**: Create **two separate API keys** with proper restrictions

**🔐 API Key Security Setup:**

1. **Production Key** (for `index.html`):
   - Go to [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
   - Find your Firebase API key
   - Click "Edit" → **Application restrictions** → Select:
     ✅ **HTTP referrers (websites)**
   - Add your domain: `https://yourdomain.com/*`
   - Example: `https://lastmachine-web.web.app/*`

2. **Development Key** (for `firebase-config-dev.js`):
   - Create a **new API key** in Google Cloud Console
   - **Application restrictions** → Select:
     ✅ **HTTP referrers (websites)**
   - Add localhost patterns:
     - `http://localhost:*`
     - `http://127.0.0.1:*`
     - `http://localhost:8000/*`

```javascript
const FIREBASE_CONFIG_DEV = {
    apiKey: "your-localhost-api-key",  // ← Use localhost-restricted key
    authDomain: "your-project.firebaseapp.com", 
    projectId: "your-project-id",
    storageBucket: "your-project.firebasestorage.app",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abcdef123456"
};
```

⚠️ **Security Notes**: 
- `firebase-config-dev.js` is gitignored (localhost secrets)
- Production config in `index.html` can be committed (domain-restricted)
- System auto-detects localhost vs production
- **Never use unrestricted API keys** - always set domain restrictions

2. **Deploy Firebase Security Rules**
   ```bash
   # Deploy Firestore rules
   firebase deploy --only firestore:rules
   
   # Deploy Storage rules  
   firebase deploy --only storage
   ```

### 3. Configure Static Site Generator

1. **Install Dependencies**
   ```bash
   pip install -r ../requirements.txt
   ```

2. **Setup Service Account**
   - Firebase Console > Project Settings > Service accounts
   - Generate private key → Save as `serviceAccountKey.json` in project root

3. **Configure Environment Variables**
   ```bash
   cp ../.env_example ../.env
   ```
   
   Edit `.env`:
   ```env
   FIREBASE_SERVICE_ACCOUNT=serviceAccountKey.json
   FIREBASE_BUCKET_NAME=your-project.firebasestorage.app
   ```

---

## 🚀 Usage

### Admin Interface

1. **Open Admin Interface**
   ```bash
   # Serve locally
   python -m http.server 8000
   # Open http://localhost:8000/cardpress/index.html
   ```

2. **Create Account**
   - First time: Click "Register" 
   - Enter email/password
   - Start creating posts!

3. **Blog Post Workflow**
   ```
   Ideas → Drafting → Editing → Deployed
   ```
   - Drag cards between columns
   - Click cards to edit
   - Move to "Deployed" when ready to publish

### Static Site Generation

1. **Export Posts to Static Site**
   ```bash
   python cardpress/firebase_to_pelican.py
   ```

2. **What It Does**
   - ✅ Fetches all "Deployed" posts from Firebase
   - ✅ Downloads images to `blog/content/imgs/`
   - ✅ Converts to Pelican markdown format
   - ✅ Builds static site with Pelican
   - ✅ Deploys to Firebase Hosting

3. **Automated Deployment**
   ```bash
   # Add to crontab for automatic daily builds
   0 6 * * * cd /path/to/project && python cardpress/firebase_to_pelican.py
   ```

---

## 🔐 Security Configuration

### Firestore Rules (`firestore.rules`)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow any authenticated user to read and write all data
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### Storage Rules (`storage.rules`)

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow any authenticated user to read and write all files
    match /{allPaths=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

---

## 📁 File Structure

```
project/
├── cardpress/
│   ├── index.html              # 🎨 Admin interface
│   ├── firebase_to_pelican.py  # 🔄 Static site generator
│   ├── firestore.rules         # 🔐 Database rules
│   ├── storage.rules           # 🔐 Storage rules
│   ├── deploy.sh               # 🚀 Deployment script
│   └── README.md              # 📖 This documentation
├── blog/
│   ├── content/               # 📝 Generated markdown files
│   ├── output/               # 🌐 Generated static site
│   ├── pelicanconf.py        # ⚙️ Pelican configuration
│   └── theme/                # 🎨 Blog theme
├── worker/
│   └── refresh.js            # 🔄 Cloudflare Worker
├── firebase.json             # ⚙️ Firebase project configuration
├── serviceAccountKey.json     # 🔑 Firebase credentials
├── .env                      # 🔧 Environment variables
└── requirements.txt          # 📦 Python dependencies
```

---

## 🐛 Troubleshooting

### Common Issues

**"invalid-api-key" Error**
```bash
# For localhost development:
cp cardpress/firebase-config-dev.js.template cardpress/firebase-config-dev.js
# Then edit firebase-config-dev.js with your localhost Firebase config

# For production: Update the production config in index.html
```

**"Permission denied" Error**
```bash
# Fix: Deploy firestore.rules and storage.rules
firebase deploy --only firestore:rules,storage
```

**"Content directory not found"**
```bash
# Fix: Script now auto-creates directories and uses correct paths
python cardpress/firebase_to_pelican.py
```

**No posts exported**
```bash
# Fix: Make sure posts are in "Deployed" column in admin interface
```

### Debug Mode

```bash
# Run with verbose output
python -v cardpress/firebase_to_pelican.py
```

---

## 🤖 Deployment Script Usage

The `deploy.sh` script automates common CardPress tasks:

### Script Options

```bash
./cardpress/deploy.sh [option]

# Interactive menu (no option)
./cardpress/deploy.sh

# Direct options:
./cardpress/deploy.sh 1  # Deploy Firebase rules only
./cardpress/deploy.sh 2  # Run blog generator only  
./cardpress/deploy.sh 3  # Deploy rules + run generator
./cardpress/deploy.sh 4  # Start local admin server
./cardpress/deploy.sh 5  # Full setup (recommended)
```

### What Each Option Does

| Option | Description | Commands Run |
|--------|-------------|--------------|
| **1** | Deploy Rules | `firebase deploy --only firestore:rules,storage` |
| **2** | Generate Blog | `python firebase_to_pelican.py` |
| **3** | Rules + Blog | Option 1 + Option 2 |
| **4** | Local Server | `python -m http.server 8000` |
| **5** | Full Setup | Options 1, 2, and 4 combined |

### Prerequisites Check

The script automatically verifies:
- ✅ Firebase CLI is installed
- ✅ You're logged into Firebase
- ✅ Required files exist

### Example Usage

```bash
# First time setup
./cardpress/deploy.sh 5

# Daily blog updates
./cardpress/deploy.sh 3

# Just test the admin interface
./cardpress/deploy.sh 4
```

---

## 🔄 Manual Deployment Workflow

### Manual Deployment
```bash
# 1. Create posts in admin interface
# 2. Move posts to "Deployed" column  
# 3. Run generator
python cardpress/firebase_to_pelican.py
```

### Automated Deployment
```bash
# Setup webhook endpoint (optional)
# Trigger via HTTP call to rebuild blog
curl -X POST "https://your-worker.workers.dev/refresh?key=SECRET"
```

---

## 🎨 Customization

### Admin Interface
- Edit `index.html` to customize colors, layout
- Modify column names in JavaScript
- Add custom fields to post form

### Static Site
- Configure `blog/pelicanconf.py` for site settings
- Customize `blog/theme/` for blog appearance
- Modify `firebase_to_pelican.py` for custom export logic

---

## 📊 Analytics & Monitoring

### Firebase Analytics
```javascript
// Add to index.html for usage tracking
import { getAnalytics } from "firebase/analytics";
const analytics = getAnalytics(app);
```

### Performance Monitoring
```javascript
// Add to index.html for performance insights
import { getPerformance } from "firebase/performance";
const perf = getPerformance(app);
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---


**Happy Blogging! 🎉** 