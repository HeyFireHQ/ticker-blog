import os
import shutil
import re
import requests
import time
from collections import defaultdict
from jinja2 import Template
from dotenv import load_dotenv
import markdown

# Load environment variables
load_dotenv('.env')

TRELLO_API_KEY = os.getenv('TRELLO_API_KEY')
TRELLO_TOKEN = os.getenv('TRELLO_TOKEN')
BOARD_ID = os.getenv('BOARD_ID')
SITE_BASE_URL = os.getenv('SITE_BASE_URL')

OUTPUT_DIR = 'output'
POST_TEMPLATE_FILE = 'templates/post_template.html'
INDEX_TEMPLATE_FILE = 'templates/index_template.html'
CATEGORY_TEMPLATE_FILE = 'templates/category_template.html'

ALLOWED_LISTS = ["Ready to Publish", "Published"]

# --- Helpers ---

def fetch_trello_cards():
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards?attachments=true&labels=all&key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def fetch_trello_lists():
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists?key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def slugify(value):
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-')

def extract_slug_and_clean_title(title):
    match = re.search(r'\[slug:(.*?)\]', title)
    if match:
        custom_slug = match.group(1).strip()
        title = re.sub(r'\[slug:.*?\]', '', title).strip()
    else:
        custom_slug = slugify(title)
    return custom_slug, title

# --- Load templates ---

with open(POST_TEMPLATE_FILE, 'r') as f:
    post_template = Template(f.read())

with open(INDEX_TEMPLATE_FILE, 'r') as f:
    index_template = Template(f.read())

with open(CATEGORY_TEMPLATE_FILE, 'r') as f:
    category_template = Template(f.read())

# --- Clean output directory ---
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)

os.makedirs(OUTPUT_DIR)
os.makedirs(os.path.join(OUTPUT_DIR, "category"))

# --- Main build ---

cards = fetch_trello_cards()
lists = fetch_trello_lists()
list_mapping = {lst['id']: lst['name'] for lst in lists}

posts = []
categories = defaultdict(list)

for card in cards:
    card_list_name = list_mapping.get(card['idList'], "")

    if card_list_name not in ALLOWED_LISTS:
        continue  # Skip drafts etc

    original_title = card['name']
    description_md = card['desc']
    image_url = card['attachments'][0]['url'] if card['attachments'] else None
    labels = [label['name'] for label in card['labels']]

    slug, clean_title = extract_slug_and_clean_title(original_title)

    # Convert Markdown description to HTML
    body_html = markdown.markdown(description_md)

    # Get the date from the card's last activity
    date = card.get('dateLastActivity', '').split('T')[0]  # Get just the date part

    post_info = {
        'title': clean_title,
        'slug': slug,
        'categories': labels,
        'date': date,
        'image_url': image_url
    }
    posts.append(post_info)

    # --- Create folder and index.html for each post ---
    post_dir = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(post_dir, exist_ok=True)

    # Get latest posts for the sidebar
    latest_posts = sorted(posts, key=lambda x: x['date'], reverse=True)[:3]

    rendered_post = post_template.render(
        title=clean_title,
        body=body_html,
        image_url=image_url,
        categories=labels,
        date=date,
        latest_posts=latest_posts
    )
    with open(os.path.join(post_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(rendered_post)

    for label in labels:
        categories[label].append(post_info)

# --- Generate homepage (index.html) ---

rendered_index = index_template.render(posts=posts, categories=categories)

with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
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
    with open(os.path.join(category_dir, 'index.html'), 'w', encoding='utf-8') as f:
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

with open(os.path.join(OUTPUT_DIR, 'sitemap.xml'), 'w', encoding='utf-8') as f:
    f.write(sitemap_content)

print("✅ CardPress blog generated successfully with Markdown, custom slugs, and clean output!")
