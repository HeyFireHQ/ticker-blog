# CardPress - Local Blog Management System

A modern, local blog content management system built with Python, SQLite, and Flask. Create, manage, and deploy beautiful static blogs with an intuitive drag-and-drop Kanban interface.

## ✨ Features

- **🏠 Local Development** - Runs entirely on your computer with SQLite
- **🔐 Secure Authentication** - Encrypted user credentials with JWT tokens  
- **📝 Kanban Interface** - Drag and drop posts between Ideas → Drafting → Editing → Deployed
- **🖼️ Image Management** - Upload and manage images locally
- **📱 Responsive Design** - Beautiful admin interface that works on all devices
- **📄 Markdown Export** - Generates Pelican-ready markdown files
- **🚀 Simple Deployment** - Export directly to your blog's content directory
- **🏷️ Tags & Labels** - Organize content with flexible tagging system

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git (optional, for version control)

### Installation

1. **Clone Repository**
   ```bash
   git clone <your-repo-url>
   cd ticker-blog
   ```

2. **Setup CardPress**
   ```bash
   cd cardpress
   python setup.py
   ```
   *This will create a virtual environment and install dependencies*

3. **Start Server**
   ```bash
   python app.py
   ```

4. **Access Admin Interface**
   - Open: http://localhost:8000
   - Login: `admin@cardpress.local` / `admin123`

## 📝 Usage

### Content Management Workflow

1. **Create Posts**: Click "➕ Add Post" to create new content
2. **Kanban Board**: Drag posts between columns:
   - **Ideas** - Initial concepts
   - **Drafting** - Active writing
   - **Editing** - Review and polish  
   - **Deployed** - Ready for publication

3. **Rich Content**: 
   - Write in Markdown
   - Upload images
   - Add tags and labels
   - Set custom colors

4. **Deploy**: Click "🚀 Deploy Site" to generate markdown files

### Blog Integration

CardPress integrates seamlessly with your existing Pelican blog:

- **Markdown files** → Generated in `blog/content/`
- **Images** → Copied to `blog/content/imgs/`
- **Ready to build** → Run `pelican content` from blog directory

## 📁 Project Structure

```
ticker-blog/
├── cardpress/                # CardPress admin system
│   ├── app.py                # Flask application
│   ├── admin.html            # Admin interface
│   ├── requirements.txt      # Python dependencies
│   ├── cardpress.db          # SQLite database (auto-created)
│   └── images/              # Uploaded images
│
├── blog/                     # Your Pelican blog
│   ├── content/             # Generated markdown files
│   ├── pelicanconf.py       # Pelican configuration  
│   └── theme/               # Blog theme
│
└── README.md                # This file
```

## 🔧 Configuration

### Admin Credentials

Default login: `admin@cardpress.local` / `admin123`

To change, edit the `.env` file in cardpress directory:
```env
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=your-secure-password
```

### Blog Settings

Edit `blog/pelicanconf.py` to customize your blog:
- Site name and URL
- Author information  
- Theme settings
- Static file paths

## 🚀 Deployment

### Local Development
1. Generate content: Click "🚀 Deploy Site" in admin
2. Build blog: `cd blog && pelican content`
3. Serve locally: `pelican --listen`

### Production Deployment

**Option 1: Cloudflare Pages**
1. Push your repository to GitHub/GitLab
2. Connect to Cloudflare Pages
3. Set build command: `cd blog && pelican content`
4. Set publish directory: `blog/output`

**Option 2: Other Static Hosts**
1. Build: `cd blog && pelican content` 
2. Upload `blog/output/` to your hosting provider

## 🛠️ Development

### Adding Features

The CardPress system is built with:
- **Backend**: Flask + SQLite
- **Frontend**: Vanilla JavaScript + CSS
- **Authentication**: JWT tokens
- **File handling**: Python pathlib

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL, 
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'admin'
);

-- Posts table  
CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    labels TEXT DEFAULT '[]',
    status TEXT DEFAULT 'ideas',
    image_url TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔒 Security

- **Password Hashing**: Werkzeug secure password hashing
- **JWT Authentication**: Secure token-based sessions
- **File Upload Security**: Secure filename handling
- **SQL Injection Protection**: Parameterized queries
- **Local Storage**: No external dependencies or API keys

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r cardpress/requirements.txt
```

**Can't login:**
- Check credentials: `admin@cardpress.local` / `admin123`
- Reset database: Delete `cardpress/cardpress.db` and restart

**Images not showing:**
- Verify images are in `cardpress/images/`
- Check file permissions
- Ensure deployment copied images to `blog/content/imgs/`

### Debug Mode

Enable Flask debugging in `cardpress/app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8000)
```

## 📚 API Reference

CardPress provides a REST API for all operations:

### Authentication
- `POST /auth/login` - Login with email/password
- `GET /auth/verify` - Verify JWT token

### Posts Management  
- `GET /posts` - List all posts
- `POST /posts` - Create new post
- `PUT /posts/{id}` - Update post
- `DELETE /posts/{id}` - Delete post

### File Upload
- `POST /images/upload` - Upload image file
- `GET /images/{filename}` - Serve image

### Deployment
- `POST /deploy` - Generate markdown files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs on GitHub Issues
- **Documentation**: See this README and code comments
- **Security**: Email maintainers for security issues

---

**Transform your ideas into beautiful blogs with CardPress! 🎉**

Built with ❤️ for bloggers who want simplicity without sacrificing power. 