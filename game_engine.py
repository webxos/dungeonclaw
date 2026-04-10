#!/usr/bin/env python3
"""
Game Engine for DungeonClaw v6.2 – Balanced combat, quests, economy.
"""
import sys
import json
import random
import os
import re
import copy
import subprocess
import difflib
import requests

TEMPLATES_FILE = os.getenv('TEMPLATES_FILE', './templates.json')
CRAFTING_RECIPES_FILE = os.getenv('CRAFTING_RECIPES_FILE', './crafting_recipes.json')
RANDOM_SEED = os.getenv('RANDOM_SEED')
if RANDOM_SEED:
    random.seed(int(RANDOM_SEED))

_templates = None
_crafting_recipes = None

def get_templates():
    global _templates
    if _templates is None:
        try:
            with open(TEMPLATES_FILE, 'r') as f:
                _templates = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load templates: {e}. Using fallback.", file=sys.stderr)
            _templates = {}
    return _templates

def get_crafting_recipes():
    global _crafting_recipes
    if _crafting_recipes is None:
        try:
            with open(CRAFTING_RECIPES_FILE, 'r') as f:
                _crafting_recipes = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load crafting recipes: {e}. Using empty.", file=sys.stderr)
            _crafting_recipes = {"weapons": {}, "armor": {}, "potions": {}, "permanent_potions": {}}
    return _crafting_recipes

def roll_dice(dice_notation="1d20"):
    match = re.match(r'^(\\d+)d(\\d+)([+-]\\d+)?$', dice_notation, re.I)
    if not match:
        return {"total": random.randint(1,20), "rolls": [random.randint(1,20)], "modifier": 0}
    count = int(match.group(1))
    sides = int(match.group(2))
    mod = int(match.group(3)) if match.group(3) else 0
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + mod
    return {"total": total, "rolls": rolls, "modifier": mod}

def get_zone(room_id, dungeon_size=50):
    if room_id < 13: return "entrance"
    elif room_id < 28: return "mid"
    elif room_id < 49: return "deep"
    else: return "boss"

def get_exits(room_id, dungeon_size=50):
    exits = []
    if room_id > 0: exits.append("south")
    if room_id < dungeon_size - 1: exits.append("north")
    if room_id % 7 == 0 and room_id + 7 < dungeon_size: exits.append("east")
    if room_id % 5 == 2 and room_id - 5 >= 0: exits.append("west")
    if len(exits) == 0:
        exits.append("north")
    return exits

def get_new_room_id(room_id, direction, dungeon_size):
    if direction == "north": new_room = room_id + 1
    elif direction == "south": new_room = room_id - 1
    elif direction == "east": new_room = room_id + 7
    elif direction == "west": new_room = room_id - 5
    else: return None
    if new_room < 0 or new_room >= dungeon_size: return None
    return new_room

# ---------- Minion & Monster Generation (Balanced) ----------
MINION_PREFIXES = [
    "Shadow", "Frost", "Fire", "Venom", "Bone", "Iron", "Cursed", "Raging",
    "Plague", "Void", "Doom", "Night", "Savage", "Vicious", "Ancient", "Elder",
    "Goblin", "Orc", "Uruk", "Kobold", "Hobgoblin", "Gnoll", "Troll", "Ogre"
]
MINION_SUFFIXES = [
    "Stalker", "Scavenger", "Berserker", "Warrior", "Mage", "Shaman",
    "Guardian", "Avenger", "Tyrant", "Warlord", "Champion", "Cultist",
    "Fanatic", "Prophet", "Oracle", "Hunter", "Ravager", "Devourer"
]

RARE_PREFIXES = [
    "Ancient", "Elder", "Mighty", "Savage", "Crimson", "Shadow", "Void", "Doom",
    "Frost", "Flame", "Storm", "Nightmare", "Abyssal", "Celestial", "Infernal",
    "Primal", "Titan", "Wrathful", "Glorious"
]
RARE_SUFFIXES = [
    "the Destroyer", "the Unyielding", "the Cursed", "the Eternal", "the Devourer",
    "the Forgotten", "the Awakened", "the Revenant", "the Bloody", "the Vile",
    "the King", "the Queen", "the Warlord", "the Chosen", "the Betrayer"
]

def generate_rare_name(base_name):
    if random.random() < 0.5:
        prefix = random.choice(RARE_PREFIXES)
        name = f"{prefix} {base_name}"
    else:
        name = base_name
    if random.random() < 0.6:
        suffix = random.choice(RARE_SUFFIXES)
        name = f"{name} {suffix}"
    return name

def generate_minion_name(zone, player_level):
    if random.random() < 0.3:
        base = random.choice(["Goblin", "Orc", "Uruk", "Kobold", "Gnoll", "Hobgoblin"])
        return generate_rare_name(base)
    else:
        base = random.choice(MINION_PREFIXES)
        if random.random() < 0.5:
            base += " " + random.choice(MINION_SUFFIXES)
        return base

def generate_monster(zone, player_level, is_minion=False):
    templates = get_templates()
    monsters = templates.get("monsters", [])
    if is_minion:
        # Balanced scaling: 0.7 + 0.15 per level, capped at 2.5
        factor = 0.7 + (player_level - 1) * 0.15
        factor = min(2.5, factor)
        name = generate_minion_name(zone, player_level)
        monster = {
            "name": name,
            "hp": int(10 * factor),
            "max_hp": int(10 * factor),
            "attack": 3 + player_level // 2,
            "defense": 2 + player_level // 3,
            "damage_range": [2, 6],
            "xp": int(20 + 5 * player_level),
            "gold_range": [5, 15],
            "loot_table": [{"item": {"name": "Minion Essence", "type": "misc", "value": 3}, "chance": 0.4}],  # reduced chance
            "is_minion": True
        }
    else:
        zone_monsters = [m for m in monsters if m.get("zone") == zone]
        if not zone_monsters:
            base = {"name": "Goblin", "base_hp": 10, "base_attack": 3, "base_defense": 2,
                    "damage_range": [2,6], "xp": 25, "gold_range": [5,15], "loot_table": []}
        else:
            base = random.choice(zone_monsters)
        # Normal monster scaling: 0.8 + 0.2 per level, capped at 3.0
        factor = 0.8 + (player_level - 1) * 0.2
        factor = min(3.0, factor)
        monster = {
            "name": base["name"],
            "hp": int(base.get("base_hp", 10) * factor),
            "max_hp": int(base.get("base_hp", 10) * factor),
            "attack": base.get("base_attack", 3) + player_level // 2,
            "defense": base.get("base_defense", 2) + player_level // 3,
            "damage_range": base.get("damage_range", [2,6]),
            "xp": int(base.get("xp", 25) * factor),
            "gold_range": base.get("gold_range", [5,15]),
            "loot_table": copy.deepcopy(base.get("loot_table", [])),
            "is_minion": False
        }

    if random.random() < 0.15:
        multiplier = random.uniform(1.5, 2.0)
        monster["hp"] = int(monster["hp"] * multiplier)
        monster["max_hp"] = int(monster["max_hp"] * multiplier)
        monster["attack"] = int(monster["attack"] * multiplier)
        monster["defense"] = int(monster["defense"] * multiplier)
        monster["xp"] = int(monster["xp"] * random.uniform(2.0, 3.0))
        monster["gold_range"][0] = int(monster["gold_range"][0] * 2)
        monster["gold_range"][1] = int(monster["gold_range"][1] * 2.5)
        special_loot = {
            "item": {"name": "Rare Essence", "type": "misc", "value": random.randint(50, 200)},
            "chance": 0.8
        }
        monster["loot_table"].append(special_loot)
        if random.random() < 0.5:
            rare_item = {
                "name": random.choice(["Dragon Gem", "Phoenix Feather", "Titan's Heart", "Abyssal Shard"]),
                "type": "misc",
                "value": random.randint(100, 500)
            }
            monster["loot_table"].append({"item": rare_item, "chance": 0.5})
        monster["name"] = generate_rare_name(monster["name"])
        monster["rarity"] = "rare"

    return monster

