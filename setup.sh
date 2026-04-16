#!/bin/bash
# setup.sh - Quick setup script for Interview-ProAI
# Usage: chmod +x setup.sh && ./setup.sh

set -e  # Exit on error

echo "╔═════════════════════════════════════════════════════════╗"
echo "║    Interview-ProAI Setup (PostgreSQL + SQLAlchemy)     ║"
echo "╚═════════════════════════════════════════════════════════╝"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}📋 Creating .env from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env with your credentials!${NC}"
        exit 1
    else
        echo -e "${RED}❌ .env.example not found!${NC}"
        exit 1
    fi
fi

# Load environment
export $(cat .env | grep -v '#' | xargs)

# Check PostgreSQL
echo -e "\n${YELLOW}🔍 Checking PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL not installed!${NC}"
    echo "   macOS: brew install postgresql"
    echo "   Ubuntu: sudo apt-get install postgresql"
    echo "   Or use Docker: docker-compose up -d"
    exit 1
fi

# Install dependencies
echo -e "\n${YELLOW}📦 Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Initialize database
echo -e "\n${YELLOW}🗄️  Initializing database...${NC}"
python -c "from app import db, app; app.app_context().push(); db.create_all()" && \
    echo -e "${GREEN}✅ Database initialized${NC}" || \
    echo -e "${RED}❌ Database initialization failed${NC}"

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "\nStart server: ${YELLOW}python app.py${NC}"
echo -e "Visit: ${YELLOW}http://localhost:5000${NC}"
