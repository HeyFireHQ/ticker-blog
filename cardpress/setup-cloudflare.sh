#!/bin/bash

# CardPress - Cloudflare Setup Script
# Automated setup for CardPress blog management system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 CardPress - Cloudflare Setup Script${NC}"
echo -e "${PURPLE}====================================${NC}"
echo ""

# Check if running from cardpress directory
if [[ ! -f "wrangler.toml" ]]; then
    echo -e "${RED}❌ Error: Please run this script from the cardpress/ directory${NC}"
    echo -e "${YELLOW}   cd cardpress/ && ./setup-cloudflare.sh${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get user input with default
get_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        read -p "$(echo -e "${CYAN}${prompt} [${default}]: ${NC}")" input
        if [ -z "$input" ]; then
            input="$default"
        fi
    else
        read -p "$(echo -e "${CYAN}${prompt}: ${NC}")" input
    fi
    
    eval "$var_name='$input'"
}

# Function to generate secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

echo -e "${BLUE}Choose setup option:${NC}"
echo -e "${YELLOW}1.${NC} 🆕 Full setup (recommended for new users)"
echo -e "${YELLOW}2.${NC} 🗄️  Create D1 database only"
echo -e "${YELLOW}3.${NC} 📦 Create R2 bucket only" 
echo -e "${YELLOW}4.${NC} ⚡ Deploy Worker only"
echo -e "${YELLOW}5.${NC} 🔧 Configure environment variables"
echo -e "${YELLOW}6.${NC} 🧪 Test setup and configuration"
echo -e "${YELLOW}7.${NC} 👤 Create admin user"
echo -e "${YELLOW}8.${NC} 🧹 Clean up and reset"
echo ""

read -p "$(echo -e "${CYAN}Enter your choice (1-8): ${NC}")" choice