# ---------- Unique Artifact Generation ----------
ARTIFACT_PREFIXES = ["Dragon", "Phoenix", "Shadow", "Void", "Star", "Moon", "Sun", "Ancient", "Eternal", "Cursed"]
ARTIFACT_SUFFIXES = ["of Might", "of Wisdom", "of the Ancients", "of the Phoenix", "of the Void", "of the King"]

def generate_unique_item(zone, player_level):
    type_ = random.choice(["weapon", "armor"])
    if type_ == "weapon":
        name = random.choice(ARTIFACT_PREFIXES) + " " + random.choice(ARTIFACT_SUFFIXES).replace("of ", "") + " Sword"
        bonus = random.randint(2, 5) + player_level // 5
        value = 200 + bonus * 30
        return {
            "name": name,
            "type": "weapon",
            "bonus": bonus,
            "value": value,
            "consumable": False,
            "unique": True,
            "description": f"A legendary blade with +{bonus} attack and damage."
        }
    else:
        name = random.choice(ARTIFACT_PREFIXES) + " " + random.choice(ARTIFACT_SUFFIXES).replace("of ", "") + " Armor"
        bonus = random.randint(2, 5) + player_level // 5
        value = 200 + bonus * 30
        return {
            "name": name,
            "type": "armor",
            "bonus": bonus,
            "value": value,
            "consumable": False,
            "unique": True,
            "description": f"Legendary armor providing +{bonus} defense."
        }

def generate_room_mechanics(room_id, dungeon_size=50, player_level=1):
    zone = get_zone(room_id, dungeon_size)
    templates = get_templates()
    # Zone-dependent weights
    if zone == "entrance":
        type_weights = {"monster": 50, "treasure": 20, "trap": 5, "shrine": 5, "npc": 10, "empty": 10}
    elif zone == "mid":
        type_weights = {"monster": 55, "treasure": 15, "trap": 10, "shrine": 3, "npc": 7, "empty": 10}
    elif zone == "deep":
        type_weights = {"monster": 60, "treasure": 10, "trap": 15, "shrine": 2, "npc": 3, "empty": 10}
    else:  # boss
        type_weights = {"monster": 70, "treasure": 5, "trap": 20, "shrine": 0, "npc": 0, "empty": 5}
    room_type = random.choices(list(type_weights.keys()), weights=list(type_weights.values()))[0]

    desc_list = templates.get("room_descriptions", ["Room {room_id}"])
    description = random.choice(desc_list).replace("{room_id}", str(room_id))
    ambient_list = templates.get("ambient", [])
    ambient = random.choice(ambient_list) if ambient_list else ""

    monster = None
    # Minion spawn reduced to 15% of monster rooms
    if room_type == "monster" or random.random() < 0.7:
        is_minion = random.random() < 0.15
        monster = generate_monster(zone, player_level, is_minion=is_minion)

    ground_loot = generate_ground_loot(zone, player_level)
    npc = generate_npc(zone) if room_type == "npc" and random.random() < 0.5 else None
    trap = generate_trap(zone) if room_type == "trap" else None
    quest_hint = get_quest_hint(zone) if random.random() < 0.2 else None

    pending_quest = None

    # In boss zone, guarantee a mini-boss before final room
    if zone == "boss" and room_id == 48 and not monster:
        monster = generate_monster(zone, player_level, is_minion=False)
        monster["name"] = "Mini-Boss " + monster["name"]
        monster["hp"] = int(monster["hp"] * 1.5)
        monster["max_hp"] = monster["hp"]

    return {
        "room_id": room_id,
        "zone": zone,
        "type": room_type,
        "description": description,
        "ambient": ambient,
        "exits": get_exits(room_id, dungeon_size),
        "monster": monster,
        "ground_loot": ground_loot,
        "npc": npc,
        "trap": trap,
        "quest_hint": quest_hint,
        "pending_quest": pending_quest,
        "visited": False
    }

def generate_ground_loot(zone, player_level):
    templates = get_templates()
    loot_table = templates.get("ground_loot", {}).get(zone, {"items": [], "chances": []})
    if not loot_table["items"]:
        return []
    count = random.randint(1, 3)
    items = []
    for _ in range(count):
        item = random.choices(loot_table["items"], weights=loot_table["chances"])[0]
        items.append(copy.deepcopy(item))
    # Add tiered potions and materials based on zone (balanced gold values)
    if zone == "entrance":
        if random.random() < 0.3:
            items.append({"name": "Lesser Health Potion", "type": "consumable", "effect": "heal", "value": 10, "tier": "lesser", "consumable": True})
        if random.random() < 0.2:
            items.append({"name": "Herb Bundle", "type": "misc", "value": 3, "consumable": False})
    elif zone == "mid":
        if random.random() < 0.3:
            items.append({"name": "Normal Health Potion", "type": "consumable", "effect": "heal", "value": 20, "tier": "normal", "consumable": True})
        if random.random() < 0.2:
            items.append({"name": "Metal Scrap", "type": "misc", "value": 1, "consumable": False})
        if random.random() < 0.1:
            items.append({"name": "Essence", "type": "misc", "value": 5, "consumable": False})
    elif zone == "deep":
        if random.random() < 0.2:
            items.append({"name": "Greater Health Potion", "type": "consumable", "effect": "heal", "value": 40, "tier": "greater", "consumable": True})
        if random.random() < 0.1:
            items.append({"name": "Gem Shard", "type": "misc", "value": 10, "consumable": False})
        if random.random() < 0.05:
            items.append(generate_unique_item(zone, player_level))
    elif zone == "boss":
        if random.random() < 0.3:
            items.append({"name": "Superior Health Potion", "type": "consumable", "effect": "heal", "value": 70, "tier": "superior", "consumable": True})
        if random.random() < 0.1:
            items.append({"name": "Supreme Health Potion", "type": "consumable", "effect": "heal", "value": 100, "tier": "supreme", "consumable": True})
        if random.random() < 0.2:
            items.append(generate_unique_item(zone, player_level))
    return items

def generate_trap(zone):
    templates = get_templates()
    traps = templates.get("traps", [])
    zone_traps = [t for t in traps if t.get("zone") == zone] or traps
    if zone_traps:
        return random.choice(zone_traps)
    return {"name": "Pit", "effect": "damage", "save_dc": 12, "damage": 5}

def generate_npc(zone):
    templates = get_templates()
    npcs = templates.get("npcs", [])
    zone_npcs = [n for n in npcs if n.get("zone") == zone] or npcs
    if zone_npcs:
        return random.choice(zone_npcs)
    return {"name": "Mysterious Stranger", "dialogue": "Beware the shadows.", "quest_giver": False}

def get_quest_hint(zone):
    templates = get_templates()
    hints = templates.get("quest_hints", {}).get(zone, [])
    return random.choice(hints) if hints else None

