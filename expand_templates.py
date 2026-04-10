#!/usr/bin/env python3
"""
expand_templates.py – Expands DungeonClaw templates to 2000+ lines (v5.1).
Run this ONCE to generate the huge templates.json file.
All existing fields are preserved and multiplied.
"""
import json
import random
import copy
import sys
import os

# Add the current directory to path to import from templates.py
sys.path.append(os.path.dirname(__file__))
try:
    from templates import BASE, expand_list, expand_monsters, expand_items, expand_ground_loot, expand_traps, expand_npcs, expand_quest_hints, expand_quests, expand_lore
except ImportError:
    # Fallback: define the base from the final templates.json we generated earlier (but that's huge).
    print("Error: Could not import BASE from templates.py. Please ensure templates.py is in the same directory.")
    sys.exit(1)

def build_mega_expanded():
    templates = copy.deepcopy(BASE)
    # Expand descriptive lists to ~800 items (double of 400)
    for key in ["room_descriptions", "ambient", "action_responses", "monster_encounters",
                "loot_descriptions", "combat_responses", "trap_responses", "npc_dialogues",
                "riddles", "prophecies", "magical_events", "model_unavailable"]:
        if key in templates:
            templates[key] = expand_list(templates[key], target_min=800)  # double again
    # Expand structured data with even larger targets
    templates["monsters"] = expand_monsters(templates["monsters"], target=200)  # double
    templates["items"] = expand_items(templates["items"], target=400)           # double
    templates["ground_loot"] = expand_ground_loot(templates["ground_loot"])
    templates["traps"] = expand_traps(templates["traps"], target=120)          # double
    templates["npcs"] = expand_npcs(templates["npcs"], target=160)             # double
    templates["quest_hints"] = expand_quest_hints(templates["quest_hints"])
    templates["quests"] = expand_quests(templates["quests"], target=80)        # double
    templates["lore_fragments"] = expand_lore(templates["lore_fragments"], target=200)  # double
    # Expand nli_fallback_messages further
    for tool, msgs in templates["nli_fallback_messages"].items():
        expanded_msgs = msgs[:]
        for _ in range(40):
            for m in msgs:
                new_m = m + " " + random.choice(["The dungeon hums.", "Shadows flicker.", "You feel a chill.", "Mystic energy swirls.", "An unseen presence watches.", "Time seems to slow.", "A distant roar echoes.", "Magic crackles in the air."])
                if new_m not in expanded_msgs:
                    expanded_msgs.append(new_m)
        templates["nli_fallback_messages"][tool] = expanded_msgs[:60]
    return templates

if __name__ == "__main__":
    random.seed(42)  # for reproducibility
    expanded = build_mega_expanded()
    with open("templates.json", "w") as f:
        json.dump(expanded, f, indent=2, ensure_ascii=False)
    print("Mega templates.json generated with", sum(len(v) if isinstance(v, list) else 1 for v in expanded.values()), "total items.")
