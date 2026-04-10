#!/usr/bin/env python3
"""
story_gen.py – Generates unique adventure arcs using templates (no LLM required).
Called by dungeonclaw.js at game start.
"""
import json
import sys
import random
import os

def generate_arc_templates(player_name, player_level, zone, templates):
    hooks = [
        f"A cursed artifact has been stolen from the {zone} shrine.",
        f"The dungeon's guardian, a legendary beast, has awakened.",
        f"A merchant caravan was attacked; the survivors beg {player_name} for help.",
        f"Strange runes appeared overnight — someone is opening a portal.",
        f"A rival adventurer challenges {player_name} to a race for the vault.",
    ]
    quests_raw = templates.get("quests", [])
    zone_quests = [q for q in quests_raw if q.get("zone") == zone] or quests_raw
    selected = random.sample(zone_quests, min(3, len(zone_quests)))
    arc = {
        "hook": random.choice(hooks),
        "quests": selected,
        "theme": random.choice(["revenge", "discovery", "survival", "honor", "greed"]),
        "villain": {
            "name": random.choice(["Lord Vexar", "The Pale Witch", "Commander Drek", "The Faceless One"]),
            "motive": random.choice(["power", "immortality", "revenge", "chaos"])
        }
    }
    return arc

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command specified"}))
        sys.exit(1)

    command = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    templates_file = os.getenv("TEMPLATES_FILE", "./templates.json")
    with open(templates_file) as f:
        templates = json.load(f)

    if command == "generate_arc":
        arc = generate_arc_templates(
            args.get("player_name", "Adventurer"),
            args.get("player_level", 1),
            args.get("zone", "entrance"),
            templates
        )
        print(json.dumps(arc))
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
