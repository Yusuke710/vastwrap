#!/bin/bash
# Startup script for vast.ai instances

# Source nvm to get npm in PATH (onstart runs without .bashrc)
source /opt/nvm/nvm.sh

npm install -g @anthropic-ai/claude-code
echo "alias claude_yolo='IS_SANDBOX=1 claude --dangerously-skip-permissions'" >> ~/.bashrc
