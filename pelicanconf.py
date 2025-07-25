AUTHOR = 'Jon V'
SITENAME = 'HeyTicker Blog'
SITEURL = "https://blog.heyticker.com"
THEME = 'theme'

# For the footer
CURRENT_YEAR = 2025

PATH = "content/"

TIMEZONE = 'America/Los_Angeles'

DEFAULT_LANG = 'en'

# URL settings for proper routing
ARTICLE_URL = '{slug}/'
ARTICLE_SAVE_AS = '{slug}/index.html'
PAGE_URL = 'pages/{slug}/'
PAGE_SAVE_AS = 'pages/{slug}/index.html'
CATEGORY_URL = 'category/{slug}/'
CATEGORY_SAVE_AS = 'category/{slug}/index.html'
TAG_URL = 'tag/{slug}/'
TAG_SAVE_AS = 'tag/{slug}/index.html'

# Static files (images, etc.)
STATIC_PATHS = ['imgs']
EXTRA_PATH_METADATA = {
    'imgs/*': {'path': 'imgs/'},
}

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DEFAULT_PAGINATION = 10

PLUGIN_PATHS = ['plugins']
PLUGINS = ['sitemap', 'fix_img_paths']

# Markdown settings
MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.codehilite': {'css_class': 'highlight'},
        'markdown.extensions.extra': {},
        'markdown.extensions.meta': {},
        'markdown.extensions.toc': {},
        'markdown.extensions.nl2br': {},
        'markdown.extensions.sane_lists': {},
    },
    'output_format': 'html5',
}

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
