# vastai-connect

CLI wrapper for [Vast.ai](https://vast.ai) that simplifies GPU rental workflow. One command to search GPU, rent, ssh, then destroy the instance afterward.

## Installation

```bash
# Install vastai CLI first
uv tool install vastai
vastai set api-key <Enter your API key from https://cloud.vast.ai/manage-keys/>

# Install vastai-connect
uv tool install git+https://github.com/Yusuke710/vastai-connect.git

# Update to latest version
uv tool upgrade vastai-connect
```

## SSH Key Setup

Add your SSH public key to Vast.ai so you can connect to instances:

1. Copy your public key: `cat ~/.ssh/id_ed25519.pub` (or `~/.ssh/id_rsa.pub`)
2. Go to https://cloud.vast.ai/manage-keys/ → SSH Keys section
3. Paste your public key and save

## Usage

```bash
vastai-connect
```

This will:
1. Show available GPU instances (arrow key selection)
2. Create the selected instance
3. Wait for it to be ready
4. SSH into the instance
5. On exit, prompt to destroy the instance (default: yes)

## Configuration

The config file is bundled with the package. To find and edit it:

```bash
# Find config location
uv tool dir
# Then edit: <tool_dir>/vastai-connect/lib/python3.x/site-packages/vastai_connect/default_config.yaml
```

### Environment Variable Overrides

Override config without editing the file:

```bash
# Use VS Code/Cursor instead of SSH
VAST_MODE=ide vastai-connect

# Use Cursor as IDE
VAST_IDE=cursor vastai-connect

# Open both IDE and SSH
VAST_MODE=both vastai-connect
```

## What gets installed on the instance

Each instance [runs a startup script](src/vastai_connect/onstart.sh) that installs:
- [Claude Code](https://github.com/anthropics/claude-code)
- Alias: `claude_yolo` for running `claude --dangerously-skip-permissions`

## License 
MIT