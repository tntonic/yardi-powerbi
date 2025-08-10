#!/bin/bash

# Claude-Flow Swarm Initialization for Power BI Yardi Project
# ============================================================

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Please set ANTHROPIC_API_KEY in .env file first"
    echo "   Get your key from: https://console.anthropic.com/settings/keys"
    exit 1
fi

# Load environment variables
export $(cat .env | xargs)

echo "🚀 Initializing Claude-Flow Swarm for Power BI Development..."
echo "=================================================="
echo "Topology: Hierarchical"
echo "Max Agents: 8"
echo "Strategy: Parallel"
echo "Memory: Enabled"
echo ""

# Initialize swarm with configuration
npx claude-flow swarm init \
    --topology hierarchical \
    --max-agents 8 \
    --strategy parallel \
    --memory \
    --auto-spawn

# Check if initialization succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Swarm initialized successfully!"
    echo ""
    echo "🤖 Spawning specialized agents for Power BI tasks..."
    
    # Spawn critical agents for Power BI validation
    npx claude-flow agent spawn powerbi-dax-validator --name "DAX-Validator"
    npx claude-flow agent spawn powerbi-measure-accuracy-tester --name "Accuracy-Tester"
    npx claude-flow agent spawn powerbi-yardi-amendment-validator --name "Amendment-Validator"
    npx claude-flow agent spawn powerbi-test-orchestrator --name "Test-Orchestrator"
    
    echo ""
    echo "📊 Ready for Power BI development tasks!"
    echo ""
    echo "Next steps:"
    echo "1. Run validation: npx claude-flow task create validation 'Validate all 122 DAX measures'"
    echo "2. Test accuracy: npx claude-flow task create testing 'Test rent roll accuracy against Yardi'"
    echo "3. Check status: npx claude-flow swarm status"
else
    echo "❌ Swarm initialization failed. Please check your API key and try again."
fi