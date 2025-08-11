#!/bin/bash

# Claude Flow Swarm Startup Script
echo "🐝 Claude Flow Swarm Launcher"
echo "==============================="

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
        echo "To set your API key:"
        echo "  1. Copy .env.example to .env"
        echo "  2. Add your API key to .env"
        echo "  3. Or export ANTHROPIC_API_KEY=your-key-here"
        echo ""
    fi
fi

# Start the swarm with configuration
echo "🚀 Starting Claude Flow Swarm..."
echo "Configuration:"
echo "  - Topology: hierarchical"
echo "  - Max Agents: 8"
echo "  - Strategy: parallel"
echo "  - Auto-spawn: enabled"
echo "  - Memory persistence: enabled"
echo ""

# Initialize swarm
./claude-flow swarm init \
    --topology hierarchical \
    --max-agents 8 \
    --strategy parallel \
    --auto-spawn \
    --memory

# Start orchestration system
echo ""
echo "Starting orchestration system..."
./claude-flow start --ui --port 3000 &

# Show status
sleep 2
echo ""
echo "📊 Current Status:"
./claude-flow status

echo ""
echo "✅ Swarm is ready!"
echo "🌐 Web UI available at: http://localhost:3000"
echo ""
echo "📋 Quick Commands:"
echo "  ./claude-flow agent spawn <type>  - Spawn a new agent"
echo "  ./claude-flow task create <task>  - Create a new task"
echo "  ./claude-flow swarm status        - Check swarm status"
echo "  ./claude-flow monitor             - Real-time monitoring"
echo ""