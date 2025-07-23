# HeyTicker Blog  
**Trello-powered Pelican Static Blog Generator + Auto-Refresh System**

---

## ✨ Overview

**Ticker Blog** is a lightweight system that lets you manage a **static blog** through **Trello** with automatic GitHub synchronization.

- Write and organize posts in Trello
- Automatically generate a static blog using Pelican
- Sync changes to GitHub automatically
- Host the blog on **Cloudflare Pages**
- Trigger blog rebuilds instantly using a **Cloudflare Worker** at `/refresh`

✅ **No CMS needed**  
✅ **Full control over templates and content**  
✅ **Automatic GitHub synchronization**  
✅ **Handles post additions, updates, and deletions**  
✅ **Secure, fast, and fully serverless**

---

## 🏗️ Project Structure

```
/
├── trello_to_pelican.py        # Trello to Pelican content generator
├── requirements.txt             # Python dependencies
├── blog/                        # Pelican blog configuration
│   ├── pelicanconf.py          # Pelican settings
│   ├── publishconf.py          # Production settings
│   ├── content/                # Generated markdown content
│   └── theme/                  # Blog theme templates
├── output/                      # Generated static site (auto-created)
├── worker/
│   └── refresh.js              # Cloudflare Worker to trigger rebuild
├── .github/
│   └── workflows/              # GitHub Actions (optional)
├── .env.example                # Example environment variables
├── .gitignore                  # Ignore output/ and secrets
├── wrangler.toml               # Cloudflare Worker configuration
└── README.md                   # This file
```

---

## ⚙️ How It Works

1. **Manage content in Trello**  
   - Cards in "Ready to Publish" or "Published" lists are treated as blog posts.
   - Supports front matter for metadata (title, date, author, etc.)
   - Downloads images from Trello attachments

2. **Build the static blog**  
   - `trello_to_pelican.py` fetches Trello cards and generates markdown content.
   - Pelican renders pages using Jinja2 templates.
   - Outputs static files into `/output/`.

3. **Automatic GitHub synchronization**  
   - Syncs all changes to GitHub using the GitHub API.
   - Handles additions, updates, and deletions automatically.
   - Works in any environment (including Cloudflare Workers).

4. **Host on Cloudflare Pages**  
   - Cloudflare automatically builds and serves the blog from `blog/output/`.

5. **Trigger rebuilds using `/refresh` endpoint**  
   - A Cloudflare Worker listens at `/refresh`.
   - When called with a secret key, it triggers a rebuild via Cloudflare Deploy Hook.

---

## 🛠️ Setup Instructions

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Configure Environment Variables

Create a `.env` file (based on `.env.example`) with your credentials:

```
# Trello Configuration
TRELLO_API_KEY=your-trello-api-key
TRELLO_TOKEN=your-trello-token
BOARD_ID=your-trello-board-id
DISCORD_PUBLIC=your-discord-webhook-url

# GitHub Configuration (for automatic commits)
GITHUB_TOKEN=your-github-personal-access-token
GITHUB_REPO=your-username/ticker-blog

# Cloudflare Deploy Hook (optional)
CLOUDFLARE_DEPLOY_HOOK=your-cloudflare-deploy-hook-url
```

✅ These are automatically used by `trello_to_pelican.py`.

---

### 3. Run Blog Generator Locally (optional)

```bash
python trello_to_pelican.py
cd blog && pelican content -o ../output -s pelicanconf.py
```

This generates the static site into the `blog/output/` folder and syncs changes to GitHub.

---

### 4. Cloudflare Pages Setup

- Connect this GitHub repo to **Cloudflare Pages**.
- Set Build Settings:
  - **Build command:** `python trello_to_pelican.py && cd blog && pelican content -o ../output -s pelicanconf.py`
  - **Output directory:** `output`
- Set the following Environment Variables inside Cloudflare Pages:
  - `TRELLO_API_KEY`
  - `TRELLO_TOKEN`
  - `BOARD_ID`
  - `GITHUB_TOKEN` (for automatic commits)
  - `GITHUB_REPO` (your repository name)

✅ Now every deployment will pull Trello cards and regenerate the blog automatically.

---

### 5. Cloudflare Worker Setup

- Navigate to [Cloudflare Workers](https://dash.cloudflare.com/).
- Create a new Worker.
- Use the code from `worker/refresh.js`.
- Set Environment Variables for the Worker:
  - `REFRESH_SECRET_KEY` → Your secret to protect `/refresh`
  - `DEPLOY_HOOK_URL` → Your Cloudflare Pages Deploy Hook URL
- Deploy the Worker and map it to:

```
https://blog.heyticker.com/refresh
```

✅ Now you have a secure endpoint to trigger rebuilds manually or automatically.

---

## 🚀 How to Trigger a Blog Rebuild

To trigger a rebuild, call:

```
https://blog.heyticker.com/refresh?key=YOUR_SECRET
```

✅ Only works if you provide the correct secret key.  
✅ The Worker triggers your Cloudflare Pages deploy hook.  
✅ Cloudflare regenerates and deploys the blog.

## 🔄 Automatic GitHub Sync

The system automatically syncs all changes to GitHub:

- **New posts**: Added to GitHub with proper metadata
- **Updated posts**: Modified in GitHub with new content
- **Deleted posts**: Removed from GitHub when deleted from Trello
- **Images**: Downloaded and committed to the repository

✅ Works in any environment (local, Cloudflare Workers, etc.)  
✅ Uses GitHub API (no SSH keys required)  
✅ Sends Discord notifications about sync status

---

## 🔐 Important Security Notes

- **Protect `/refresh`** with a strong `REFRESH_SECRET_KEY`.
- **Never push** your real `.env` file to GitHub — use `.env.example` to document required environment variables.
- **Use Environment Variables** inside Cloudflare Pages and Workers, not hardcoded secrets.
- **GitHub Token**: Create a Personal Access Token with `repo` permissions for automatic commits.
- **Trello Lists**: Only cards in "Ready to Publish" or "Published" lists are processed.

---

## 🌟 Final Notes

This project is designed to be:

- **Serverless**
- **Cheap (or free) to run**
- **Easy to manage**
- **Expandable into a full SaaS if needed**
- **Version controlled** with automatic GitHub sync

✅ You can manage your entire blog through Trello + Cloudflare  
✅ With minimal code, maximum flexibility!  
✅ Full version control and deployment automation

