# vastai-connect

CLI wrapper for [Vast.ai](https://vast.ai) that simplifies GPU rental workflow. One command to search GPU, rent, ssh, then destroy the instance afterward.

## Installation

```bash
# Install vastai CLI first
uv add vastai
vastai setup <Enter your API key from VastAI console>  

# Install vastai-connect
git@github.com:Yusuke710/vastai-connect.git
uv sync
```

## SSH Key Setup

Add your SSH public key to Vast.ai so you can connect to instances:

1. Copy your public key: `cat ~/.ssh/id_ed25519.pub` (or `~/.ssh/id_rsa.pub`)
2. Go to https://cloud.vast.ai/account/ → SSH Keys section
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

Customize the [config](src/vastai_connect/default_config.yaml) file to set GPU types you want to rent and the Docker image for the instance:

```yaml
gpu_types:
  - RTX 3090
  - RTX 4090
  - A100
  - H100
  - H200

image: vastai/pytorch:latest
```

## What gets installed on the instance

Each instance [runs a startup script](src/vastai_connect/onstart.sh) that installs:
- [Claude Code](https://github.com/anthropics/claude-code)
- Alias: `claude_yolo` for running `claude --dangerously-skip-permissions`
