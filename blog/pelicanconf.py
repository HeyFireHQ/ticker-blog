AUTHOR = 'Jon V'
SITENAME = 'HeyTicker Blog'
SITEURL = ""
THEME = 'theme'

# Add these two:
SITENAME = "HeyTicker Blog"

# For the footer
CURRENT_YEAR = 2025

PATH = "content"

TIMEZONE = 'America/Los_Angeles'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (
    ("Pelican", "https://getpelican.com/"),
    ("Python.org", "https://www.python.org/"),
    ("Jinja2", "https://palletsprojects.com/p/jinja/"),
    ("You can modify those links in your config file", "#"),
)

# Social widget
SOCIAL = (
    ("You can add links in your config file", "#"),
    ("Another social link", "#"),
)

DEFAULT_PAGINATION = 10

PLUGIN_PATHS = ['pelican-plugins']
PLUGINS = ['sitemap']

# Configure the sitemap
SITEMAP = {
    'format': 'xml',
    'priorities': {
        'articles': 0.7,
        'pages': 0.5,
        'indexes': 0.5,
    },
    'changefreqs': {
        'articles': 'weekly',
        'pages': 'monthly',
        'indexes': 'daily',
    }
}

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True

def fix_yaml_formatting(yaml_text):
    """Fix common YAML formatting issues caused by auto-formatting"""
    lines = yaml_text.split('\n')
    fixed_lines = []
    
    for line in lines:
        if ':' in line and '[' in line and '](' in line:
            # This line contains a markdown link, quote it
            key, value = line.split(':', 1)
            value = value.strip()
            # Quote the entire value to make it valid YAML
            line = f'{key}: "{value}"'
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def parse_front_matter(text):
    front_matter = {}
    body = text

    if text.strip().startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            yaml_block = parts[1]
            body = parts[2].lstrip('\n')
            
            # Fix YAML formatting issues
            yaml_block = fix_yaml_formatting(yaml_block)
            
            try:
                front_matter = yaml.safe_load(yaml_block) or {}
            except yaml.YAMLError as e:
                print(f"⚠️ YAML parsing error: {e}")
                print(f"YAML block: {yaml_block}")
                front_matter = {}

    return front_matter, body

# Prepare metadata
metadata = [
    f"Title: {original_title}",
    f"Date: {today_date}",
    f"Slug: {slug}",
    f"Image: {image_url}"
]
if author:
    metadata.append(f"Author: {author}")
if author_url:
    metadata.append(f"Authorurl: {author_url}")
if labels:
    metadata.append(f"Tags: {', '.join(labels)}")

# Always add colors, even if empty
if label_colors:
    metadata.append(f"Colors: {', '.join(label_colors)}")
else:
    metadata.append(f"Colors: #F97316")  # Default color
