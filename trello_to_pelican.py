import os
import shutil
import re
import requests
import yaml
from dotenv import load_dotenv
from datetime import datetime
from discord import SyncWebhook, File

# Load environment variables
load_dotenv('.env')

TRELLO_API_KEY = os.getenv('TRELLO_API_KEY')
TRELLO_TOKEN = os.getenv('TRELLO_TOKEN')
BOARD_ID = os.getenv('BOARD_ID')
DISCORD_PUBLIC = os.getenv('DISCORD_PUBLIC')

CONTENT_DIR = 'blog/content'
IMAGES_DIR = os.path.join(CONTENT_DIR, 'imgs')
ALLOWED_LISTS = ["Ready to Publish", "Published"]

# Mapping of Trello label color names to HEX codes
TRELLO_COLOR_HEX = {
    'green': '#61BD4F',
    'yellow': '#F2D600',
    'orange': '#FF9F1A',
    'red': '#EB5A46',
    'purple': '#C377E0',
    'blue': '#0079BF',
    'sky': '#00C2E0',
    'pink': '#FF78CB',
    'black': '#344563',
    'lime': '#51e898',
    'null': ''
}


def send_message_to_discord(message, file_stream=None):
    try:
        discord_url = DISCORD_PUBLIC 
        webhook = SyncWebhook.from_url(discord_url) # Initializing webhook
        if file_stream:
            import io
            import base64
            file_stream = file_stream.split(',')[1]
            
            # Decode base64 image
            file_stream = base64.b64decode(file_stream)
            file_stream = io.BytesIO(file_stream)
            file = File(file_stream, filename=message+'.png')
            webhook.send(content=message, file=file)
        else:
            webhook.send(content=message)
    except:
        pass

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

def extract_markdown_link(text):
    """Extract name and URL from markdown link [name](url)"""
    match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', text.strip())
    if match:
        return match.group(1), match.group(2)  # name, url
    return text.strip(), None

def parse_front_matter(text):
    front_matter = {}
    body = text

    if text.strip().startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            yaml_block = parts[1]
            body = parts[2].lstrip('\n')
            
            try:
                front_matter = yaml.safe_load(yaml_block) or {}
                
                # Post-process author field if it contains markdown
                if 'author' in front_matter:
                    author_text = str(front_matter['author'])
                    if '[' in author_text and '](' in author_text:
                        name, url = extract_markdown_link(author_text)
                        front_matter['author-name'] = name
                        front_matter['author-url'] = url
                        del front_matter['author']
                        
            except yaml.YAMLError as e:
                print(f"⚠️ YAML parsing error: {e}")
                front_matter = {}

    return front_matter, body

def download_image(url, save_path):
    headers = {
        "Accept": "application/json"
    }
    if "trello.com" in url:
        if '?' in url:
            url += f"&key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
        else:
            url += f"?key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    with open(save_path, 'wb') as f:
        f.write(response.content)

    return save_path

#os.makedirs(CONTENT_DIR)
#os.makedirs(IMAGES_DIR)

# --- Main build ---

cards = fetch_trello_cards()
lists = fetch_trello_lists()
list_mapping = {lst['id']: lst['name'] for lst in lists}

for card in cards:
    card_list_name = list_mapping.get(card['idList'], "")

    if card_list_name not in ALLOWED_LISTS:
        continue  # Skip drafts etc

    original_title = card['name']
    description_full = card['desc']
    attachments = card.get('attachments', [])
    labels = [label['name'] for label in card['labels']]

    # NEW: capture label colors
    label_colors = []
    for label in card['labels']:
        color_name = label.get('color')
        if color_name and color_name in TRELLO_COLOR_HEX:
            label_colors.append(TRELLO_COLOR_HEX[color_name])

    # Parse front matter
    front_matter, description_md = parse_front_matter(description_full)

    # Get date - priority: front matter > card creation date
    custom_date = front_matter.get('date', None)
    if custom_date:
        article_date = custom_date
    else:
        # Extract date from card ID (creation date)
        card_id = card['id']
        timestamp = int(card_id[:8], 16)
        card_date = datetime.fromtimestamp(timestamp)
        article_date = card_date.strftime('%Y-%m-%d')

    slug = front_matter.get('slug') or slugify(original_title)
    author = front_matter.get('author-name', None)
    author_url = front_matter.get('author-url', None)
    description = front_matter.get('description', None)
    keywords = front_matter.get('keywords', None)
    custom_image_name = front_matter.get('image', None)

    image_markdown = ""

    # If attachment exists, download properly
    if attachments:
        image_url = attachments[0]['url']
        if not custom_image_name:
            custom_image_name = os.path.basename(image_url.split('?')[0])

        image_save_path = os.path.join(IMAGES_DIR, custom_image_name)
        
        try:
            result = download_image(image_url, image_save_path)
            image_markdown = f"![{original_title}](imgs/{custom_image_name})\n\n"
        except Exception as e:
            print(f"⚠️ Failed to download {image_url}: {e}")
            image_markdown = f"![{original_title}]({image_url})\n\n"

    # Prepare metadata
    metadata = [
        f"Title: {original_title}",
        f"Date: {article_date}",  # Use the extracted date
        f"Slug: {slug}",
        f"Image: {image_url}"
    ]
    if author:
        metadata.append(f"Author: {author}")
    if author_url:
        metadata.append(f"Authorurl: {author_url}")
    if description:
        metadata.append(f"Description: {description}")
    if keywords:
        metadata.append(f"Keywords: {keywords}")
    if labels:
        metadata.append(f"Tags: {', '.join(labels)}")
    if label_colors:
        metadata.append(f"Colors: {', '.join(label_colors)}")
    else:
        metadata.append(f"Colors: #F97316")

    # Full file content
    file_content = '\n'.join(metadata) + '\n\n' + description_md

    # Write to file
    post_filename = f"{slug}.md"
    post_path = os.path.join(CONTENT_DIR, post_filename)

    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(file_content)
    
    send_message_to_discord(f"New post: {original_title}")

print("✅ Markdown files with downloaded images and colors generated successfully!")
