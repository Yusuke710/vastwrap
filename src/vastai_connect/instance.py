"""Instance management - create, wait, ssh, destroy."""

import json
import re
import subprocess
import time
from pathlib import Path

from .config import get_startup_script

SSH_CONFIG_HOST = "vast-gpu"


def create_instance(offer_id: int, image: str) -> int:
    """Create a new instance and return the instance ID."""
    onstart_cmd = get_startup_script()

    result = subprocess.run(
        [
            "vastai",
            "create",
            "instance",
            str(offer_id),
            "--image",
            image,
            "--onstart-cmd",
            onstart_cmd,
            "--ssh",
            "--raw",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to create instance: {result.stderr}")

    # Parse the response to get instance ID
    data = json.loads(result.stdout)
    if "new_contract" in data:
        return data["new_contract"]
    raise RuntimeError(f"Unexpected response: {result.stdout}")


def wait_for_instance(instance_id: int, timeout: int = 300) -> bool:
    """Wait for instance to be running. Returns True when ready."""
    print(f"Waiting for instance {instance_id} to start...", end="", flush=True)
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = subprocess.run(
            ["vastai", "show", "instances", "--raw"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            instances = json.loads(result.stdout)
            for instance in instances:
                if instance.get("id") == instance_id:
                    status = instance.get("actual_status", "")
                    if status == "running":
                        print(" Ready!")
                        return True

        print(".", end="", flush=True)
        time.sleep(5)

    print(" Timeout!")
    return False


def get_ssh_command(instance_id: int) -> list[str]:
    """Get the SSH command for connecting to an instance."""
    result = subprocess.run(
        ["vastai", "ssh-url", str(instance_id)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to get SSH URL: {result.stderr}")

    # Output is like: ssh://root@ssh6.vast.ai:17538
    ssh_url = result.stdout.strip()

    # Parse ssh:// URL into ssh command args
    if ssh_url.startswith("ssh://"):
        # ssh://root@ssh6.vast.ai:17538 -> ssh -p 17538 root@ssh6.vast.ai
        url = ssh_url[6:]  # Remove "ssh://"
        user_host, port = url.rsplit(":", 1)
        return ["ssh", "-p", port, user_host]

    # Fallback: assume it's already in "ssh -p PORT user@host" format
    return ssh_url.split()


def wait_for_ssh(instance_id: int, timeout: int = 180) -> bool:
    """Wait for SSH to be actually accessible. Returns True when ready."""
    print("Waiting for SSH to be ready...", end="", flush=True)
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            ssh_cmd = get_ssh_command(instance_id)
            result = subprocess.run(
                ssh_cmd + ["-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new",
                           "-o", "BatchMode=yes", "exit", "0"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                print(" Ready!")
                return True
            if "Permission denied" in result.stderr:
                print(" Authentication failed! Check your SSH key configuration.")
                return False
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(3)

    print(" Timeout!")
    return False


def ssh_to_instance(instance_id: int) -> int:
    """SSH into the instance. Returns the exit code."""
    ssh_cmd = get_ssh_command(instance_id)
    print(f"Connecting: {' '.join(ssh_cmd)}")

    # Use subprocess.call to let SSH take over the terminal
    return subprocess.call(ssh_cmd)


def destroy_instance(instance_id: int) -> bool:
    """Destroy an instance. Returns True on success."""
    result = subprocess.run(
        ["vastai", "destroy", "instance", str(instance_id)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def update_ssh_config_for_instance(instance_id: int) -> None:
    """Update ~/.ssh/config with instance details for easy reconnection."""
    ssh_cmd = get_ssh_command(instance_id)
    # ssh_cmd is like: ["ssh", "-p", "17538", "root@ssh6.vast.ai"]
    port = ssh_cmd[2]
    user, host = ssh_cmd[3].split("@")

    # Validate inputs (no whitespace/newlines that could inject config)
    for name, val in [("host", host), ("user", user), ("port", port)]:
        if not val or any(c in val for c in " \t\n\r"):
            raise ValueError(f"Invalid SSH {name}: {val!r}")

    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    config_path = ssh_dir / "config"
    tmp_path = ssh_dir / "config.tmp"

    new_block = f"""Host {SSH_CONFIG_HOST}
    HostName {host}
    Port {port}
    User {user}
    StrictHostKeyChecking accept-new
"""

    if config_path.exists():
        content = config_path.read_text()
        pattern = rf"Host {SSH_CONFIG_HOST}\n(?:[ \t]+\S+.*\n)*"
        if re.search(pattern, content):
            content = re.sub(pattern, new_block, content)
        else:
            content = content.rstrip() + "\n\n" + new_block
    else:
        content = new_block

    # Atomic write + always enforce permissions
    tmp_path.write_text(content)
    tmp_path.chmod(0o600)
    tmp_path.rename(config_path)

    print(f"SSH config updated: ssh {SSH_CONFIG_HOST}")


def open_ide(ide_command: str) -> bool:
    """Open IDE with remote SSH connection. Returns True on success.

    Assumes update_ssh_config_for_instance() was already called.
    """
    # Use SSH config alias - VS Code reads port from config
    cmd = [ide_command, "--remote", f"ssh-remote+{SSH_CONFIG_HOST}", "/root"]

    print(f"Opening {ide_command}: {' '.join(cmd)}")
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        print(f"Error: '{ide_command}' not found. Install it or add to PATH.")
        return False
