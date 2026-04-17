#!/bin/bash
# 🔐 Secure Environment Setup Script
# Usage: bash setup-environment.sh
#
# This script helps securely set up your .env file and validate credentials.

set -e  # Exit on error

echo "🔐 Interview-ProAI Secure Environment Setup"
echo "═════════════════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists."
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file."
        exit 0
    fi
fi

# Copy template
echo "📋 Creating .env from template..."
cp .env.example .env
echo -e "${GREEN}✅ Created .env${NC}"
echo ""

# Generate SECRET_KEY
echo "🔑 Generating secure SECRET_KEY..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
# Use sed to replace (handles macOS and Linux differences)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/SECRET_KEY=dev_key_change_in_production_to_long_random_string_12345678901234567890/SECRET_KEY=$SECRET_KEY/" .env
else
    sed -i "s/SECRET_KEY=dev_key_change_in_production_to_long_random_string_12345678901234567890/SECRET_KEY=$SECRET_KEY/" .env
fi
echo -e "${GREEN}✅ Generated SECRET_KEY${NC}"
echo ""

# Prompt for configuration
echo "📝 Configure your environment:"
echo "───────────────────────────────────────────────────────────────────────"
echo ""

# Database
read -p "Database Host (default: localhost): " -e db_host
db_host=${db_host:-localhost}
read -p "Database Port (default: 5432): " -e db_port
db_port=${db_port:-5432}
read -p "Database Name (default: interview_proai): " -e db_name
db_name=${db_name:-interview_proai}
read -p "Database User (default: postgres): " -e db_user
db_user=${db_user:-postgres}
read -sp "Database Password: " db_pass
echo ""

DATABASE_URL="postgresql://$db_user:$db_pass@$db_host:$db_port/$db_name"

# Redis
echo ""
read -p "Redis URL (default: redis://localhost:6379/0): " -e redis_url
redis_url=${redis_url:-redis://localhost:6379/0}

# AI Backend
echo ""
echo "Choose primary AI backend:"
echo "1) OpenAI (GPT-3.5/4) - requires OPENAI_API_KEY"
echo "2) Anthropic Claude - requires ANTHROPIC_API_KEY"
echo "3) Google Gemini - requires GOOGLE_API_KEY"
echo "4) Local Ollama - requires OLLAMA_URL (free, runs locally)"
read -p "Choose (1-4, or press Enter to skip): " ai_choice

ai_key=""
case $ai_choice in
    1)
        read -sp "Enter OpenAI API Key (sk-...): " ai_key
        echo ""
        ;;
    2)
        read -sp "Enter Anthropic API Key (sk-ant-...): " ai_key
        echo ""
        ;;
    3)
        read -sp "Enter Google API Key (AIzaSy...): " ai_key
        echo ""
        ;;
    4)
        read -p "Enter Ollama URL (default: http://localhost:11434/api/generate): " ai_key
        ai_key=${ai_key:-http://localhost:11434/api/generate}
        ;;
esac

# Google OAuth
echo ""
read -p "Google OAuth Client ID (from Google Cloud Console): " google_client_id
read -sp "Google OAuth Client Secret: " google_client_secret
echo ""

# Update .env file
echo ""
echo "💾 Updating .env file..."

# Function to safely update .env variable
update_env() {
    local key=$1
    local value=$2
    # Escape special characters for sed
    value=$(printf '%s\n' "$value" | sed -e 's/[\/&]/\\&/g')
    if grep -q "^$key=" .env; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^$key=.*|$key=$value|" .env
        else
            sed -i "s|^$key=.*|$key=$value|" .env
        fi
    else
        echo "$key=$value" >> .env
    fi
}

update_env "DATABASE_URL" "$DATABASE_URL"
update_env "REDIS_URL" "$redis_url"

case $ai_choice in
    1)
        update_env "OPENAI_API_KEY" "$ai_key"
        ;;
    2)
        update_env "ANTHROPIC_API_KEY" "$ai_key"
        ;;
    3)
        update_env "GOOGLE_API_KEY" "$ai_key"
        ;;
    4)
        update_env "OLLAMA_URL" "$ai_key"
        ;;
esac

update_env "GOOGLE_CLIENT_ID" "$google_client_id"
update_env "GOOGLE_CLIENT_SECRET" "$google_client_secret"

echo -e "${GREEN}✅ .env file updated${NC}"
echo ""

# Install pre-commit hook
echo "🛡️  Setting up git pre-commit security hook..."
mkdir -p .git/hooks
if [ -f .git-hooks/pre-commit-secrets ]; then
    cp .git-hooks/pre-commit-secrets .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo -e "${GREEN}✅ Git pre-commit hook installed${NC}"
else
    echo -e "${YELLOW}⚠️  Pre-commit hook not found. Skipping.${NC}"
fi

echo ""
echo "───────────────────────────────────────────────────────────────────────"
echo "✅ Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Review your .env file and make sure all values are correct"
echo "2. Ensure your database and Redis are running"
echo "3. Run: python app.py"
echo ""
echo "The app will validate your environment on startup."
echo ""
echo "📖 For more information, see: CREDENTIALS_SECURITY.md"
echo ""
