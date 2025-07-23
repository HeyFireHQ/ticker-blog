#!/bin/bash

# CardPress Deployment Script
# This script helps deploy Firebase rules and run the blog generator

set -e  # Exit on any error

echo "🚀 CardPress Deployment Script"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Firebase CLI is installed
check_firebase_cli() {
    if ! command -v firebase &> /dev/null; then
        print_error "Firebase CLI not found. Please install it first:"
        echo "npm install -g firebase-tools"
        exit 1
    fi
    print_success "Firebase CLI is installed"
}

# Check if logged into Firebase
check_firebase_auth() {
    if ! firebase projects:list &> /dev/null; then
        print_error "Not logged into Firebase. Please run:"
        echo "firebase login"
        exit 1
    fi
    print_success "Firebase authentication verified"
}

# Deploy Firebase rules
deploy_rules() {
    print_status "Deploying Firebase rules..."
    
    # Move to project root for Firebase deployment
    original_dir=$(pwd)
    cd ..
    
    # Deploy both Firestore and Storage rules together
    if [ -f "cardpress/firestore.rules" ] && [ -f "cardpress/storage.rules" ]; then
        print_status "Deploying Firestore and Storage rules..."
        firebase deploy --only firestore:rules,storage
        print_success "Firebase rules deployed"
    else
        print_warning "Rules files not found, skipping..."
    fi
    
    # Return to original directory
    cd "$original_dir"
}

# Run the blog generator
run_generator() {
    print_status "Running Firebase to Pelican generator..."
    
    # Check if Python script exists
    if [ -f "firebase_to_pelican.py" ]; then
        # Check if virtual environment exists and activate it
        if [ -d "../venv/bin" ]; then
            print_status "Activating virtual environment..."
            source ../venv/bin/activate
        else
            print_warning "Virtual environment not found. Make sure Python dependencies are installed:"
            print_warning "pip install -r requirements.txt"
        fi
        
        # Try python3 first, then python
        if command -v python3 &> /dev/null; then
            python3 firebase_to_pelican.py
        elif command -v python &> /dev/null; then
            python firebase_to_pelican.py
        else
            print_error "Python not found. Please install Python 3."
            exit 1
        fi
        print_success "Blog generation completed"
    else
        print_error "firebase_to_pelican.py not found"
        exit 1
    fi
}

# Start local server for admin interface
start_server() {
    print_status "Starting local server for admin interface..."
    print_status "Access admin interface at: http://localhost:8000/cardpress/"
    print_warning "Press Ctrl+C to stop the server"
    
    cd ..
    # Try python3 first, then python
    if command -v python3 &> /dev/null; then
        python3 -m http.server 8000
    elif command -v python &> /dev/null; then
        python -m http.server 8000
    else
        print_error "Python not found. Please install Python 3."
        exit 1
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "Choose an option:"
    echo "1) Deploy Firebase rules only"
    echo "2) Run blog generator only"
    echo "3) Deploy rules + run generator"
    echo "4) Start local admin server"
    echo "5) Full setup (rules + generator + server)"
    echo "6) Exit"
    echo ""
}

# Main execution
main() {
    # Navigate to cardpress directory
    cd "$(dirname "$0")"
    
    # Check prerequisites
    check_firebase_cli
    check_firebase_auth
    
    # Show menu if no arguments provided
    if [ $# -eq 0 ]; then
        show_menu
        read -p "Enter your choice (1-6): " choice
    else
        choice=$1
    fi
    
    case $choice in
        1)
            deploy_rules
            ;;
        2)
            run_generator
            ;;
        3)
            deploy_rules
            run_generator
            ;;
        4)
            start_server
            ;;
        5)
            deploy_rules
            run_generator
            echo ""
            print_status "Setup complete! Starting server..."
            sleep 2
            start_server
            ;;
        6)
            print_status "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please select 1-6."
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 