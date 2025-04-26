# CardPress  
**Trello-powered Static Blog Generator + Auto-Refresh System**

---

## ✨ Overview

**CardPress** is a lightweight system that lets you manage a **static blog** through **Trello**.

- Write and organize posts in Trello
- Automatically generate a static blog
- Host the blog on **Cloudflare Pages**
- Trigger blog rebuilds instantly using a **Cloudflare Worker** at `/refresh`

✅ **No CMS needed**  
✅ **Full control over templates and content**  
✅ **Secure, fast, and fully serverless**

---

## 🏗️ Project Structure

```
/
├── generate.py                 # Blog generator script
├── requirements.txt            # Python dependencies
├── templates/                  # Blog page templates
│   ├── index_template.html
│   ├── post_template.html
│   ├── category_template.html
├── output/                      # (Generated blog - auto-created)
├── worker/
│   ├── refresh.js               # Cloudflare Worker to trigger rebuild
├── .env.example                 # Example environment variables
├── .gitignore                   # Ignore output/ and secrets
├── README.md                    # This file
```

---

## ⚙️ How It Works

1. **Manage content in Trello**  
   - Cards in "Ready to Publish" or "Published" lists are treated as blog posts.

2. **Build the static blog**  
   - `generate.py` fetches Trello cards.
   - Renders pages using Jinja2 templates.
   - Outputs static files into `/output/`.

3. **Host on Cloudflare Pages**  
   - Cloudflare automatically builds and serves the blog from `/output/`.

4. **Trigger rebuilds using `/refresh` endpoint**  
   - A Cloudflare Worker listens at `/refresh`.
   - When called with a secret key, it triggers a rebuild via Cloudflare Deploy Hook.

---

## 🛠️ Setup Instructions

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Configure Trello Access

Create a `.env` file (based on `.env.example`) with your Trello API credentials:

```
TRELLO_API_KEY=your-trello-api-key
TRELLO_TOKEN=your-trello-token
BOARD_ID=your-trello-board-id
```

✅ These are automatically used by `generate.py`.

---

### 3. Run Blog Generator Locally (optional)

```bash
python generate.py
```

This generates the static site into the `/output/` folder.

---

### 4. Cloudflare Pages Setup

- Connect this GitHub repo to **Cloudflare Pages**.
- Set Build Settings:
  - **Build command:** `python generate.py`
  - **Output directory:** `output`
- Set the following Environment Variables inside Cloudflare Pages:
  - `TRELLO_API_KEY`
  - `TRELLO_TOKEN`
  - `BOARD_ID`

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

---

## 🔐 Important Security Notes

- **Protect `/refresh`** with a strong `REFRESH_SECRET_KEY`.
- **Never push** your real `.env` file to GitHub — use `.env.example` to document required environment variables.
- **Use Environment Variables** inside Cloudflare Pages and Workers, not hardcoded secrets.

---

## 🌟 Final Notes

This project is designed to be:

- **Serverless**
- **Cheap (or free) to run**
- **Easy to manage**
- **Expandable into a full SaaS if needed**

✅ You can manage your entire blog through Trello + Cloudflare  
✅ With minimal code, maximum flexibility!

