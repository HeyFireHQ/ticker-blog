AUTHOR = 'Jon V'
SITENAME = 'HeyTicker Blog'
SITEURL = "https://blog.heyticker.com"
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