# ---------- RAG Search ----------
def rag_search(query, top_k=3):
    results = []
    skill_path = os.path.join(os.path.dirname(__file__), 'SKILL.md')
    if os.path.exists(skill_path):
        with open(skill_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        scored = difflib.get_close_matches(query.lower(), [l.lower() for l in lines], n=top_k, cutoff=0.3)
        for s in scored:
            original = lines[[l.lower() for l in lines].index(s)].strip()
            if original:
                results.append({'source': 'SKILL.md', 'text': original})
    templates = get_templates()
    q_lower = query.lower()
    for key in ['items', 'monsters', 'npcs', 'quests', 'lore_fragments']:
        for item in templates.get(key, []):
            name = str(item.get('name', '')).lower()
            desc = str(item.get('description', item.get('dialogue', ''))).lower()
            if q_lower in name or q_lower in desc:
                results.append({'source': key, 'text': f"{item.get('name','?')}: {item.get('description', item.get('dialogue', ''))[:120]}"})
                if len(results) >= top_k * 2:
                    break
    return results[:top_k]

# ---------- Crafting (Updated Costs) ----------
RECIPES = {
    "Goblin Ear Potion": {
        "ingredients": [{"name": "Goblin Ear", "count": 3}],
        "result": {"name": "Goblin Ear Potion", "type": "consumable", "effect": "heal", "value": 15, "consumable": True}
    },
    "Minion Essence Potion": {
        "ingredients": [{"name": "Minion Essence", "count": 2}],
        "result": {"name": "Minion Essence Potion", "type": "consumable", "effect": "buff", "value": 2, "consumable": True}
    },
    "Silk Cloth": {
        "ingredients": [{"name": "Spider Silk", "count": 2}, {"name": "Gold Coins", "count": 5}],
        "result": {"name": "Silk Cloth", "type": "armor", "bonus": 1, "value": 15, "consumable": False}
    },
    "Orcish Elixir": {
        "ingredients": [{"name": "Orc Axe", "count": 1}, {"name": "Gold Coins", "count": 10}],
        "result": {"name": "Orcish Elixir", "type": "consumable", "effect": "heal", "value": 20, "consumable": True}
    }
}

def tool_craft(args, state):
    recipe_name = args.get("recipe_name", "").lower().strip()
    player = state["player"]
    recipe = None
    for rname, rdata in RECIPES.items():
        if rname.lower() == recipe_name:
            recipe = rdata
            break
    if not recipe:
        return {"success": False, "message": f"Unknown recipe. Known: {', '.join(RECIPES.keys())}"}
    inv = player["inventory"]
    can_craft = True
    for ing in recipe["ingredients"]:
        count_in_inv = sum(1 for i in inv if i["name"] == ing["name"])
        if count_in_inv < ing["count"]:
            can_craft = False
            break
    if not can_craft:
        return {"success": False, "message": f"Missing ingredients for {recipe_name}."}
    for ing in recipe["ingredients"]:
        removed = 0
        new_inv = []
        for i in inv:
            if i["name"] == ing["name"] and removed < ing["count"]:
                removed += 1
                continue
            new_inv.append(i)
        player["inventory"] = new_inv
    result_item = copy.deepcopy(recipe["result"])
    player["inventory"].append(result_item)
    return {"success": True, "message": f"You crafted {result_item['name']}!", "player": player, "item_used": result_item["name"]}

# ---------- Recycling (Improved Yield) ----------
def tool_recycle(args, state):
    item_name = args.get("item_name")
    player = state["player"]
    item = find_item_by_name(item_name, player["inventory"])
    if not item:
        return {"success": False, "message": f"You don't have {item_name}."}
    materials = []
    value = item.get("value", 1)
    if item["type"] in ["weapon", "armor"]:
        if "metal" in item["name"].lower() or "iron" in item["name"].lower() or "steel" in item["name"].lower():
            scrap_type = "Metal Scrap"
        else:
            scrap_type = "Leather Scrap"
        # yield more scraps: value//5 instead of //10
        count = max(1, value // 5)
        materials.append({"name": scrap_type, "count": count})
        if item.get("unique"):
            materials.append({"name": "Enchanted Dust", "count": 1})
    elif item["type"] == "consumable":
        if "potion" in item["name"].lower():
            materials.append({"name": "Herb Bundle", "count": max(1, value // 8)})
            materials.append({"name": "Essence", "count": 1})
        else:
            materials.append({"name": "Enchanted Dust", "count": max(1, value // 15)})
    else:
        materials.append({"name": "Misc Scrap", "count": 2})
    for mat in materials:
        for _ in range(mat["count"]):
            player["inventory"].append({"name": mat["name"], "type": "misc", "value": 1, "consumable": False})
    player["inventory"] = [i for i in player["inventory"] if i["name"] != item["name"]]
    material_str = ', '.join([f"{m['count']}x {m['name']}" for m in materials])
    return {"success": True, "message": f"You recycle {item['name']} and receive {material_str}.", "player": player}

# ---------- Blacksmith (Updated Upgrade Costs) ----------
def ollama_generate(prompt, system="", temperature=0.7, max_tokens=80):
    endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
    model = os.getenv("MODEL", "nemotron-3-nano:4b")
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens}
    }
    try:
        response = requests.post(endpoint, json=payload, timeout=int(os.getenv("LLM_TIMEOUT", "5000")))
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "").strip()
    except Exception as e:
        print(f"Ollama call failed: {e}", file=sys.stderr)
    return ""

def tool_blacksmith_menu(args, state):
    return {
        "success": True,
        "menu": [
            {"id": "craft_weapon", "name": "Craft Weapon", "description": "Forge a new weapon from metal scraps."},
            {"id": "craft_armor", "name": "Craft Armor", "description": "Forge new armor."},
            {"id": "upgrade_artifact", "name": "Upgrade Artifact", "description": "Enhance a unique artifact (requires materials)."},
            {"id": "recycle", "name": "Recycle Items", "description": "Break down items into crafting materials."},
            {"id": "exit", "name": "Exit", "description": "Leave the blacksmith."}
        ]
    }

def tool_blacksmith_action(args, state):
    action = args.get("action")
    player = state["player"]
    if action == "craft_weapon":
        recipes = get_crafting_recipes().get("weapons", {})
        if not recipes:
            return {"success": False, "message": "No weapon recipes available."}
        return {
            "success": True,
            "type": "craft_weapon",
            "recipes": [{"name": name, "materials": data["materials"], "gold_cost": data["gold_cost"], "result": data["result"]} for name, data in recipes.items()]
        }
    elif action == "craft_armor":
        recipes = get_crafting_recipes().get("armor", {})
        if not recipes:
            return {"success": False, "message": "No armor recipes available."}
        return {
            "success": True,
            "type": "craft_armor",
            "recipes": [{"name": name, "materials": data["materials"], "gold_cost": data["gold_cost"], "result": data["result"]} for name, data in recipes.items()]
        }
    elif action == "craft_selected":
        recipe_name = args.get("recipe_name")
        recipes = get_crafting_recipes()
        for category in ["weapons", "armor"]:
            if recipe_name in recipes.get(category, {}):
                recipe = recipes[category][recipe_name]
                inv = player["inventory"]
                for mat, count_needed in recipe["materials"].items():
                    have = sum(1 for i in inv if i["name"] == mat)
                    if have < count_needed:
                        return {"success": False, "message": f"Missing {count_needed - have} x {mat}."}
                if player["gold"] < recipe["gold_cost"]:
                    return {"success": False, "message": f"Need {recipe['gold_cost']} gold."}
                for mat, count_needed in recipe["materials"].items():
                    removed = 0
                    new_inv = []
                    for i in inv:
                        if i["name"] == mat and removed < count_needed:
                            removed += 1
                            continue
                        new_inv.append(i)
                    player["inventory"] = new_inv
                player["gold"] -= recipe["gold_cost"]
                result_item = copy.deepcopy(recipe["result"])
                player["inventory"].append(result_item)
                return {"success": True, "message": f"You craft {result_item['name']}!", "player": player}
        return {"success": False, "message": f"Unknown recipe {recipe_name}."}
    elif action == "upgrade_artifact":
        artifacts = [i for i in player["inventory"] if i.get("unique")]
        if not artifacts:
            return {"success": False, "message": "You have no artifacts to upgrade."}
        return {
            "success": True,
            "type": "upgrade_artifact",
            "artifacts": [{"name": a["name"], "upgrade_level": a.get("upgrade_level", 0), "bonus": a.get("bonus", 0)} for a in artifacts]
        }
    elif action == "upgrade_selected":
        artifact_name = args.get("artifact_name")
        artifact = None
        for i in player["inventory"]:
            if i["name"] == artifact_name and i.get("unique"):
                artifact = i
                break
        if not artifact:
            return {"success": False, "message": "Artifact not found."}
        upgrade_level = artifact.get("upgrade_level", 0)
        if upgrade_level >= 3:
            return {"success": False, "message": "This artifact is already fully upgraded."}
        # Exponential upgrade cost
        cost_gold = 150 * (upgrade_level + 1)
        cost_materials = {"Gem Shard": upgrade_level + 1, "Enchanted Dust": upgrade_level + 2}
        inv = player["inventory"]
        for mat, need in cost_materials.items():
            have = sum(1 for i in inv if i["name"] == mat)
            if have < need:
                return {"success": False, "message": f"Need {need - have} more {mat}."}
        if player["gold"] < cost_gold:
            return {"success": False, "message": f"Need {cost_gold} gold."}
        for mat, need in cost_materials.items():
            removed = 0
            new_inv = []
            for i in inv:
                if i["name"] == mat and removed < need:
                    removed += 1
                    continue
                new_inv.append(i)
            player["inventory"] = new_inv
        player["gold"] -= cost_gold
        artifact["upgrade_level"] = upgrade_level + 1
        artifact["bonus"] = artifact.get("bonus", 2) + 1
        artifact["value"] = int(artifact["value"] * 1.2)
        if player.get("weapon") and player["weapon"]["name"] == artifact_name:
            player["weapon"] = artifact
        if player.get("armor") and player["armor"]["name"] == artifact_name:
            player["armor"] = artifact
        return {"success": True, "message": f"You upgrade {artifact_name} to +{artifact['bonus']}!", "player": player}
    elif action == "recycle":
        return {
            "success": True,
            "type": "recycle",
            "items": [{"name": i["name"], "type": i["type"]} for i in player["inventory"] if i.get("type") != "misc" or i.get("value", 0) > 0]
        }
    elif action == "recycle_selected":
        return tool_recycle({"item_name": args.get("item_name")}, state)
    else:
        return {"success": False, "message": "Unknown blacksmith action."}

# ---------- Alchemist (Updated Potion Costs) ----------
def tool_alchemist_menu(args, state):
    return {
        "success": True,
        "menu": [
            {"id": "brew_potion", "name": "Brew Potion", "description": "Create a healing or buff potion."},
            {"id": "brew_permanent", "name": "Brew Permanent Potion", "description": "Craft a potion that permanently enhances your stats (rare materials)."},
            {"id": "recycle", "name": "Recycle Items", "description": "Break down items into crafting materials."},
            {"id": "exit", "name": "Exit", "description": "Leave the alchemist."}
        ]
    }

def tool_alchemist_action(args, state):
    action = args.get("action")
    player = state["player"]
    if action == "brew_potion":
        recipes = get_crafting_recipes().get("potions", {})
        if not recipes:
            return {"success": False, "message": "No potion recipes available."}
        return {
            "success": True,
            "type": "brew_potion",
            "recipes": [{"name": name, "materials": data["materials"], "gold_cost": data["gold_cost"], "result": data["result"]} for name, data in recipes.items()]
        }
    elif action == "brew_permanent":
        recipes = get_crafting_recipes().get("permanent_potions", {})
        if not recipes:
            return {"success": False, "message": "No permanent potion recipes available."}
        return {
            "success": True,
            "type": "brew_permanent",
            "recipes": [{"name": name, "materials": data["materials"], "gold_cost": data["gold_cost"], "result": data["result"], "max_consumed": data.get("max_consumed", 1)} for name, data in recipes.items()]
        }
    elif action == "brew_selected":
        recipe_name = args.get("recipe_name")
        potion_type = args.get("potion_type")
        recipes = get_crafting_recipes()
        category = "potions" if potion_type == "potion" else "permanent_potions"
        if recipe_name not in recipes.get(category, {}):
            return {"success": False, "message": f"Unknown recipe {recipe_name}."}
        recipe = recipes[category][recipe_name]
        inv = player["inventory"]
        for mat, count_needed in recipe["materials"].items():
            have = sum(1 for i in inv if i["name"] == mat)
            if have < count_needed:
                return {"success": False, "message": f"Missing {count_needed - have} x {mat}."}
        if player["gold"] < recipe["gold_cost"]:
            return {"success": False, "message": f"Need {recipe['gold_cost']} gold."}
        if potion_type == "permanent":
            consumed = player.get("consumed_permanent", [])
            if recipe_name in consumed:
                return {"success": False, "message": f"You have already consumed {recipe_name} once. Its effects are permanent and cannot be stacked."}
            max_consumed = recipe.get("max_consumed", 1)
            if len([p for p in consumed if p == recipe_name]) >= max_consumed:
                return {"success": False, "message": f"You cannot consume more than {max_consumed} of this potion."}
        for mat, count_needed in recipe["materials"].items():
            removed = 0
            new_inv = []
            for i in inv:
                if i["name"] == mat and removed < count_needed:
                    removed += 1
                    continue
                new_inv.append(i)
            player["inventory"] = new_inv
        player["gold"] -= recipe["gold_cost"]
        if potion_type == "potion":
            result_item = copy.deepcopy(recipe["result"])
            player["inventory"].append(result_item)
            return {"success": True, "message": f"You brew {result_item['name']}!", "player": player}
        else:
            effect = recipe["result"]["effect"]
            value = recipe["result"]["value"]
            if effect == "permanent_hp_boost":
                player["maxHp"] += value
                player["hp"] += value
            elif effect == "permanent_attack_boost":
                player["attack_bonus"] += value
            elif effect == "permanent_defense_boost":
                player["defense_bonus"] += value
            player.setdefault("consumed_permanent", []).append(recipe_name)
            return {"success": True, "message": f"You drink the {recipe_name} and feel a permanent change in your body!", "player": player}
    elif action == "recycle":
        return {
            "success": True,
            "type": "recycle",
            "items": [{"name": i["name"], "type": i["type"]} for i in player["inventory"] if i.get("type") != "misc" or i.get("value", 0) > 0]
        }
    elif action == "recycle_selected":
        return tool_recycle({"item_name": args.get("item_name")}, state)
    else:
        return {"success": False, "message": "Unknown alchemist action."}

# ---------- Fuzzy item finder ----------
def find_item_by_name(item_name, inventory, cutoff=0.7):
    lower_name = item_name.lower()
    exact = next((i for i in inventory if i["name"].lower() == lower_name), None)
    if exact:
        return exact
    names = [i["name"] for i in inventory]
    matches = difflib.get_close_matches(lower_name, [n.lower() for n in names], n=1, cutoff=cutoff)
    if matches:
        matched_name = next(n for n in names if n.lower() == matches[0])
        return next(i for i in inventory if i["name"] == matched_name)
    return None

# ---------- Combat Action (Overhauled: flee, defense, crits) ----------
def tool_combat_action(args, state):
    action = args.get("action")
    player = state["player"]
    mech = state["room_mechanics"]
    monster = mech.get("monster")
    if not monster or monster["hp"] <= 0:
        return {"success": False, "message": "No monster to fight."}

    for effect in player.get("effects", []):
        if effect["name"] == "poisoned":
            damage = effect.get("value", 2)
            player["hp"] -= damage
            effect["duration"] -= 1
    player["effects"] = [e for e in player["effects"] if e["duration"] > 0]

    weapon = player.get("weapon")
    damage_bonus = player.get("damage_bonus", 0) + (weapon.get("bonus", 0) if weapon else 0)
    attack_bonus = player.get("attack_bonus", 0) + (weapon.get("hit_bonus", 0) if weapon else 0)
    defense_bonus = player.get("defense_bonus", 0)
    armor = player.get("armor")
    if armor:
        defense_bonus += armor.get("bonus", 0)

    monster_name = monster["name"]

    if action == "attack":
        dice_result = roll_dice("1d20")
        roll = dice_result["total"]
        rolls = dice_result["rolls"]
        total_attack = roll + attack_bonus
        monster_ac = 10 + monster["defense"]
        if total_attack >= monster_ac:
            # Separate base dice damage from flat bonuses
            base_dice = random.randint(monster["damage_range"][0], monster["damage_range"][1])
            crit = roll == 20
            if crit:
                base_dice *= 2
                crit_msg = " Critical hit!"
            else:
                crit_msg = ""
            total_damage = base_dice + damage_bonus
            monster["hp"] -= total_damage
            msg = f"You attack the {monster_name} and hit for {total_damage} damage!{crit_msg}"
            if monster["hp"] <= 0:
                xp = monster["xp"]
                gold = random.randint(monster["gold_range"][0], monster["gold_range"][1])
                loot = []
                if monster["loot_table"]:
                    for entry in monster["loot_table"]:
                        if random.random() < entry.get("chance", 1.0):
                            loot.append(entry["item"])
                mech["monster"] = None
                player["xp"] += xp
                player["gold"] += gold
                if loot:
                    player["inventory"].extend(loot)
                msg += f" You defeated the {monster_name}! Gained {xp} XP, {gold} gold."
                if loot:
                    loot_names = ', '.join([item['name'] for item in loot])
                    msg += f" Found: {loot_names}."
                if random.random() < 0.2:
                    new_monster = generate_monster(mech["zone"], player["level"], is_minion=random.random()<0.15)
                    mech["monster"] = new_monster
                    msg += f" From the shadows, a {new_monster['name']} appears!"
                return {
                    "success": True,
                    "message": msg,
                    "player": player,
                    "updated_room_mechanics": mech,
                    "xp": xp,
                    "gold": gold,
                    "loot": loot,
                    "monster_defeated": True,
                    "monster_name": monster_name,
                    "is_minion": monster.get("is_minion", False),
                    "zone": mech["zone"],
                    "dice": {"notation": "1d20", "rolls": rolls, "total": total_attack, "modifier": attack_bonus},
                    "round_summary": {
                        "player_roll": roll, "player_hit": True,
                        "player_damage": total_damage, "critical": crit
                    }
                }
            else:
                monster_roll_obj = roll_dice("1d20")
                monster_roll = monster_roll_obj["total"]
                monster_rolls = monster_roll_obj["rolls"]
                monster_attack = monster_roll + monster["attack"]
                player_ac = 10 + defense_bonus
                monster_damage = 0
                if monster_attack >= player_ac:
                    # Defense reduces incoming damage
                    raw_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
                    monster_damage = max(1, raw_damage - defense_bonus)
                    player["hp"] -= monster_damage
                    msg += f" The {monster_name} hits you back for {monster_damage} damage!"
                else:
                    msg += f" The {monster_name} misses you."
                return {
                    "success": True,
                    "message": msg,
                    "player": player,
                    "updated_room_mechanics": mech,
                    "damage": monster_damage,
                    "dice": {"notation": "1d20", "rolls": rolls, "total": total_attack, "modifier": attack_bonus},
                    "monster_dice": {"notation": "1d20", "rolls": monster_rolls, "total": monster_attack, "modifier": monster["attack"]},
                    "round_summary": {
                        "player_roll": roll, "player_hit": True, "player_damage": total_damage,
                        "monster_roll": monster_roll, "monster_hit": monster_attack >= player_ac,
                        "monster_damage": monster_damage, "critical": crit
                    }
                }
        else:
            msg = f"You attack the {monster_name} but miss."
            monster_roll_obj = roll_dice("1d20")
            monster_roll = monster_roll_obj["total"]
            monster_rolls = monster_roll_obj["rolls"]
            monster_attack = monster_roll + monster["attack"]
            player_ac = 10 + defense_bonus
            monster_damage = 0
            if monster_attack >= player_ac:
                raw_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
                monster_damage = max(1, raw_damage - defense_bonus)
                player["hp"] -= monster_damage
                msg += f" The {monster_name} hits you for {monster_damage} damage!"
            else:
                msg += f" The {monster_name} misses you."
            return {
                "success": True,
                "message": msg,
                "player": player,
                "updated_room_mechanics": mech,
                "damage": monster_damage,
                "dice": {"notation": "1d20", "rolls": rolls, "total": total_attack, "modifier": attack_bonus},
                "monster_dice": {"notation": "1d20", "rolls": monster_rolls, "total": monster_attack, "modifier": monster["attack"]},
                "round_summary": {
                    "player_roll": roll, "player_hit": False, "player_damage": 0,
                    "monster_roll": monster_roll, "monster_hit": monster_attack >= player_ac,
                    "monster_damage": monster_damage, "fumble": roll == 1
                }
            }

    elif action == "defend":
        monster_damage = 0
        player.setdefault("effects", []).append({"name": "defending", "duration": 1, "value": 2})
        msg = "You take a defensive stance."
        monster_roll1 = roll_dice("1d20")["total"]
        monster_roll2 = roll_dice("1d20")["total"]
        monster_roll = min(monster_roll1, monster_roll2)
        monster_attack = monster_roll + monster["attack"]
        player_ac = 10 + defense_bonus + 2
        if monster_attack >= player_ac:
            raw_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
            monster_damage = max(1, raw_damage - defense_bonus)
            player["hp"] -= monster_damage
            msg += f" The {monster_name} still hits you for {monster_damage} damage!"
        else:
            msg += f" The {monster_name} misses you."
        return {
            "success": True,
            "message": msg,
            "player": player,
            "updated_room_mechanics": mech,
            "damage": monster_damage,
            "dice": {"notation": "defend (disadvantage)", "rolls": [monster_roll1, monster_roll2], "total": monster_roll, "modifier": monster["attack"]}
        }

    elif action == "use":
        item_name = args.get("item_name")
        player = state["player"]
        item = find_item_by_name(item_name, player["inventory"])
        if not item:
            return {"success": False, "message": f"You don't have {item_name}."}
        if not item.get("consumable", False) and item.get("type") != "consumable":
            return {"success": False, "message": f"{item_name} is not usable in combat."}
        effect = item.get("effect")
        if effect == "heal":
            heal_amount = calculate_heal(item, player.get("level", 1))
            max_hp = player.get("maxHp", 100)
            player["hp"] = min(max_hp, player["hp"] + heal_amount)
            msg = f"You use {item_name} and heal {heal_amount} HP."
        elif effect == "buff":
            player.setdefault("effects", []).append({"name": "blessed", "duration": 3, "value": 2})
            msg = f"You use {item_name} and feel blessed (+2 attack for 3 turns)."
        else:
            msg = f"You use {item_name} but nothing happens."
        remove_one_item(player, item)
        monster_roll_obj = roll_dice("1d20")
        monster_roll = monster_roll_obj["total"]
        monster_rolls = monster_roll_obj["rolls"]
        monster_attack = monster_roll + monster["attack"]
        player_ac = 10 + defense_bonus
        monster_damage = 0
        if monster_attack >= player_ac:
            raw_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
            monster_damage = max(1, raw_damage - defense_bonus)
            player["hp"] -= monster_damage
            msg += f" The {monster_name} hits you for {monster_damage} damage!"
        else:
            msg += f" The {monster_name} misses you."
        return {
            "success": True,
            "message": msg,
            "player": player,
            "updated_room_mechanics": mech,
            "damage": monster_damage,
            "item_used": item["name"],
            "monster_dice": {"notation": "1d20", "rolls": monster_rolls, "total": monster_attack, "modifier": monster["attack"]}
        }

    elif action == "flee":
        direction = args.get("direction")
        exits = mech.get("exits", [])
        flee_roll = roll_dice("1d20")
        # Derive monster level roughly from its attack/HP
        monster_level = max(1, monster["attack"] // 2)
        flee_bonus = (player.get("level", 1) - monster_level) * 6
        flee_total = flee_roll["total"] + max(-10, min(10, flee_bonus))
        flee_dc = 12
        if flee_total >= flee_dc:
            exit_dir = direction if direction in exits else (exits[0] if exits else None)
            if exit_dir:
                new_room = get_new_room_id(state["room"], exit_dir, state.get("dungeon_size", 50))
                new_mech = generate_room_mechanics(new_room, state.get("dungeon_size",50), player["level"])
                msg = f"You roll {flee_roll['rolls']} ({flee_total}) vs DC {flee_dc} — you flee {exit_dir}!"
                return {
                    "success": True, "message": msg,
                    "new_room": new_room, "room_mechanics": new_mech,
                    "player": player, "updated_room_mechanics": new_mech,
                    "dice": {"notation": "1d20", "rolls": flee_roll["rolls"], "total": flee_total, "modifier": flee_bonus},
                    "fled": True
                }
        raw_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
        monster_damage = max(1, raw_damage - defense_bonus)
        player["hp"] -= monster_damage
        msg = (f"You roll {flee_roll['rolls']} ({flee_total}) vs DC {flee_dc} — FAILED to flee! "
               f"The {monster['name']} strikes you for {monster_damage} damage!")
        return {
            "success": True, "message": msg, "player": player,
            "updated_room_mechanics": mech, "damage": monster_damage,
            "dice": {"notation": "1d20", "rolls": flee_roll["rolls"], "total": flee_total, "modifier": flee_bonus},
            "fled": False
        }

def calculate_heal(item, player_level):
    tier = item.get("tier", "normal")
    base_heal = item.get("value", 10)
    if tier == "lesser":
        return base_heal + player_level * 2
    elif tier == "normal":
        return base_heal + player_level * 3
    elif tier == "greater":
        return base_heal + player_level * 4
    elif tier == "superior":
        return base_heal + player_level * 5
    elif tier == "supreme":
        return base_heal + player_level * 6
    else:
        return base_heal + player_level * 2

def remove_one_item(player, item):
    for i in player["inventory"]:
        if i["name"] == item["name"] and i.get("stack", 1) > 1:
            i["stack"] -= 1
            return
    player["inventory"] = [i for i in player["inventory"] if i["name"] != item["name"]]

# ---------- Movement Tool ----------
def tool_move(args, state):
    dir = args.get("direction")
    current = state.get("room")
    if current is None:
        current = state.get("currentRoom")
    if current is None:
        return {"success": False, "message": "No current room in state."}
    dungeon_size = state.get("dungeon_size", 50)
    exits = get_exits(current, dungeon_size)
    if dir not in exits:
        return {"success": False, "message": f"Cannot go {dir}."}
    mech = state["room_mechanics"]
    if mech.get("monster") and mech["monster"]["hp"] > 0:
        return {"success": False, "message": f"A {mech['monster']['name']} blocks your way! You must defeat or flee it first."}
    new_room = get_new_room_id(current, dir, dungeon_size)
    if new_room is None:
        return {"success": False, "message": "The dungeon ends here."}
    player_level = state["player"]["level"]
    new_mech = generate_room_mechanics(new_room, dungeon_size, player_level)
    return {
        "success": True,
        "new_room": new_room,
        "room_mechanics": new_mech,
        "message": f"You move {dir} to Room {new_room}."
    }

# ---------- Other Tools (unchanged, but ensure they return proper fields) ----------
def tool_look(args, state):
    mech = state["room_mechanics"]
    desc = mech.get("description", f"You are in Room {mech['room_id']}.")
    if mech.get("ambient"):
        desc += " " + mech["ambient"]
    desc += f" Exits: {', '.join(mech['exits'])}."
    if mech.get("monster"):
        m = mech["monster"]
        desc += f" A {m['name']} (HP: {m['hp']}/{m['max_hp']}) is here!"
    if mech.get("ground_loot"):
        loot_names = [item["name"] for item in mech["ground_loot"]]
        desc += f" You see: {', '.join(loot_names)}."
    if mech.get("npc"):
        desc += f" {mech['npc']['name']} is here."
    if mech.get("quest_hint"):
        desc += f" {mech['quest_hint']}"
    return {"success": True, "description": desc, "message": desc}

def tool_search(args, state):
    mech = state["room_mechanics"]
    loot = mech.get("ground_loot", [])
    if loot:
        msg = f"You find: {', '.join([item['name'] for item in loot])}."
        player = state["player"]
        player["inventory"].extend(loot)
        mech["ground_loot"] = []
        return {
            "success": True,
            "message": msg,
            "player": player,
            "updated_room_mechanics": mech,
            "loot": loot
        }
    else:
        return {"success": True, "message": "You find nothing."}

def tool_take(args, state):
    item_name = args.get("item_name")
    mech = state["room_mechanics"]
    loot_list = mech.get("ground_loot", [])
    item = find_item_by_name(item_name, loot_list, cutoff=0.7)
    if not item:
        return {"success": False, "message": f"No {item_name} here."}
    player = state["player"]
    add_to_inventory(player, item)
    mech["ground_loot"] = [i for i in loot_list if i["name"] != item["name"]]
    return {
        "success": True,
        "message": f"You take the {item['name']}.",
        "player": player,
        "updated_room_mechanics": mech,
        "loot": [item]
    }

def add_to_inventory(player, item):
    if item.get("consumable") or item.get("type") == "misc":
        for i in player["inventory"]:
            if i["name"] == item["name"] and i.get("type") == item["type"]:
                i["stack"] = i.get("stack", 1) + 1
                return
    player["inventory"].append(item)

def tool_equip(args, state):
    item_name = args.get("item_name")
    player = state["player"]
    item = find_item_by_name(item_name, player["inventory"])
    if not item:
        return {"success": False, "message": f"You don't have {item_name}."}
    if item["type"] == "weapon":
        if player.get("weapon"):
            player["inventory"].append(player["weapon"])
        player["weapon"] = item
        player["inventory"] = [i for i in player["inventory"] if i["name"] != item["name"]]
        return {"success": True, "message": f"You equip {item['name']} as weapon.", "player": player}
    elif item["type"] == "armor":
        if player.get("armor"):
            player["inventory"].append(player["armor"])
        player["armor"] = item
        player["inventory"] = [i for i in player["inventory"] if i["name"] != item["name"]]
        return {"success": True, "message": f"You wear {item['name']}.", "player": player}
    else:
        return {"success": False, "message": f"{item['name']} cannot be equipped."}

def tool_use_out_of_combat(args, state):
    item_name = args.get("item_name")
    player = state["player"]
    item = find_item_by_name(item_name, player["inventory"])
    if not item:
        return {"success": False, "message": f"You don't have {item_name}."}
    if not item.get("consumable", False) and item.get("type") != "consumable":
        return {"success": False, "message": f"{item_name} is not usable."}
    effect = item.get("effect")
    if effect == "heal":
        heal_amount = calculate_heal(item, player.get("level", 1))
        max_hp = player.get("maxHp", 100)
        player["hp"] = min(max_hp, player["hp"] + heal_amount)
        msg = f"You use {item_name} and heal {heal_amount} HP."
    elif effect == "cure":
        player["effects"] = [e for e in player["effects"] if e["name"] not in ["poisoned", "burning", "cursed"]]
        msg = f"You use {item_name} and are cured of ailments."
    else:
        msg = f"You use {item_name} but nothing happens."
    remove_one_item(player, item)
    return {"success": True, "message": msg, "player": player, "item_used": item["name"]}

def tool_use_wrapper(args, state):
    if state.get("combat_active"):
        return tool_combat_action({"action": "use", "item_name": args.get("item_name")}, state)
    else:
        return tool_use_out_of_combat(args, state)

def tool_rest(args, state):
    # rest is now handled in JS; this is fallback
    return {"success": False, "message": "Use 'rest' command in main game."}

def tool_status(args, state):
    return {"success": True, "status": state["player"], "message": "You check your status."}

def tool_inventory(args, state):
    return {"success": True, "inventory": state["player"]["inventory"], "message": "You check your inventory."}

def tool_talk(args, state):
    mech = state["room_mechanics"]
    npc = mech.get("npc")
    if not npc:
        return {"success": False, "message": "No one here to talk to."}
    msg = npc.get("dialogue", f"{npc['name']} greets you.")
    if npc.get("quest_giver") and random.random() < 0.5 and not mech.get("pending_quest"):
        quest = generate_quest(mech["zone"], state["player"]["level"])
        if quest:
            mech["pending_quest"] = quest
            msg += f" {npc['name']} offers you a quest: {quest['name']} – {quest['description']} (Reward: {quest['reward']['gold']} gold, {quest['reward']['xp']} XP). Accept? (say 'accept quest')"
    return {"success": True, "message": msg, "updated_room_mechanics": mech}

def tool_accept_quest(args, state):
    mech = state["room_mechanics"]
    quest = mech.get("pending_quest")
    if not quest:
        return {"success": False, "message": "No quest is currently offered."}
    player_quests = state.get("quests", [])
    player_quests.append(quest)
    mech["pending_quest"] = None
    return {
        "success": True,
        "message": f"You accept the quest: {quest['name']}.",
        "quests": player_quests,
        "updated_room_mechanics": mech
    }

def tool_quest_log(args, state):
    return {"success": True, "quests": state.get("quests", []), "message": "Your quest journal."}

def tool_lore(args, state):
    return {"success": True, "lore": state.get("lore", []), "message": "Lore fragments."}

def tool_summary(args, state):
    p = state["player"]
    mech = state["room_mechanics"]
    parts = [
        f"Room {mech['room_id']} ({mech['zone']})",
        f"HP {p['hp']}/{p.get('maxHp', 100)}",
        f"Level {p['level']} (XP {p['xp']}/{p.get('xpToNext', 100)})",
    ]
    if mech.get("monster") and mech["monster"]["hp"] > 0:
        m = mech["monster"]
        parts.append(f"Monster: {m['name']} HP {m['hp']}/{m['max_hp']}")
    if mech.get("ground_loot"):
        parts.append(f"Loot visible")
    parts.append(f"Exits: {', '.join(mech.get('exits', []))}")
    if state.get("combat_active"):
        parts.append("COMBAT")
    return {"success": True, "summary": " | ".join(parts)}

def get_action_menu(state):
    actions = []
    mech = state["room_mechanics"]
    if state.get("combat_active") and mech.get("monster") and mech["monster"]["hp"] > 0:
        actions.append(("attack", "Attack"))
        actions.append(("defend", "Defend"))
        actions.append(("flee", "Flee"))
        actions.append(("use", "Use item"))
    else:
        actions.append(("look", "Look around"))
        actions.append(("inventory", "Check inventory"))
        actions.append(("status", "Show status"))
        for ex in mech.get("exits", []):
            actions.append((f"move {ex}", f"Move {ex}"))
        if mech.get("monster") and mech["monster"]["hp"] > 0:
            actions.append(("attack", f"Attack {mech['monster']['name']}"))
        if mech.get("ground_loot"):
            actions.append(("search", "Search for loot"))
        if mech.get("npc"):
            actions.append(("talk", "Talk to NPC"))
        if mech.get("pending_quest"):
            actions.append(("accept_quest", "Accept quest"))
        actions.append(("rest", "Rest"))
        actions.append(("craft", "Craft items"))
        actions.append(("recycle", "Recycle items"))
    return actions

def parse_llm_choice(text, actions):
    text = text.strip().lower()
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(actions):
            return actions[idx][0]
    for key, desc in actions:
        if key in text or text in key:
            return key
        if any(word in text for word in desc.lower().split()):
            return key
    return None

def validate_intent(tool_name, tool_args, state):
    if tool_name in ["move", "flee"]:
        direction = tool_args.get("direction")
        exits = state["room_mechanics"].get("exits", [])
        if direction and exits and direction not in exits:
            return False, f"You can't go {direction}. Available exits: {', '.join(exits)}"
    if tool_name in ["attack", "defend", "flee"]:
        monster = state["room_mechanics"].get("monster")
        if not monster or monster.get("hp", 0) <= 0:
            return False, "There is nothing to fight here."
    if tool_name == "move" and state.get("combat_active"):
        return False, "You can't leave — you're in combat! Fight or flee."
    if tool_name == "move":
        direction = tool_args.get("direction")
        exits = state["room_mechanics"].get("exits", [])
        if direction not in exits:
            return False, f"No exit to the {direction}."
        monster = state["room_mechanics"].get("monster")
        if monster and monster["hp"] > 0:
            return False, f"A {monster['name']} blocks the way! Defeat or flee it first."
        return True, ""
    elif tool_name == "attack":
        if state.get("combat_active"):
            return True, ""
        else:
            has_monster = bool(state["room_mechanics"].get("monster") and state["room_mechanics"]["monster"]["hp"] > 0)
            return has_monster, "No monster here."
    elif tool_name in ["defend", "flee"]:
        return state.get("combat_active", False), "Not in combat."
    elif tool_name in ["recycle", "blacksmith", "alchemist"]:
        return True, ""
    elif tool_name in ["take", "equip", "craft"]:
        return True, ""
    elif tool_name in ["search", "look", "status", "inventory", "rest", "talk", "quest_log", "lore", "accept_quest"]:
        return True, ""
    return False, "Unknown action."

def generate_quest(zone=None, player_level=1):
    templates = get_templates()
    quest_templates = templates.get("quest_templates", [])
    if not quest_templates:
        return None
    template = random.choice(quest_templates)
    quest = copy.deepcopy(template)
    quest["id"] = f"q_{random.randint(10000,99999)}"
    quest["reward"]["gold"] = int(quest["reward"]["gold"] * (1 + player_level/10))
    quest["reward"]["xp"] = int(quest["reward"]["xp"] * (1 + player_level/8))
    return quest

def list_models():
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return {"error": "Failed to run ollama list. Is ollama installed and in PATH?"}
        lines = result.stdout.strip().split('\\n')
        if len(lines) < 2:
            return {"models": []}
        models = []
        for line in lines[1:]:
            parts = line.split()
            if parts:
                model_name = parts[0]
                models.append(model_name)
        return {"models": models}
    except Exception as e:
        return {"error": str(e)}

def cast_spell(args, state):
    spell = args.get("spell", "").lower().strip()
    player = state["player"]
    mech = state["room_mechanics"]
    if not spell:
        return {"success": False, "message": "You didn't specify a spell."}
    if spell == "fireball":
        monster = mech.get("monster")
        if not monster or monster["hp"] <= 0:
            return {"success": False, "message": "There's no enemy to target with Fireball."}
        damage = roll_dice("4d6")["total"] + player.get("damage_bonus", 0)
        monster["hp"] -= damage
        msg = f"You cast Fireball! The {monster['name']} takes {damage} damage."
        if monster["hp"] <= 0:
            msg += " It is consumed by flames and defeated!"
            mech["monster"] = None
            xp = monster.get("xp", 50)
            gold = random.randint(monster.get("gold_range", [5,15])[0], monster.get("gold_range", [5,15])[1])
            player["xp"] += xp
            player["gold"] += gold
            msg += f" You gain {xp} XP and {gold} gold."
            if monster.get("loot_table"):
                loot = []
                for entry in monster["loot_table"]:
                    if random.random() < entry.get("chance", 1.0):
                        loot.append(entry["item"])
                if loot:
                    player["inventory"].extend(loot)
                    msg += f" You find: {', '.join(i['name'] for i in loot)}."
            return {
                "success": True,
                "message": msg,
                "player": player,
                "updated_room_mechanics": mech,
                "monster_defeated": True,
                "monster_name": monster["name"],
                "xp": xp,
                "gold": gold,
                "loot": loot if 'loot' in locals() else []
            }
        else:
            monster_roll = roll_dice("1d20")["total"] + monster["attack"]
            player_ac = 10 + player.get("defense_bonus", 0)
            if monster_roll >= player_ac:
                monster_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
                player["hp"] -= monster_damage
                msg += f" The {monster['name']} retaliates and hits you for {monster_damage} damage!"
            else:
                msg += f" The {monster['name']} misses you."
            return {
                "success": True,
                "message": msg,
                "player": player,
                "updated_room_mechanics": mech,
                "damage": monster_damage if 'monster_damage' in locals() else 0
            }
    elif spell == "heal":
        heal_amount = roll_dice("2d4")["total"] + player.get("damage_bonus", 0)
        player["hp"] = min(player.get("maxHp", 100), player["hp"] + heal_amount)
        msg = f"You cast Heal and restore {heal_amount} HP."
        return {"success": True, "message": msg, "player": player, "heal": heal_amount}
    elif spell == "cure":
        player["effects"] = [e for e in player["effects"] if e["name"] not in ["poisoned", "burning", "cursed"]]
        msg = "You cast Cure and are relieved of ailments."
        return {"success": True, "message": msg, "player": player}
    else:
        msg = f"You cast {spell.capitalize()}, but nothing seems to happen (spell not implemented)."
        return {"success": False, "message": msg, "player": player}

def generate_arc(args):
    player_name = args.get("player_name", "Adventurer")
    player_level = args.get("player_level", 1)
    zone = args.get("zone", "entrance")
    templates = get_templates()
    story_gen_path = os.path.join(os.path.dirname(__file__), "story_gen.py")
    if os.path.exists(story_gen_path):
        try:
            result = subprocess.run(
                ["python3", story_gen_path, "generate_arc", json.dumps({
                    "player_name": player_name,
                    "player_level": player_level,
                    "zone": zone
                })],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
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

# ---------- Tool Dispatch ----------
TOOLS = {
    "move": {"func": tool_move, "args": ["direction"]},
    "look": {"func": tool_look, "args": []},
    "attack": {"func": tool_combat_action, "args": ["action"]},
    "defend": {"func": tool_combat_action, "args": ["action"]},
    "flee": {"func": tool_combat_action, "args": ["action"]},
    "use": {"func": tool_use_wrapper, "args": ["item_name"]},
    "craft": {"func": tool_craft, "args": ["recipe_name"]},
    "recycle": {"func": tool_recycle, "args": ["item_name"]},
    "blacksmith_menu": {"func": tool_blacksmith_menu, "args": []},
    "blacksmith_action": {"func": tool_blacksmith_action, "args": ["action"]},
    "alchemist_menu": {"func": tool_alchemist_menu, "args": []},
    "alchemist_action": {"func": tool_alchemist_action, "args": ["action"]},
    "search": {"func": tool_search, "args": []},
    "take": {"func": tool_take, "args": ["item_name"]},
    "equip": {"func": tool_equip, "args": ["item_name"]},
    "rest": {"func": tool_rest, "args": []},
    "status": {"func": tool_status, "args": []},
    "inventory": {"func": tool_inventory, "args": []},
    "talk": {"func": tool_talk, "args": []},
    "accept_quest": {"func": tool_accept_quest, "args": []},
    "quest_log": {"func": tool_quest_log, "args": []},
    "lore": {"func": tool_lore, "args": []},
    "summary": {"func": tool_summary, "args": []},
    "roll_dice": {"func": lambda args, state: roll_dice(args.get("dice", "1d20")), "args": ["dice"]},
    "cast_spell": {"func": cast_spell, "args": ["spell"]},
    "generate_arc": {"func": generate_arc, "args": []},
}

def main():
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No command specified"}))
            sys.exit(1)

        command = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

        if command == "generate_room":
            room_id = args.get("room", 0)
            dungeon_size = args.get("dungeon_size", 50)
            player_level = args.get("player_level", 1)
            print(json.dumps(generate_room_mechanics(room_id, dungeon_size, player_level)))

        elif command == "execute_tool":
            tool_name = args.get("tool")
            tool_args = args.get("args", {})
            state = args.get("state", {})
            if tool_name not in TOOLS:
                print(json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"}))
                return
            tool = TOOLS[tool_name]
            if tool_name in ["attack", "defend", "flee"] and "action" not in tool_args:
                tool_args["action"] = tool_name
            missing = [arg for arg in tool["args"] if arg not in tool_args]
            if missing:
                print(json.dumps({"success": False, "error": f"Missing args: {missing}"}))
                return
            result = tool["func"](tool_args, state)
            print(json.dumps(result))

        elif command == "get_action_menu":
            state = args.get("state")
            print(json.dumps({"menu": get_action_menu(state)}))

        elif command == "parse_llm_choice":
            text = args.get("text")
            actions = args.get("actions")
            choice = parse_llm_choice(text, actions)
            print(json.dumps({"choice": choice}))

        elif command == "validate_intent":
            tool_name = args.get("tool")
            tool_args = args.get("args", {})
            state = args.get("state", {})
            valid, reason = validate_intent(tool_name, tool_args, state)
            print(json.dumps({"valid": valid, "reason": reason}))

        elif command == "tool_summary":
            state = args.get("state")
            print(json.dumps(tool_summary(state)))

        elif command == "list_models":
            result = list_models()
            print(json.dumps(result))

        elif command == "rag_search":
            query = args.get("query", "")
            top_k = args.get("top_k", 3)
            results = rag_search(query, top_k)
            print(json.dumps({"results": results}))

        elif command == "roll_dice":
            dice = args.get("dice", "1d20")
            result = roll_dice(dice)
            print(json.dumps(result))

        elif command == "cast_spell":
            result = cast_spell(args, args.get("state", {}))
            print(json.dumps(result))

        elif command == "generate_arc":
            arc = generate_arc(args)
            print(json.dumps(arc))

        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
    except Exception as e:
        import traceback
        print(f"Unhandled exception in game_engine.py: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": str(e)}))

if __name__ == '__main__':
    main()