case $choice in
    1)
        echo -e "${GREEN}🆕 Starting full CardPress setup...${NC}"
        
        # Check prerequisites
        echo -e "${BLUE}📋 Checking prerequisites...${NC}"
        
        if ! command_exists wrangler; then
            echo -e "${RED}❌ Wrangler CLI not found${NC}"
            echo -e "${YELLOW}   Install with: npm install -g wrangler${NC}"
            exit 1
        fi
        
        if ! command_exists python3; then
            echo -e "${RED}❌ Python 3 not found${NC}"
            echo -e "${YELLOW}   Please install Python 3.7+${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✅ Prerequisites satisfied${NC}"
        echo ""
        
        # Get configuration
        echo -e "${BLUE}🔧 Configuration Setup${NC}"
        
        get_input "GitHub repository (username/repo)" "" GITHUB_REPO
        get_input "GitHub deploy branch" "gh-pages" GITHUB_BRANCH
        get_input "Admin email address" "admin@example.com" ADMIN_EMAIL
        
        # Generate secure password
        ADMIN_PASSWORD=$(generate_password)
        echo -e "${GREEN}🔐 Generated secure admin password: ${ADMIN_PASSWORD}${NC}"
        
        # Update wrangler.toml
        echo -e "${BLUE}⚙️  Updating Wrangler configuration...${NC}"
        sed -i.bak "s/your-username\/your-repo/${GITHUB_REPO//\//\\/}/g" wrangler.toml
        sed -i.bak "s/gh-pages/${GITHUB_BRANCH}/g" wrangler.toml
        sed -i.bak "s/admin@example.com/${ADMIN_EMAIL}/g" wrangler.toml
        
        # Create D1 database
        echo -e "${BLUE}🗄️  Creating D1 database...${NC}"
        DB_OUTPUT=$(wrangler d1 create cardpress-blog)
        DB_ID=$(echo "$DB_OUTPUT" | grep "database_id" | cut -d'"' -f4)
        
        if [ -n "$DB_ID" ]; then
            echo -e "${GREEN}✅ D1 database created with ID: ${DB_ID}${NC}"
            # Update wrangler.toml with real database ID
            sed -i.bak "s/your-d1-database-id/${DB_ID}/g" wrangler.toml
        else
            echo -e "${RED}❌ Failed to create D1 database${NC}"
            exit 1
        fi
        
        # Initialize database schema
        echo -e "${BLUE}📊 Initializing database schema...${NC}"
        if wrangler d1 execute cardpress-blog --file=schema.sql; then
            echo -e "${GREEN}✅ Database schema initialized${NC}"
        else
            echo -e "${RED}❌ Failed to initialize database schema${NC}"
            exit 1
        fi
        
        # Create R2 bucket
        echo -e "${BLUE}📦 Creating R2 storage bucket...${NC}"
        if wrangler r2 bucket create cardpress-storage; then
            echo -e "${GREEN}✅ R2 bucket created: cardpress-storage${NC}"
        else
            echo -e "${YELLOW}⚠️  R2 bucket might already exist or creation failed${NC}"
        fi
        
        # Deploy worker
        echo -e "${BLUE}⚡ Deploying Cloudflare Worker...${NC}"
        if wrangler deploy; then
            echo -e "${GREEN}✅ Worker deployed successfully${NC}"
        else
            echo -e "${RED}❌ Failed to deploy worker${NC}"
            exit 1
        fi
        
        # Create environment file
        echo -e "${BLUE}📝 Creating environment configuration...${NC}"
        cp .env_example .env
        
        # Get Cloudflare account info
        ACCOUNT_ID=$(wrangler whoami | grep "Account ID" | cut -d':' -f2 | tr -d ' ')
        
        # Update .env file
        sed -i.bak "s/your_account_id_here/${ACCOUNT_ID}/g" .env 2>/dev/null || true
        sed -i.bak "s/your_d1_database_id_here/${DB_ID}/g" .env 2>/dev/null || true
        sed -i.bak "s/your-username\/your-repo-name/${GITHUB_REPO//\//\\/}/g" .env 2>/dev/null || true
        sed -i.bak "s/gh-pages/${GITHUB_BRANCH}/g" .env 2>/dev/null || true
        sed -i.bak "s/admin@example.com/${ADMIN_EMAIL}/g" .env 2>/dev/null || true
        sed -i.bak "s/admin123/${ADMIN_PASSWORD}/g" .env 2>/dev/null || true
        
        # Create admin user
        echo -e "${BLUE}👤 Creating admin user...${NC}"
        ADMIN_ID="admin_$(date +%s)"
        BCRYPT_HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw('${ADMIN_PASSWORD}'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))")
        
        wrangler d1 execute cardpress-blog --command="
        INSERT OR REPLACE INTO users (id, email, password_hash, is_admin, created_at, updated_at) 
        VALUES ('${ADMIN_ID}', '${ADMIN_EMAIL}', '${BCRYPT_HASH}', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Admin user created successfully${NC}"
        else
            echo -e "${RED}❌ Failed to create admin user${NC}"
            exit 1
        fi
        
        # Get worker URL
        WORKER_URL=$(wrangler whoami | grep -o 'https://.*\.workers\.dev' | head -1)
        if [ -z "$WORKER_URL" ]; then
            WORKER_URL="https://cardpress-refresh.YOUR_SUBDOMAIN.workers.dev"
        fi
        
        echo ""
        echo -e "${GREEN}🎉 CardPress setup completed successfully!${NC}"
        echo -e "${GREEN}================================${NC}"
        echo ""
        echo -e "${BLUE}📋 Setup Summary:${NC}"
        echo -e "${YELLOW}   D1 Database ID:${NC} ${DB_ID}"
        echo -e "${YELLOW}   R2 Bucket:${NC} cardpress-storage"
        echo -e "${YELLOW}   Worker URL:${NC} ${WORKER_URL}"
        echo -e "${YELLOW}   GitHub Repo:${NC} ${GITHUB_REPO}"
        echo -e "${YELLOW}   Deploy Branch:${NC} ${GITHUB_BRANCH}"
        echo ""
        echo -e "${BLUE}🔐 Admin Credentials:${NC}"
        echo -e "${YELLOW}   Email:${NC} ${ADMIN_EMAIL}"
        echo -e "${YELLOW}   Password:${NC} ${ADMIN_PASSWORD}"
        echo ""
        echo -e "${BLUE}⚡ Next Steps:${NC}"
        echo -e "${YELLOW}1.${NC} Set up GitHub Personal Access Token:"
        echo -e "   ${CYAN}wrangler secret put GITHUB_TOKEN${NC}"
        echo -e "${YELLOW}2.${NC} Open admin interface:"
        echo -e "   ${CYAN}python3 -m http.server 8000${NC}"
        echo -e "   ${CYAN}open http://localhost:8000/index.html${NC}"
        echo -e "${YELLOW}3.${NC} Configure Cloudflare Pages to deploy from GitHub"
        echo ""
        echo -e "${GREEN}📖 See README.md for detailed documentation${NC}"
        ;;
        
    2)
        echo -e "${BLUE}🗄️  Creating D1 database...${NC}"
        wrangler d1 create cardpress-blog
        echo -e "${BLUE}📊 Initializing schema...${NC}"
        wrangler d1 execute cardpress-blog --file=schema.sql
        echo -e "${GREEN}✅ D1 database setup complete${NC}"
        ;;
        
    3)
        echo -e "${BLUE}📦 Creating R2 bucket...${NC}"
        wrangler r2 bucket create cardpress-storage
        echo -e "${GREEN}✅ R2 bucket setup complete${NC}"
        ;;
        
    4)
        echo -e "${BLUE}⚡ Deploying Worker...${NC}"
        wrangler deploy
        echo -e "${GREEN}✅ Worker deployment complete${NC}"
        ;;
        
    5)
        echo -e "${BLUE}🔧 Environment Configuration${NC}"
        if [ ! -f ".env" ]; then
            cp .env_example .env
            echo -e "${GREEN}✅ Created .env file from template${NC}"
        fi
        echo -e "${YELLOW}Please edit .env file with your configuration${NC}"
        echo -e "${CYAN}Required settings:${NC}"
        echo -e "  - GITHUB_TOKEN (Personal Access Token)"
        echo -e "  - GITHUB_REPO (username/repo)"
        echo -e "  - CLOUDFLARE_API_TOKEN"
        echo -e "  - D1_DATABASE_ID"
        ;;
        
    6)
        echo -e "${BLUE}🧪 Testing setup and configuration...${NC}"
        
        # Test Wrangler auth
        if wrangler whoami > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Wrangler authentication successful${NC}"
        else
            echo -e "${RED}❌ Wrangler not authenticated. Run: wrangler login${NC}"
        fi
        
        # Test D1 database
        if wrangler d1 execute cardpress-blog --command="SELECT COUNT(*) FROM users" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ D1 database accessible${NC}"
            USER_COUNT=$(wrangler d1 execute cardpress-blog --command="SELECT COUNT(*) as count FROM users WHERE is_admin=1" --json | grep -o '"count":[0-9]*' | cut -d':' -f2)
            echo -e "${BLUE}   Admin users: ${USER_COUNT}${NC}"
        else
            echo -e "${RED}❌ D1 database not accessible${NC}"
        fi
        
        # Test R2 bucket
        if wrangler r2 bucket list | grep -q "cardpress-storage"; then
            echo -e "${GREEN}✅ R2 bucket accessible${NC}"
        else
            echo -e "${RED}❌ R2 bucket not found${NC}"
        fi
        
        # Test worker deployment
        if wrangler deployments list > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Worker deployed${NC}"
        else
            echo -e "${RED}❌ Worker not deployed${NC}"
        fi
        
        echo -e "${BLUE}🔍 Configuration check complete${NC}"
        ;;
        
    7)
        echo -e "${BLUE}👤 Creating admin user...${NC}"
        
        get_input "Admin email" "admin@example.com" ADMIN_EMAIL
        get_input "Admin password (leave empty to generate)" "" ADMIN_PASSWORD
        
        if [ -z "$ADMIN_PASSWORD" ]; then
            ADMIN_PASSWORD=$(generate_password)
            echo -e "${GREEN}🔐 Generated password: ${ADMIN_PASSWORD}${NC}"
        fi
        
        ADMIN_ID="admin_$(date +%s)"
        
        # Check if Python bcrypt is available
        if ! python3 -c "import bcrypt" 2>/dev/null; then
            echo -e "${RED}❌ Python bcrypt module not found${NC}"
            echo -e "${YELLOW}   Install with: pip install bcrypt${NC}"
            exit 1
        fi
        
        BCRYPT_HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw('${ADMIN_PASSWORD}'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))")
        
        wrangler d1 execute cardpress-blog --command="
        INSERT OR REPLACE INTO users (id, email, password_hash, is_admin, created_at, updated_at) 
        VALUES ('${ADMIN_ID}', '${ADMIN_EMAIL}', '${BCRYPT_HASH}', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        
        echo -e "${GREEN}✅ Admin user created${NC}"
        echo -e "${YELLOW}   Email: ${ADMIN_EMAIL}${NC}"
        echo -e "${YELLOW}   Password: ${ADMIN_PASSWORD}${NC}"
        ;;
        
    8)
        echo -e "${YELLOW}🧹 Cleanup and reset${NC}"
        echo -e "${RED}This will delete all CardPress resources!${NC}"
        read -p "$(echo -e "${CYAN}Are you sure? (type 'DELETE' to confirm): ${NC}")" confirm
        
        if [ "$confirm" = "DELETE" ]; then
            echo -e "${BLUE}🗑️  Deleting resources...${NC}"
            
            # Delete D1 database
            wrangler d1 delete cardpress-blog || echo "Database might not exist"
            
            # Delete R2 bucket (this might fail if bucket has contents)
            wrangler r2 bucket delete cardpress-storage || echo "Bucket might not exist or has contents"
            
            # Remove local files
            rm -f .env .env.bak wrangler.toml.bak
            
            echo -e "${GREEN}✅ Cleanup complete${NC}"
            echo -e "${YELLOW}Note: You may need to manually delete the Worker from Cloudflare dashboard${NC}"
        else
            echo -e "${BLUE}Cleanup cancelled${NC}"
        fi
        ;;
        
    *)
        echo -e "${RED}❌ Invalid option. Please choose 1-8.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${PURPLE}🎯 CardPress setup script completed${NC}"
echo -e "${CYAN}📖 For detailed documentation, see: README.md${NC}" 