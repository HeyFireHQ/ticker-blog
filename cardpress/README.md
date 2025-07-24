# CardPress - Local Python Edition

A modern, local blog content management system built with Python, SQLite, and Flask. Create, manage, and deploy beautiful static blogs with an intuitive drag-and-drop interface.

## ✨ Features

- **🏠 Local Development** - Runs entirely on your computer with SQLite
- **🔐 Secure Authentication** - Encrypted user credentials with JWT tokens
- **📝 Kanban-Style Editor** - Drag and drop posts between Ideas → Drafting → Editing → Deployed
- **🖼️ Image Support** - Upload and manage images locally
- **📱 Responsive Design** - Beautiful admin interface that works on all devices
- **🚀 Static Site Generation** - Generate optimized static HTML for deployment
- **☁️ Cloudflare Pages** - One-click deployment to Cloudflare Pages
- **📄 Markdown Support** - Write content in Markdown with live preview
- **🏷️ Tags & Labels** - Organize content with flexible tagging system

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd cardpress
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python app.py
```

### 3. Access Admin Interface

Open your browser to: **http://localhost:8000**

**Default Login:**
- Email: `admin@cardpress.local`
- Password: `admin123`

### 4. Create Content

1. Click "➕ Add Post" to create new content
2. Drag posts between columns: Ideas → Drafting → Editing → Deployed
3. Upload images, add tags, and write in Markdown
4. Move finished posts to "Deployed" when ready to publish

### 5. Deploy Your Blog

1. Click "🚀 Deploy Site" in the admin interface
2. Run the deployment script: `python deploy_to_pages.py`
3. Your static blog will be generated in the `static_output/` folder

## 📁 Project Structure

```
cardpress/
├── app.py                 # Main Flask application
├── static_generator.py    # Static site generator
├── deploy_to_pages.py     # Cloudflare Pages deployment
├── admin.html            # Admin interface
├── requirements.txt      # Python dependencies
├── cardpress.db          # SQLite database (auto-created)
├── images/              # Uploaded images
├── static_output/       # Generated static site
└── templates/           # HTML templates (auto-created)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the cardpress directory:

```env
SECRET_KEY=your-secret-key-here
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=your-secure-password
```

### Customization

#### Change Admin Credentials

1. Edit the `init_database()` function in `app.py`
2. Or add a new user via the API:

```python
# In Python shell
from app import get_db
from werkzeug.security import generate_password_hash

conn = get_db()
cursor = conn.cursor()
cursor.execute('''
    INSERT INTO users (id, email, password_hash, role)
    VALUES (?, ?, ?, ?)
''', ('your-id', 'new@email.com', generate_password_hash('new-password'), 'admin'))
conn.commit()
```

#### Customize Templates

Edit templates in the `templates/` directory:
- `base.html` - Main layout
- `index.html` - Blog homepage
- `post.html` - Individual post page
- `rss.xml` - RSS feed

#### Modify Styles

Edit the CSS in `static_generator.py` or create custom CSS files.

## 🚀 Deployment Options

### Option 1: Cloudflare Pages (Recommended)

1. **Generate Static Site:**
   ```bash
   python deploy_to_pages.py
   ```

2. **Connect to Cloudflare Pages:**
   - Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
   - Pages → Create a project
   - Connect your Git repository
   - Set build settings:
     - Build command: `python deploy_to_pages.py`
     - Build output directory: `static_output`

### Option 2: Manual Upload

1. Generate static site: `python deploy_to_pages.py`
2. Upload contents of `static_output/` to any static hosting provider

### Option 3: Git-based Deployment

The deployment script can automatically create a `pages-deploy` branch with your static files.

## 🎨 Customizing Your Blog

### Blog Settings

Edit the templates in `static_generator.py`:

```python
# Change blog title and description
base_template = '''
<title>Your Blog Name</title>
<meta name="description" content="Your blog description">
'''
```

### Color Schemes

Modify the CSS variables in the generated styles:

```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    /* Add your colors */
}
```

### Post Statuses

Customize the Kanban columns by editing the `columns` array in `admin.html`:

```javascript
const columns = [
    { id: 'ideas', title: 'Ideas', color: '#3498db' },
    { id: 'writing', title: 'Writing', color: '#f39c12' },
    { id: 'review', title: 'Review', color: '#e74c3c' },
    { id: 'published', title: 'Published', color: '#27ae60' }
];
```

## 🔒 Security Features

- **Encrypted Passwords** - Using Werkzeug's secure password hashing
- **JWT Authentication** - Secure token-based authentication
- **CORS Protection** - Configurable cross-origin requests
- **File Upload Security** - Secure filename handling and validation
- **SQL Injection Protection** - Parameterized queries throughout

## 🐛 Troubleshooting

### Common Issues

**Database locked error:**
```bash
# Stop the server and restart
pkill -f "python app.py"
python app.py
```

**Images not showing:**
- Check that images are in the `images/` directory
- Verify file permissions
- Ensure Flask is serving static files correctly

**Deploy fails:**
- Make sure you have posts in "Deployed" status
- Check that all dependencies are installed
- Verify write permissions in the project directory

### Debug Mode

Enable Flask debug mode:

```python
# In app.py, change:
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 📚 API Reference

### Authentication

- `POST /auth/login` - Login with email/password
- `GET /auth/verify` - Verify JWT token

### Posts

- `GET /posts` - Get all posts
- `GET /posts/{id}` - Get specific post
- `POST /posts` - Create new post
- `PUT /posts/{id}` - Update post
- `DELETE /posts/{id}` - Delete post

### Images

- `POST /images/upload` - Upload image file
- `GET /images/{filename}` - Serve uploaded image

### Deployment

- `POST /deploy` - Generate static site

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs and request features on GitHub
- **Documentation**: Check this README and code comments
- **Community**: Join discussions in GitHub Discussions

---

**Made with ❤️ by the CardPress team**

*Transform your ideas into beautiful blogs with CardPress!*

