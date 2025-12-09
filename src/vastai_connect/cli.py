"""Main CLI entry point for vastai-connect."""

import sys

import questionary

from .config import load_config
from .instance import (
    create_instance, destroy_instance, get_ssh_command,
    ssh_to_instance, wait_for_instance, wait_for_ssh,
)
from .offers import filter_offers, search_offers, select_offer


def main() -> int:
    """Main entry point."""
    config = load_config()

    # Step 1: Search and select offer
    print("Searching for available GPU instances...")
    try:
        offers = search_offers()
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
        instance_id = create_instance(offer["id"], config["image"])
        print(f"Instance created: {instance_id}")
    except Exception as e:
        print(f"Error creating instance: {e}")
        return 1

    return _run_session(instance_id)


def _run_session(instance_id: int) -> int:
    """Run SSH session with cleanup on exit."""
    exit_code = 0
    try:
        # Step 3: Wait for instance to be ready
        if not wait_for_instance(instance_id):
            print("Instance failed to start.")
            return 1

        # Step 4: Wait for SSH to be accessible
        if not wait_for_ssh(instance_id):
            print(f"SSH failed to become ready. Try manually: {' '.join(get_ssh_command(instance_id))}")
            return 1

        # Step 5: SSH into instance
        print("\nConnecting to instance...")
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
