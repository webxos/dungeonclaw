# DungeonClaw v6.2 (Under Development)

[![Follow on X](https://img.shields.io/badge/Follow_@dungeonclaw-1DA1F2?style=for-the-badge&logo=x&logoColor=white)](https://x.com/dungeonclaw)

![Alt Text](https://github.com/webxos/dungeonclaw/blob/main/assets/logo.jpeg)

**An Epic Fantasy AI Dungeon Master – Full RPG with TUI, quests, crafting, and local LLM integration.**

DungeonClaw is a terminal‑based, single‑player role‑playing agent harness that turns your local Ollama model into a Dungeon Master with generated dungeon, fight monsters, complete quests, craft gear, and shape your character’s story – all guided by a robust Python game engine.

> **Latest version v6.2** includes a complete balance overhaul: smarter monster scaling, fair flee chance, defense damage reduction, linear XP curve, level‑up choices, fixed quest objective tracking, zone‑dependent difficulty, improved economy, and much more.

---

## ✨ Features

- **Immersive TUI** – Colored ASCII interface, dice roll animations, health/XP bars, and dynamic room descriptions.
- **Local LLM Dungeon Master** – Uses any Ollama model (from 0.5B to 70B) to narrate your actions and react to your choices.
- **Deterministic NLI** – Fast, zero‑latency command parsing (move, attack, use, etc.) with fuzzy spelling correction.
- **Full RPG mechanics**
  - Turn‑based combat with attack, defend, flee, and item use.
  - Equipment (weapons/armor), inventory, consumables, and permanent stat potions.
  - Leveling with **player‑chosen bonuses** (+2 attack, +2 defense, +4 damage, or +10 HP).
  - Alignment system (Good / Neutral / Evil) with minor XP/gold modifiers.
- **Quest system** – Kill, collect, explore, talk, escort, destroy, survive battles, and more. Quests can **fail** if you take too long or violate conditions.
- **Crafting & NPCs** – Blacksmith (weapons/armor, artifact upgrades, recycling) and Alchemist (potions, permanent boosts).
- **Procedural dungeon** – 50 rooms across four zones (entrance, mid, deep, boss) with zone‑dependent room types, traps, NPCs, and lore.
- **Persistent save/load** – Your adventure is saved locally, including quest progress.
- **Character soul & memory** – Your actions are recorded in `character_soul.md` and used by the LLM to keep context.
- **Balanced economy** – Gold, material costs, and loot tables tuned for a challenging but fair experience.

---

## 🎮 How to Play

You type commands in natural language. The Dungeon Master (LLM) interprets your intent and describes the outcome.

### Basic commands

| Action | Example |
|--------|---------|
| Move | `north`, `south`, `east`, `west`, `go north` |
| Look | `look`, `examine` |
| Attack | `attack`, `fight` |
| Defend | `defend`, `block` |
| Flee | `flee`, `run east` |
| Search | `search`, `loot` |
| Take item | `take rusty dagger` |
| Use item | `use health potion` |
| Equip | `equip iron sword` |
| Rest | `rest` (partial heal: 40% max HP + 2/level) |
| Talk to NPC | `talk` |
| Accept quest | `accept quest` |
| Craft | `craft Goblin Ear Potion` |

### System commands (start with `/`)

| Command | Description |
|---------|-------------|
| `/status` | Show HP, XP, level, bonuses, alignment |
| `/inventory` | List your items |
| `/quests` | Show active/completed quests and progress |
| `/lore` | Show discovered lore fragments |
| `/equip` | Show currently equipped gear |
| `/blacksmith` | Open the blacksmith crafting menu |
| `/alchemist` | Open the alchemist potion‑brewing menu |
| `/recycle` | Break down an item into crafting materials |
| `/roll d20` | Roll dice (e.g., `2d6+3`) |
| `/cast fireball` | Cast a spell (fireball, heal, cure) |
| `/save` | Save the game |
| `/load` | Load the last saved game |
| `/dm` | Switch to a different Ollama model |
| `/help` | Display full command list |
| `/guide` | Show quick tips |

---

## Installation

Put all the files from this repo into a folder.

```bash
1. cd ~/dungeonclaw (The folder that contains the files)

2. npm install

3. npm start
```

---

## ⚙️ Configuration

All settings are in `.env` (or environment variables). Important ones:

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL` | `nemotron-3-nano:4b` | Ollama model name |
| `OLLAMA_ENDPOINT` | `http://localhost:11434/api/generate` | Ollama API endpoint |
| `LLM_TIMEOUT` | `8000` | Timeout in ms for LLM calls |
| `DUNGEON_SIZE` | `50` | Number of rooms (0‑49) |
| `NLI_ENABLED` | `true` | Use fast intent matcher |
| `NARRATOR_ENABLED` | `true` | Use LLM for flavour narration |
| `MODEL_TIER` | `auto` | Override tier detection (`tiny`/`small`/`medium`/`large`) |
| `PYTHON_CMD` | `python3` | Python interpreter command |

---

## 🧠 Model Tier System

DungeonClaw automatically detects your model’s size and adjusts features:

| Tier | Model size | Features |
|------|------------|----------|
| `tiny` | ≤1B | No LLM fallback, no narration – NLI only |
| `small` | 1.5B–4B | Narration + LLM fallback + quest generation |
| `medium` | 7B–8B | Richer narration, more tokens |
| `large` | ≥13B | Deep story mode, full descriptive power |

You can force a tier with `MODEL_TIER=small` in `.env`.

---

## ⚔️ Balance & Design Philosophy (v6.2)

This version incorporates a comprehensive overhaul based on community feedback:

- **Monster scaling** – Reduced exponential growth; minions scale slower (capped at 2.5×), normal monsters cap at 3×.
- **Flee chance** – `40% + 6% per level above monster`, min 25% / max 80%.
- **Defense** – Now reduces incoming damage (min 1), not just AC.
- **Critical hits** – Only base dice are doubled; flat bonuses are not.
- **Minions** – Spawn in 15% of monster rooms (was 30%), and Minion Essence drop chance reduced to 40%.
- **XP curve** – Linear: `xpToNext = 100 + 20*(level-1)`. Max level 20.
- **Level‑up bonuses** – Choose between +2 attack, +2 defense, +4 damage, or +10 HP.
- **Rest** – Heals `40% max HP + 2*level` instead of full; has a chance to trigger an encounter in mid/deep zones.
- **Quest system** – Supports `kill`, `collect`, `explore`, `use`, `lore`, `talk`, `escort`, `destroy`, `kill_in_zone`, `survive_battles`. Includes failure conditions (time limit, alignment, forbidden kills).
- **Economy** – Boss gold reduced, potion crafting costs increased, recycling yields more materials, permanent potions are end‑game expensive.
- **Zone difficulty** – Room type weights change per zone (more traps in deep, fewer NPCs in boss, etc.). Boss zone includes a mini‑boss before the final room.

---

## 📁 File Structure

```
dungeonclaw/
├── dungeonclaw.js          # Main game loop (TypeScript/JS)
├── game_engine.py          # Python backend: combat, generation, crafting
├── nli.js                  # Deterministic intent resolver
├── fuzz.js                 # Levenshtein spell correction
├── model_tier.js           # Model size detection
├── tui.js                  # Terminal UI helpers (bars, boxes, animations)
├── templates.py            # Base template expansion script
├── templates.json          # Generated game data (rooms, monsters, items…)
├── crafting_recipes.json   # Crafting definitions
├── story_gen.py            # Story arc generator (template‑based)
├── SKILL.md                # Knowledge base for RAG (retrieval)
├── character_soul.md       # Player memory & persona (auto‑generated)
├── character_history.md    # Action log (markdown)
├── dungeonclaw_errors.ndjson # Error log
├── .env.example            # Environment variables template
├── package.json            # Node dependencies
└── README.md               # This file
```

---

## 🐛 Troubleshooting

- **`ollama` not found** – Make sure Ollama is installed and in your PATH.
- **Model fails to respond** – Increase `LLM_TIMEOUT` or try a smaller model (e.g., `tinyllama`).
- **Python errors** – Verify you have `requests` installed (`pip install requests`).  
  If you see `No module named 'python_shell'`, that’s a Node package – run `npm install`.
- **Game freezes on rest** – The rest animation is now removed; rest is instant. If you still see a delay, check your `tui.js` (the `restAnimation` function is not used anymore).
- **Quests not updating** – Make sure you are using the latest `dungeonclaw.js` and `game_engine.py` (v6.2). The quest objective handler now supports all types.


## 📜 License

MIT 

# SCREENSHOTS

![Alt Text](https://github.com/webxos/dungeonclaw/blob/main/assets/screen1.png)


![Alt Text](https://github.com/webxos/dungeonclaw/blob/main/assets/screen2.png)


![Alt Text](https://github.com/webxos/dungeonclaw/blob/main/assets/screen3.png)


![Alt Text](https://github.com/webxos/dungeonclaw/blob/main/assets/screen4.png)
