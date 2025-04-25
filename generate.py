import requests
import os
import shutil
import time
from jinja2 import Template
import re
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv('.env')  # Load local environment variables

TRELLO_API_KEY = os.getenv('TRELLO_API_KEY')
TRELLO_TOKEN = os.getenv('TRELLO_TOKEN')
BOARD_ID = os.getenv('BOARD_ID')
SITE_BASE_URL = os.getenv('SITE_BASE_URL')

OUTPUT_DIR = 'output'
POST_TEMPLATE_FILE = 'templates/post_template.html'
INDEX_TEMPLATE_FILE = 'templates/index_template.html'
CATEGORY_TEMPLATE_FILE = 'templates/category_template.html'

ALLOWED_LISTS = ["Ready to Publish", "Published"]

# --- Fetch Trello cards ---
def fetch_trello_cards():
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards?attachments=true&labels=all&key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# --- Slugify titles for URLs ---
def slugify(value):
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-')

# --- Load templates ---
with open(POST_TEMPLATE_FILE, 'r') as f:
    post_template_content = f.read()

with open(INDEX_TEMPLATE_FILE, 'r') as f:
    index_template_content = f.read()

with open(CATEGORY_TEMPLATE_FILE, 'r') as f:
    category_template_content = f.read()

post_template = Template(post_template_content)
index_template = Template(index_template_content)
category_template = Template(category_template_content)

# --- Clean output directory ---
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)

os.makedirs(OUTPUT_DIR)
os.makedirs(os.path.join(OUTPUT_DIR, "category"))

# --- Main build ---
cards = fetch_trello_cards()

# Fetch list names
list_url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists?key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
list_response = requests.get(list_url)
list_response.raise_for_status()
lists = list_response.json()
list_mapping = {lst['id']: lst['name'] for lst in lists}

posts = []
categories = defaultdict(list)

for card in cards:
    card_list_name = list_mapping.get(card['idList'], "")

    if card_list_name not in ALLOWED_LISTS:
        continue  # Skip drafts etc

    title = card['name']
    body = card['desc']
    image_url = card['attachments'][0]['url'] if card['attachments'] else None
    labels = [label['name'] for label in card['labels']]  # Trello labels
    slug = slugify(title)

    post_info = {
        'title': title,
        'slug': slug,
        'categories': labels
    }
    posts.append(post_info)

    # --- Create folder and index.html for each post ---
    post_dir = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(post_dir, exist_ok=True)
    rendered_post = post_template.render(
        title=title,
        body=body,
        image_url=image_url,
        categories=labels
    )
    with open(os.path.join(post_dir, 'index.html'), 'w') as f:
        f.write(rendered_post)

    for label in labels:
        categories[label].append(post_info)

# --- Generate homepage (index.html) ---
rendered_index = index_template.render(posts=posts, categories=categories)

with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
    f.write(rendered_index)

# --- Generate per-category pages ---
for category_name, posts_in_category in categories.items():
    category_slug = slugify(category_name)
    category_dir = os.path.join(OUTPUT_DIR, 'category', category_slug)
    os.makedirs(category_dir, exist_ok=True)

    rendered_category = category_template.render(
        category_name=category_name,
        posts=posts_in_category
    )
    with open(os.path.join(category_dir, 'index.html'), 'w') as f:
        f.write(rendered_category)

# --- Generate sitemap.xml ---
sitemap_entries = []

# Add all posts
for post in posts:
    sitemap_entries.append(f"<url><loc>{SITE_BASE_URL}/{post['slug']}/</loc></url>")

# Add all categories
for category_name in categories.keys():
    category_slug = slugify(category_name)
    sitemap_entries.append(f"<url><loc>{SITE_BASE_URL}/category/{category_slug}/</loc></url>")

sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(sitemap_entries)}
</urlset>
"""

with open(os.path.join(OUTPUT_DIR, 'sitemap.xml'), 'w') as f:
    f.write(sitemap_content)

print("✅ CardPress blog generated successfully with pretty URLs and clean output!")