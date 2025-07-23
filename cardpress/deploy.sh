#!/bin/bash

# CardPress - Multi-Platform Deployment Script
# Fetches posts from Cloudflare D1, generates static site, and deploys

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 CardPress - Deploy Script${NC}"
echo -e "${PURPLE}============================${NC}"

# Check if running from cardpress directory
if [[ ! -f "wrangler.toml" ]]; then
    echo -e "${RED}❌ Error: Please run this script from the cardpress/ directory${NC}"
    echo -e "${YELLOW}   cd cardpress/ && ./deploy.sh${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to log with timestamp
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

# Function to check requirements
check_requirements() {
    log "Checking requirements..."
    
    local missing_reqs=()
    
    if ! command_exists python3; then
        missing_reqs+=("python3")
    fi
    
    if ! python3 -c "import pelican" 2>/dev/null; then
        missing_reqs+=("pelican (pip install pelican)")
    fi
    
    if ! python3 -c "import requests" 2>/dev/null; then
        missing_reqs+=("requests (pip install requests)")
    fi
    
    if [ ${#missing_reqs[@]} -ne 0 ]; then
        echo -e "${RED}❌ Missing requirements:${NC}"
        for req in "${missing_reqs[@]}"; do
            echo -e "   - $req"
        done
        exit 1
    fi
    
    echo -e "${GREEN}✅ All requirements satisfied${NC}"
}

# Function to load environment variables
load_environment() {
    if [ -f ".env" ]; then
        log "Loading environment variables..."
        export $(grep -v '^#' .env | xargs)
        echo -e "${GREEN}✅ Environment variables loaded${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env file found. Using defaults.${NC}"
    fi
}

# Function to authenticate with Cloudflare Worker
authenticate_worker() {
    log "Authenticating with Cloudflare Worker..."
    
    if [ -z "$WORKER_URL" ]; then
        echo -e "${RED}❌ WORKER_URL not configured${NC}"
        return 1
    fi
    
    if [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ]; then
        echo -e "${RED}❌ Admin credentials not configured${NC}"
        return 1
    fi
    
    # Test worker authentication
    local auth_response=$(curl -s -X POST "${WORKER_URL}/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")
    
    if echo "$auth_response" | grep -q "token"; then
        export AUTH_TOKEN=$(echo "$auth_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
        echo -e "${GREEN}✅ Worker authentication successful${NC}"
        return 0
    else
        echo -e "${RED}❌ Worker authentication failed${NC}"
        echo -e "${YELLOW}Response: $auth_response${NC}"
        return 1
    fi
}

# Function to check for deployed posts
check_deployed_posts() {
    log "Checking for deployed posts..."
    
    local posts_response=$(curl -s -H "Authorization: Bearer ${AUTH_TOKEN}" "${WORKER_URL}/posts")
    
    if echo "$posts_response" | grep -q "error"; then
        echo -e "${RED}❌ Failed to fetch posts${NC}"
        echo -e "${YELLOW}Response: $posts_response${NC}"
        return 1
    fi
    
    local deployed_count=$(echo "$posts_response" | python3 -c "
import sys, json
posts = json.load(sys.stdin)
deployed = [p for p in posts if p.get('column_status') == 'deployed']
print(len(deployed))
" 2>/dev/null || echo "0")
    
    if [ "$deployed_count" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No posts in deployed status${NC}"
        echo -e "${CYAN}   Move posts to 'Deployed' column in admin interface first${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Found $deployed_count deployed posts ready for publication${NC}"
    return 0
}

# Function to generate static site
generate_static_site() {
    log "Generating static site from Cloudflare posts..."
    
    # Use the cloudflare_to_pelican.py script
    if [ -f "cloudflare_to_pelican.py" ]; then
        if python3 cloudflare_to_pelican.py; then
            echo -e "${GREEN}✅ Static site generated successfully${NC}"
            return 0
        else
            echo -e "${RED}❌ Failed to generate static site${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ cloudflare_to_pelican.py not found${NC}"
        return 1
    fi
}

# Function to deploy to Firebase Hosting
deploy_firebase() {
    log "Deploying to Firebase Hosting..."
    
    if ! command_exists firebase; then
        echo -e "${RED}❌ Firebase CLI not installed${NC}"
        echo -e "${YELLOW}   Install with: npm install -g firebase-tools${NC}"
        return 1
    fi
    
    # Create firebase.json if it doesn't exist
    if [ ! -f "firebase.json" ]; then
        cat > firebase.json << EOF
{
  "hosting": {
    "public": "output",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
EOF
        echo -e "${BLUE}📝 Created firebase.json${NC}"
    fi
    
    if firebase deploy --only hosting; then
        echo -e "${GREEN}✅ Deployed to Firebase Hosting${NC}"
        return 0
    else
        echo -e "${RED}❌ Firebase deployment failed${NC}"
        return 1
    fi
}

# Function to deploy to Netlify
deploy_netlify() {
    log "Deploying to Netlify..."
    
    if ! command_exists netlify; then
        echo -e "${RED}❌ Netlify CLI not installed${NC}"
        echo -e "${YELLOW}   Install with: npm install -g netlify-cli${NC}"
        return 1
    fi
    
    if netlify deploy --prod --dir=output; then
        echo -e "${GREEN}✅ Deployed to Netlify${NC}"
        return 0
    else
        echo -e "${RED}❌ Netlify deployment failed${NC}"
        return 1
    fi
}

# Function to deploy to GitHub Pages
deploy_github_pages() {
    log "Deploying to GitHub Pages..."
    
    if ! command_exists git; then
        echo -e "${RED}❌ Git not installed${NC}"
        return 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}❌ Not in a git repository${NC}"
        return 1
    fi
    
    # Create gh-pages branch if it doesn't exist
    if ! git show-ref --verify --quiet refs/heads/gh-pages; then
        git checkout --orphan gh-pages
        git rm -rf .
        git commit --allow-empty -m "Initial gh-pages commit"
        git checkout main || git checkout master
    fi
    
    # Copy output to gh-pages branch
    git checkout gh-pages
    git rm -rf .
    cp -r output/* .
    git add .
    git commit -m "Deploy CardPress blog $(date)"
    
    if git push origin gh-pages; then
        echo -e "${GREEN}✅ Deployed to GitHub Pages${NC}"
        git checkout main || git checkout master
        return 0
    else
        echo -e "${RED}❌ GitHub Pages deployment failed${NC}"
        git checkout main || git checkout master
        return 1
    fi
}

# Function to deploy to Cloudflare Pages
deploy_cloudflare_pages() {
    log "Deploying to Cloudflare Pages..."
    
    if ! command_exists wrangler; then
        echo -e "${RED}❌ Wrangler CLI not installed${NC}"
        echo -e "${YELLOW}   Install with: npm install -g wrangler${NC}"
        return 1
    fi
    
    if [ -z "$CLOUDFLARE_PAGES_PROJECT" ]; then
        echo -e "${RED}❌ CLOUDFLARE_PAGES_PROJECT not configured${NC}"
        return 1
    fi
    
    if wrangler pages publish output --project-name="$CLOUDFLARE_PAGES_PROJECT"; then
        echo -e "${GREEN}✅ Deployed to Cloudflare Pages${NC}"
        return 0
    else
        echo -e "${RED}❌ Cloudflare Pages deployment failed${NC}"
        return 1
    fi
}

# Function to deploy to custom server via rsync
deploy_custom_server() {
    log "Deploying to custom server..."
    
    if ! command_exists rsync; then
        echo -e "${RED}❌ rsync not installed${NC}"
        return 1
    fi
    
    if [ -z "$DEPLOY_HOST" ] || [ -z "$DEPLOY_PATH" ] || [ -z "$DEPLOY_USER" ]; then
        echo -e "${RED}❌ Custom server configuration incomplete${NC}"
        echo -e "${YELLOW}   Required: DEPLOY_HOST, DEPLOY_PATH, DEPLOY_USER${NC}"
        return 1
    fi
    
    if rsync -avz --delete output/ "${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PATH}"; then
        echo -e "${GREEN}✅ Deployed to custom server${NC}"
        return 0
    else
        echo -e "${RED}❌ Custom server deployment failed${NC}"
        return 1
    fi
}

# Function to trigger refresh webhook
trigger_refresh_webhook() {
    if [ -n "$REFRESH_WEBHOOK_URL" ]; then
        log "Triggering refresh webhook..."
        if curl -s -X POST "$REFRESH_WEBHOOK_URL" > /dev/null; then
            echo -e "${GREEN}✅ Refresh webhook triggered${NC}"
        else
            echo -e "${YELLOW}⚠️  Refresh webhook failed${NC}"
        fi
    fi
}

# Main deployment function
deploy_to_platform() {
    local platform=$1
    
    case $platform in
        1)
            deploy_firebase
            ;;
        2)
            deploy_netlify
            ;;
        3)
            deploy_github_pages
            ;;
        4)
            deploy_cloudflare_pages
            ;;
        5)
            deploy_custom_server
            ;;
        6)
            echo -e "${BLUE}📦 Static site generated only${NC}"
            return 0
            ;;
        7)
            echo -e "${BLUE}🚀 Deploying to all configured platforms...${NC}"
            local success_count=0
            local total_count=0
            
            for p in 1 2 3 4 5; do
                echo -e "${CYAN}--- Platform $p ---${NC}"
                total_count=$((total_count + 1))
                if deploy_to_platform $p; then
                    success_count=$((success_count + 1))
                fi
                echo ""
            done
            
            echo -e "${BLUE}📊 Deployment Summary: $success_count/$total_count platforms successful${NC}"
            return 0
            ;;
        *)
            echo -e "${RED}❌ Invalid platform selection${NC}"
            return 1
            ;;
    esac
}

# Main execution
main() {
    # Parse command line arguments
    local platform=${1:-""}
    
    if [ -z "$platform" ]; then
        echo -e "${BLUE}Choose deployment platform:${NC}"
        echo -e "${YELLOW}1.${NC} 🔥 Firebase Hosting"
        echo -e "${YELLOW}2.${NC} 🌐 Netlify"
        echo -e "${YELLOW}3.${NC} 📚 GitHub Pages"
        echo -e "${YELLOW}4.${NC} ☁️  Cloudflare Pages (recommended)"
        echo -e "${YELLOW}5.${NC} 🖥️  Custom Server (rsync)"
        echo -e "${YELLOW}6.${NC} 📦 Generate Only (no deploy)"
        echo -e "${YELLOW}7.${NC} 🚀 Deploy to All Platforms"
        echo ""
        read -p "$(echo -e "${CYAN}Enter your choice (1-7): ${NC}")" platform
    fi
    
    # Load environment and check requirements
    load_environment
    check_requirements
    
    # Authenticate with worker
    if ! authenticate_worker; then
        exit 1
    fi
    
    # Check for deployed posts
    if ! check_deployed_posts; then
        exit 1
    fi
    
    # Generate static site
    if ! generate_static_site; then
        exit 1
    fi
    
    # Deploy to selected platform(s)
    if deploy_to_platform "$platform"; then
        echo ""
        echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
        
        # Trigger refresh webhook if configured
        trigger_refresh_webhook
        
        echo ""
        echo -e "${BLUE}📊 Deployment Summary:${NC}"
        echo -e "${YELLOW}   Platform:${NC} $platform"
        echo -e "${YELLOW}   Generated:${NC} $(find output -name "*.html" | wc -l) HTML files"
        echo -e "${YELLOW}   Timestamp:${NC} $(date)"
        
        if [ -d "output" ]; then
            echo -e "${YELLOW}   Size:${NC} $(du -sh output | cut -f1)"
        fi
        
        echo ""
        echo -e "${GREEN}✨ Your CardPress blog is now live!${NC}"
    else
        echo ""
        echo -e "${RED}❌ Deployment failed${NC}"
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 