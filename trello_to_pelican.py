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
    """Parse simple metadata from card description instead of YAML"""
    metadata = {}
    body = text

    # Look for simple key: value patterns in the description
    lines = text.split('\n')
    body_lines = []
    in_body = False
    
    for line in lines:
        if ':' in line and not in_body:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key in ['title', 'date', 'slug', 'author', 'description', 'keywords', 'image']:
                metadata[key] = value
            else:
                # If we hit a line that doesn't look like metadata, start body
                in_body = True
                body_lines.append(line)
        else:
            in_body = True
            body_lines.append(line)
    
    body = '\n'.join(body_lines).strip()
    return metadata, body

# Ensure directories exist
os.makedirs(CONTENT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# --- Main build ---

cards = fetch_trello_cards()
lists = fetch_trello_lists()
list_mapping = {lst['id']: lst['name'] for lst in lists}

for card in cards:
    try:
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
        author = front_matter.get('author', None)
        author_url = front_matter.get('author-url', None)
        description = front_matter.get('description', None)
        keywords = front_matter.get('keywords', None)
        custom_image_name = front_matter.get('image', None)

        image_markdown = ""
        image_url = ""

        # If attachment exists, use the URL directly (no download)
        if attachments:
            image_url = attachments[0]['url']
            if not custom_image_name:
                custom_image_name = os.path.basename(image_url.split('?')[0])

            # Use the original Trello URL in markdown (no download attempt)
            image_markdown = f"![{original_title}]({image_url})\n\n"

        # Prepare metadata
        metadata = [
            f"Title: {original_title}",
            f"Date: {article_date}",  # Use the extracted date
            f"Slug: {slug}",
        ]
        if image_url:
            metadata.append(f"Image: {image_url}")
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
    
    except Exception as e:
        error_message = f"❌ Error processing card '{card.get('name', 'Unknown')}': {str(e)}"
        print(error_message)
        send_message_to_discord(error_message)

print("✅ Markdown files with downloaded images and colors generated successfully!")
