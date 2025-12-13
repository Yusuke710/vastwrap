"""Search and filter GPU offers from vastai."""

import json
import re
import subprocess

import questionary


def search_offers(disk_size: int = 10) -> list[dict]:
    """Search for available GPU offers using vastai CLI."""
    result = subprocess.run(
        ["vastai", "search", "offers", "--storage", str(disk_size), "--raw"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to search offers: {result.stderr}")
    return json.loads(result.stdout)


def format_offer(o: dict) -> str:
    """Format offer as 'RTX 4090 (24GB) - $0.28/hr'."""
    n, name = o.get("num_gpus", 1), o.get("gpu_name", "Unknown")
    ram, price = int(o.get("gpu_ram", 0) / 1024), o.get("dph_total", 0)
    return f"{f'{n}x{name}' if n > 1 else name} ({ram}GB) - ${price:.2f}/hr"


def filter_offers(offers: list[dict], gpu_types: list[str]) -> list[dict]:
    """Filter by GPU type, dedupe to cheapest per config, sort by price."""
    def matches(name: str) -> bool:
        return any(re.search(rf"\b{re.escape(g)}\b", name, re.IGNORECASE) for g in gpu_types)

    seen, result = set(), []
    for o in sorted((o for o in offers if matches(o.get("gpu_name", ""))),
                    key=lambda x: x.get("dph_total", float("inf"))):
        key = format_offer(o).rsplit(" - ", 1)[0]
        if key not in seen:
            seen.add(key)
            result.append(o)
    return result


def select_offer(offers: list[dict]) -> dict | None:
    """Display offers and let user select one with arrow keys."""
    if not offers:
        print("No offers found matching your GPU filters.")
        return None
    choices = [questionary.Choice(title=format_offer(o), value=o) for o in offers[:20]]
    return questionary.select("Select a GPU instance:", choices=choices).ask()
