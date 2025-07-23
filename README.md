# Ticker Blog - Multi-System Blog Management

**A collection of blog management tools and systems**

---

## 📁 Project Structure

This repository contains multiple blog management systems and tools:

### 🎯 **CardPress** (`/cardpress/`)
**Modern Cloudflare-powered blog admin system with GitHub Pages integration**

- 🔐 **Admin-only interface** with secure authentication
- 🌐 **Cloudflare edge infrastructure** (D1, R2, Workers)
- 🚀 **GitHub Pages deployment** with live preview
- 📱 **Responsive admin interface** with Kanban workflow
- 👥 **Multi-admin user management**

**→ [📖 CardPress Documentation](./cardpress/README.md)**

---

### 📚 **Legacy Blog System** (`/blog/`)
**Traditional Pelican-based static site generator**

- Static site generation with Pelican
- Theme customization
- Traditional file-based workflow

---

### 🔧 **Migration Tools**
**Scripts for migrating between different blog systems**

- `trello_to_pelican.py` - Convert Trello boards to Pelican posts
- Legacy Firebase migration tools

---

## 🚀 Quick Start

### For New Users (Recommended)
**Use CardPress for a modern blog management experience:**

```bash
cd cardpress/
./setup-cloudflare.sh
```

### For Legacy System
**Use the traditional Pelican workflow:**

```bash
cd blog/
pelican content
```

---

## 🎯 Which System Should I Use?

| Feature | CardPress | Legacy Blog |
|---------|-----------|-------------|
| **Admin Interface** | ✅ Beautiful web UI | ❌ Command line only |
| **Multi-user** | ✅ Admin management | ❌ Single user |
| **Cloud Integration** | ✅ Cloudflare edge | ❌ Local files |
| **GitHub Integration** | ✅ Auto-deploy | ⚙️ Manual |
| **Image Management** | ✅ R2 cloud storage | ❌ Local files |
| **Security** | ✅ Admin-only access | ❌ No authentication |
| **Performance** | ✅ Global CDN | ⚡ Static files |
| **Learning Curve** | 🟢 Easy setup | 🟡 Requires technical knowledge |

**Recommendation**: Use **CardPress** for new projects. It provides a modern, secure, and user-friendly blog management experience.

---

## 📋 Requirements

### CardPress Requirements
```bash
# Node.js (for Wrangler CLI)
node --version  # v16+ required

# Python (for Pelican generation)
python3 --version  # v3.7+ required

# Dependencies
npm install -g wrangler
pip install -r requirements.txt
```

### Legacy Blog Requirements
```bash
# Python and Pelican
pip install pelican markdown
```

---

## 🛠️ Development

### CardPress Development
```bash
cd cardpress/
wrangler dev --local
```

### Legacy Blog Development
```bash
cd blog/
pelican content --autoreload --listen
```

---

## 📈 Migration Path

### From Legacy Blog to CardPress
1. **Export existing posts** using migration tools
2. **Set up CardPress** following the setup guide
3. **Import posts** via the admin interface
4. **Configure GitHub Pages** for deployment

### From Other Systems
- **From Trello**: Use `trello_to_pelican.py`
- **From Firebase**: Use migration tools in CardPress
- **From WordPress**: Export to markdown, then import to CardPress

---

## 🤝 Contributing

### CardPress Contributions
See [CardPress README](./cardpress/README.md) for specific contribution guidelines.

### General Project Contributions
```bash
# Fork repository
git clone https://github.com/your-username/ticker-blog.git

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
# Submit pull request
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🆘 Support

- 📖 **CardPress Documentation**: [./cardpress/README.md](./cardpress/README.md)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-repo/ticker-blog/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-repo/ticker-blog/discussions)

---

**Choose CardPress for a modern blog management experience! 🚀** 