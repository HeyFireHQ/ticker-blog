# TinaCMS Clone - GitHub-based Content Management System

A modern, GitHub-integrated content management system that allows you to create, edit, and manage content directly in your GitHub repositories with a beautiful web interface.

## ✨ Features

- **🔐 GitHub OAuth Authentication** - Secure login with your GitHub account
- **📁 Direct GitHub Integration** - Edit files directly in your repositories
- **📝 Template System** - Pre-defined content types with field validation
- **🖼️ Image Management** - Upload images directly to GitHub
- **🌿 Branch Management** - Create and switch between branches
- **📱 Responsive Design** - Beautiful admin interface that works on all devices
- **🚀 Easy Deployment** - Docker support for simple deployment
- **⚡ Live Preview** - Real-time content editing experience

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- GitHub account
- GitHub OAuth App (for authentication)

### 1. Setup GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/applications/new)
2. Create a new OAuth App with:
   - **Application name**: TinaCMS Clone
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/auth/callback`
3. Note down your **Client ID** and **Client Secret**

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd ticker-blog/cardpress

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your GitHub OAuth credentials
```

### 3. Configuration

Edit `.env` file:

```env
SECRET_KEY=your-secret-key-here-use-a-long-random-string
GITHUB_CLIENT_ID=your-github-oauth-client-id
GITHUB_CLIENT_SECRET=your-github-oauth-client-secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/callback
```

### 4. Start the Server

```bash
python app.py
```

### 5. Access the Interface

Open your browser to: **http://localhost:8000**

## 📖 Usage

### 1. Authentication

- Click "Login with GitHub" to authenticate
- Grant repository access when prompted
- You'll be redirected back to the admin interface

### 2. Select Repository

- Choose a GitHub repository from the dropdown
- The system will load your repository structure

### 3. Content Management

#### Templates

The system comes with pre-configured templates:

- **Blog Post** - Standard blog posts with title, content, tags, etc.
- **Page** - Static pages
- **Documentation** - Docs with categories and ordering

#### Creating Content

1. Click "New Content"
2. Select a template
3. Fill in the required fields  
4. Click "Save" to commit to GitHub

#### Editing Content

1. Browse existing content files
2. Click on any file to edit
3. Make changes and save to commit

### 4. Image Management

- Upload images directly to your repository
- Images are stored in the `images/` folder
- Get GitHub raw URLs for use in content

### 5. Branch Management

- Create new branches for feature development
- Switch between branches
- All changes are committed to the selected branch

## 🎨 Templates

Templates define content structure with typed fields:

### Field Types

- **text** - Single line text input
- **textarea** - Multi-line text input  
- **rich-text** - Markdown content area
- **image** - Image URL/path
- **date** - Date picker
- **select** - Dropdown selection
- **boolean** - Checkbox
- **number** - Numeric input

### Custom Templates

Edit `templates.yml` to create custom content types:

```yaml
templates:
  - name: product
    label: Product
    description: Product information
    path: products/{slug}.md
    format: markdown
    fields:
      - name: title
        type: text  
        label: Product Name
        required: true
      - name: price
        type: number
        label: Price
        required: true
      - name: description
        type: rich-text
        label: Description
        required: true
```

## 🚀 Deployment

### Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t tinacms-clone .
docker run -p 8000:8000 --env-file .env tinacms-clone
```

### Production Environment Variables

```env
SECRET_KEY=your-production-secret-key
GITHUB_CLIENT_ID=your-github-oauth-client-id
GITHUB_CLIENT_SECRET=your-github-oauth-client-secret
GITHUB_REDIRECT_URI=https://your-domain.com/auth/callback
FLASK_ENV=production
```

### Platform Deployment

#### Vercel

1. Connect your GitHub repository
2. Set environment variables in Vercel dashboard
3. Deploy automatically on git push

#### Railway

1. Connect repository to Railway
2. Set environment variables
3. Deploy with automatic HTTPS

#### Heroku

```bash
# Install Heroku CLI
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
heroku config:set GITHUB_CLIENT_ID=your-client-id
heroku config:set GITHUB_CLIENT_SECRET=your-client-secret
heroku config:set GITHUB_REDIRECT_URI=https://your-app.herokuapp.com/auth/callback
git push heroku main
```

## 🏗️ Architecture

### Backend (Python/Flask)

- **GitHub Service** - Handles all GitHub API interactions
- **Template System** - Manages content templates and validation
- **OAuth Service** - Handles GitHub authentication flow
- **Main App** - Flask application with REST API

### Frontend (Vanilla JS)

- **Repository Management** - Browse and select repositories
- **Content Editor** - Template-based content editing
- **File Browser** - Navigate repository structure  
- **Branch Manager** - Git branch operations

### Key Components

```
cardpress/
├── app.py                 # Main Flask application
├── github_service.py      # GitHub API integration
├── template_system.py     # Content templates
├── oauth_service.py       # OAuth authentication
├── admin.html            # Web interface
├── templates.yml         # Template definitions
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
└── docker-compose.yml   # Multi-container setup
```

## 🔧 API Reference

### Authentication

- `GET /auth/login` - Initiate GitHub OAuth
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Logout user
- `GET /api/auth/verify` - Verify authentication

### Repositories

- `GET /api/repositories` - List accessible repositories
- `POST /api/repositories/{repo}/select` - Select repository

### Content

- `GET /api/content` - List content files
- `GET /api/content/{path}` - Get file content
- `PUT /api/content/{path}` - Update file
- `POST /api/content` - Create new file
- `DELETE /api/content/{path}` - Delete file

### Templates

- `GET /api/templates` - List available templates
- `GET /api/templates/{name}` - Get template definition

### Images

- `POST /api/images/upload` - Upload image to repository

### Branches

- `GET /api/branches` - List repository branches
- `POST /api/branches` - Create new branch

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode
FLASK_ENV=development python app.py

# The app will reload automatically on file changes
```

### Adding New Features

1. **Backend**: Extend services in `github_service.py`, `template_system.py`
2. **Frontend**: Update `admin.html` with new UI components
3. **Templates**: Add new field types in `template_system.py`
4. **API**: Add new endpoints in `app.py`

### Testing

```bash
# Run basic health check
curl http://localhost:8000/

# Test API endpoints (requires authentication)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/repositories
```

## 🔒 Security

- **OAuth Authentication** - Secure GitHub integration
- **Token-based Sessions** - JWT tokens for API access
- **Repository Permissions** - Respects GitHub repository permissions
- **CSRF Protection** - State parameter in OAuth flow
- **Input Validation** - Template-based field validation

## 🐛 Troubleshooting

### Common Issues

**OAuth Error: "The redirect_uri MUST match the registered callback URL"**
- Ensure `GITHUB_REDIRECT_URI` in `.env` matches your OAuth app settings
- Check for trailing slashes and exact URL match

**Repository Access Denied**
- Ensure you have push access to the repository
- Re-authenticate to grant proper permissions

**Templates Not Loading**
- Check `templates.yml` syntax is valid YAML
- Ensure file permissions allow reading

**Images Not Uploading**
- Verify repository permissions for file creation
- Check file size limits (GitHub has 100MB limit)

### Debug Mode

Enable debug mode for detailed error messages:

```env
FLASK_ENV=development
```

### Logs

Application logs are written to stdout. For Docker:

```bash
docker-compose logs -f tinacms-clone
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 for Python code
- Use semantic commit messages
- Add tests for new features
- Update documentation

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs on GitHub Issues
- **Documentation**: See this README and inline code comments
- **Community**: Join discussions in GitHub Discussions

---

**Transform your GitHub repositories into a powerful CMS! 🚀**

Built with ❤️ for developers who want the power of Git with the ease of a CMS.

