"""Main CLI entry point for vastai-connect."""

import sys

import questionary

from .config import get_connect_mode, get_disk_size, load_config
from .instance import (
    create_instance, destroy_instance, get_ssh_command, open_ide,
    ssh_to_instance, update_ssh_config_for_instance, wait_for_instance, wait_for_ssh,
)
from .offers import filter_offers, search_offers, select_offer


def main() -> int:
    """Main entry point."""
    config = load_config()
    disk_size = get_disk_size(config)

    # Step 1: Search and select offer
    print("Searching for available GPU instances...")
    try:
        offers = search_offers(disk_size)
    except Exception as e:
        print(f"Error: {e}\nMake sure vastai is installed and configured (run: vastai setup <your API key>)")
        return 1

    filtered = filter_offers(offers, config["gpu_types"])
    if not filtered:
        print(f"No offers found for GPU types: {config['gpu_types']}")
        return 1

    offer = select_offer(filtered)
    if not offer:
        return 0

    # Step 2: Create instance
    print(f"\nCreating instance with {offer.get('gpu_name', 'GPU')}...")
    try:
        instance_id = create_instance(offer["id"], config["image"], disk_size)
        print(f"Instance created: {instance_id}")
    except Exception as e:
        print(f"Error creating instance: {e}")
        return 1

    return _run_session(instance_id, config)


def _run_session(instance_id: int, config: dict) -> int:
    """Run session with cleanup on exit."""
    exit_code = 0
    connect_mode = get_connect_mode(config)

    try:
        # Step 3: Wait for instance to be ready
        if not wait_for_instance(instance_id):
            print("Instance failed to start.")
            return 1

        # Step 4: Wait for SSH to be accessible
        if not wait_for_ssh(instance_id):
            print(f"SSH failed to become ready. Try manually: {' '.join(get_ssh_command(instance_id))}")
            return 1

        # Step 5: Always update SSH config so user can reconnect later
        update_ssh_config_for_instance(instance_id)

        # Step 6: Connect based on mode
        print(f"\nConnecting (mode: {connect_mode})...")

        if connect_mode in ("vscode", "cursor"):
            ide_command = "code" if connect_mode == "vscode" else "cursor"
            open_ide(ide_command)
            input("\nPress Enter when you're finished with the IDE session...")
        else:  # cli mode
            exit_code = ssh_to_instance(instance_id)
            print(f"\nSSH session ended (exit code: {exit_code})")
    except KeyboardInterrupt:
        print("\n\nInterrupted!")
        exit_code = 130
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        exit_code = 1
    finally:
        _prompt_destroy(instance_id)
    return exit_code


def _prompt_destroy(instance_id: int) -> None:
    """Prompt user to destroy instance to stop billing."""
    if questionary.confirm("Destroy instance to stop billing?", default=True).ask():
        print(f"Destroying instance {instance_id}...")
        if destroy_instance(instance_id):
            print("Instance destroyed.")
        else:
            print(f"Failed to destroy. Run: vastai destroy instance {instance_id}")
    else:
        print(f"Instance {instance_id} still running.")
        print(f"Reconnect: {' '.join(get_ssh_command(instance_id))}")
        print(f"Destroy: vastai destroy instance {instance_id}")


if __name__ == "__main__":
    sys.exit(main())
