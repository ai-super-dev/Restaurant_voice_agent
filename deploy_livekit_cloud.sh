#!/bin/bash
# Automated deployment script for LiveKit Cloud
# Usage: ./deploy_livekit_cloud.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Agent to LiveKit Cloud${NC}"
echo ""

# Check if LiveKit CLI is installed
if ! command -v lk &> /dev/null; then
    echo -e "${RED}❌ LiveKit CLI not found!${NC}"
    echo ""
    echo -e "${YELLOW}LiveKit CLI is NOT a pip package!${NC}"
    echo "Please install it using one of these methods:"
    echo ""
    echo -e "${YELLOW}macOS:${NC}"
    echo "  brew install livekit"
    echo ""
    echo -e "${YELLOW}Linux/Windows:${NC}"
    echo "  Download from: https://github.com/livekit/livekit-cli/releases"
    echo ""
    echo "After installation, run this script again."
    exit 1
fi

echo -e "${GREEN}✅ LiveKit CLI ready${NC}"
echo ""

# Check if logged in
if ! lk cloud whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to LiveKit Cloud${NC}"
    echo "Please login:"
    lk cloud login
fi

echo -e "${GREEN}✅ Authenticated with LiveKit Cloud${NC}"
echo ""

# Check for required files
echo -e "${YELLOW}Checking required files...${NC}"

if [ ! -f "agent.py" ]; then
    echo -e "${RED}❌ agent.py not found!${NC}"
    exit 1
fi

if [ ! -f "livekit-agent.yaml" ]; then
    echo -e "${RED}❌ livekit-agent.yaml not found!${NC}"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required files found${NC}"
echo ""

# Check for entrypoint function
if ! grep -q "async def entrypoint" agent.py; then
    echo -e "${RED}❌ entrypoint function not found in agent.py!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Entrypoint function found${NC}"
echo ""

# Check environment variables
echo -e "${YELLOW}Checking environment variables...${NC}"

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set in environment${NC}"
    echo "Make sure to set it in LiveKit Cloud dashboard!"
fi

echo -e "${GREEN}✅ Environment check complete${NC}"
echo ""

# Deploy
echo -e "${GREEN}📦 Deploying agent to LiveKit Cloud...${NC}"
echo ""

lk cloud deploy agent --config livekit-agent.yaml

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Check agent status in LiveKit Cloud dashboard"
echo "2. View logs: lk cloud logs agent"
echo "3. Test by calling your Twilio number"
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"

