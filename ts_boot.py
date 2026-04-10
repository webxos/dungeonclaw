#!/usr/bin/env python3
"""
ts_boot.py – DungeonClaw v6.1 Unified Bootstrapper
Creates the complete project folder with all TypeScript, Python, JSON, and support files.
Usage: python3 ts_boot.py
"""

import os
import sys
import json
from pathlib import Path

# ======================================================================
# File content strings – embedded as raw strings
# ======================================================================

# ---------- TypeScript source files (updated for v6.1) ----------

TYPES_TS = '''// src/types.ts
export type Direction = 'north' | 'south' | 'east' | 'west';
export type ItemType = 'weapon' | 'armor' | 'potion' | 'key' | 'misc' | 'quest';
export type ToolName = 
  | 'move' | 'look' | 'attack' | 'defend' | 'flee'
  | 'search' | 'take' | 'equip' | 'use'
  | 'talk' | 'rest' | 'status' | 'inventory'
  | 'quest_log' | 'lore' | 'craft' | 'roll' | 'cast' | 'alignment' | 'accept_quest'
  | 'recycle' | 'blacksmith_menu' | 'alchemist_menu' | 'blacksmith_action' | 'alchemist_action';
export type ErrorSeverity = 'warn' | 'error' | 'fatal';
export type ErrorCategory = 'llm_json' | 'python_tool' | 'intent' | 'save_load' | 'quest' | 'combat' | 'agent';
export type ToolArgs = Record<string, unknown>;

export interface Item {
  name: string;
  type: ItemType;
  value: number;
  bonus?: number;          // for weapons/armor
  effect?: string;         // 'heal', 'buff', etc.
  consumable?: boolean;
  tier?: string;           // 'lesser', 'normal', 'greater', etc.
  stack?: number;          // for stackable items
  unique?: boolean;
  upgrade_level?: number;
  [key: string]: unknown;
}

export interface StatusEffect {
  name: string;
  duration: number;   // turns remaining
  value: number;      // magnitude
}

export interface Player {
  hp: number;
  maxHp: number;
  gold: number;
  inventory: Item[];
  level: number;
  xp: number;
  xpToNext: number;
  attack_bonus: number;
  defense_bonus: number;
  damage_bonus: number;
  weapon: Item | null;
  armor: Item | null;
  effects: StatusEffect[];
  alignment: number; // -10 to +10
  consumed_permanent?: string[];
}

export interface Monster {
  name: string;
  hp: number;
  max_hp: number;
  attack: number;
  defense: number;
  damage_range: [number, number];
  xp: number;
  gold_range: [number, number];
  loot_table: LootEntry[];
  special?: string;
  rarity?: string;
  is_minion?: boolean;
}

interface LootEntry {
  item: Item;
  chance: number;
}

export interface RoomMechanics {
  room_id: number;
  zone: 'entrance' | 'mid' | 'deep' | 'boss';
  type: string;
  description: string;
  ambient: string;
  exits: Direction[];
  monster: Monster | null;
  ground_loot: Item[];
  npc?: NPC;
  trap?: Trap;
  quest_hint?: string;
  pending_quest?: Quest;
  visited?: boolean;
}

export interface NPC {
  name: string;
  dialogue: string;
  quest_giver?: boolean;
  type?: 'blacksmith' | 'alchemist' | 'default';
}

export interface Trap {
  name: string;
  zone: string;
  effect: string;
  save_dc: number;
  damage: number;
}

export interface QuestObjective {
  type: 'kill' | 'collect' | 'visit' | 'talk' | 'use' | 'lore' | 'escort' | 'destroy';
  target: string;
  required: number;
  current: number;
}

export interface Quest {
  id: string;
  name: string;
  description: string;
  objectives: QuestObjective[];
  reward: { gold: number; xp: number; item?: Item };
  completed: boolean;
  failed?: boolean;
  alignment_shift?: number;
}

export interface Soul {
  persona: string;
  memory: string[];
  directives: string;
}

export interface ToolResult {
  success: boolean;
  message: string;
  description?: string;
  error?: string;
  new_room?: number;
  room_mechanics?: RoomMechanics;
  updated_room_mechanics?: RoomMechanics;
  player?: Player;
  damage?: number;
  heal?: number;
  gold?: number;
  xp?: number;
  loot?: Item | Item[];
  effects?: StatusEffect[];
  weapon?: Item;
  armor?: Item;
  quests?: Quest[];
  lore?: string[];
  alignment_shift?: number;
  total?: number;
  rolls?: number[];
  modifier?: number;
  dice?: { notation: string; rolls: number[]; total: number; modifier: number };
  monster_dice?: { notation: string; rolls: number[]; total: number; modifier: number };
  round_summary?: any;
  monster_defeated?: boolean;
  monster_name?: string;
  fled?: boolean;
  item_used?: string;
  type?: string;
  recipes?: any[];
  artifacts?: any[];
  items?: any[];
  menu?: { id: string; name: string; description: string }[];
}

export interface GameState {
  playerName: string;
  currentRoom: number;
  player: Player;
  visited: number[];
  room_mechanics: RoomMechanics | null;
  roomCache: [number, RoomMechanics][];
  quests: Quest[];
  lore: string[];
  combat_active: boolean;
  dungeon_size: number;
}

export interface HistoryEntry {
  user: string;
  agent: string;
  summary: string;
  toolName?: ToolName;
  timestamp: string;
}

export interface AgentStep {
  thought?: string;
  toolName?: ToolName;
  args?: ToolArgs;
  answer?: string;
  error?: string;
  source?: 'nli' | 'llm' | 'fallback';
}

export interface ErrorLogEntry {
  timestamp: string;
  severity: ErrorSeverity;
  category: ErrorCategory;
  context: string;
  raw?: string;
  stack?: string;
  tool?: ToolName;
  room?: number;
  playerLevel?: number;
  guide?: string;
}
'''

LOGGER_TS = '''// src/logger.ts
import * as fs from 'node:fs/promises';
import path from 'node:path';
import type { ErrorLogEntry, ErrorSeverity, ErrorCategory, ToolName } from './types.js';

const LOG_PATH = process.env.JSON_ERROR_LOG ?? path.join(process.cwd(), 'dungeonclaw_errors.ndjson');

export async function logError(
  severity: ErrorSeverity,
  category: ErrorCategory,
  context: string,
  opts: {
    raw?: string;
    stack?: string;
    tool?: ToolName;
    room?: number;
    playerLevel?: number;
    guide?: string;
  } = {}
): Promise<void> {
  const entry: ErrorLogEntry = {
    timestamp: new Date().toISOString(),
    severity,
    category,
    context: context.substring(0, 2000),
    ...opts
  };
  try {
    await fs.appendFile(LOG_PATH, JSON.stringify(entry) + '\\n');
  } catch (err) {
    console.error('[logger] Failed to write error log:', (err as Error).message);
  }
}

export const warn = (cat: ErrorCategory, ctx: string, opts = {}) => logError('warn', cat, ctx, opts);
export const error = (cat: ErrorCategory, ctx: string, opts = {}) => logError('error', cat, ctx, opts);
export const fatal = (cat: ErrorCategory, ctx: string, opts = {}) => logError('fatal', cat, ctx, opts);
'''

NLI_TS = '''// src/nli.ts
import type { ToolName, ToolArgs, Direction } from './types.js';

interface IntentPattern {
  patterns: RegExp[];
  tool: ToolName;
  extractArgs: (input: string) => ToolArgs | null;
}

const INTENT_MAP: IntentPattern[] = [
  {
    patterns: [/^go\\s+(north|south|east|west)/i, /^move\\s+(north|south|east|west)/i, /^(north|south|east|west)$/i],
    tool: 'move',
    extractArgs: (input) => {
      const m = input.match(/\\b(north|south|east|west)\\b/i);
      return m ? { direction: m[1].toLowerCase() as Direction } : null;
    }
  },
  {
    patterns: [/^look/i, /^describe/i, /^what('?s| is) here/i, /^where am i/i, /^examine/i],
    tool: 'look',
    extractArgs: () => ({})
  },
  {
    patterns: [/^take\\s+(.+)/i, /^get\\s+(.+)/i],
    tool: 'take',
    extractArgs: (input) => {
      const m = input.match(/^take\\s+(.+)/i) || input.match(/^get\\s+(.+)/i);
      return m ? { item_name: m[1].trim() } : null;
    }
  },
  {
    patterns: [/^search/i, /^loot/i, /^find/i, /^check for/i],
    tool: 'search',
    extractArgs: () => ({})
  },
  {
    patterns: [/^attack/i, /^fight/i, /^hit/i, /^strike/i, /^kill/i, /^slay/i],
    tool: 'attack',
    extractArgs: () => ({})
  },
  {
    patterns: [/^defend/i, /^block/i, /^parry/i, /^guard/i],
    tool: 'defend',
    extractArgs: () => ({})
  },
  {
    patterns: [/^flee/i, /^run\\s*(away)?$/i, /^retreat/i, /^escape/i],
    tool: 'flee',
    extractArgs: (input) => {
      const m = input.match(/\\b(north|south|east|west)\\b/i);
      return m ? { direction: m[1].toLowerCase() as Direction } : {};
    }
  },
  {
    patterns: [/^use\\s+(.+)/i],
    tool: 'use',
    extractArgs: (input) => {
      const m = input.match(/^use\\s+(.+)/i);
      return m ? { item_name: m[1].trim() } : null;
    }
  },
  {
    patterns: [/^equip\\s+(.+)/i, /^wield\\s+(.+)/i, /^wear\\s+(.+)/i],
    tool: 'equip',
    extractArgs: (input) => {
      const m = input.match(/^(equip|wield|wear)\\s+(.+)/i);
      return m ? { item_name: m[2].trim() } : null;
    }
  },
  {
    patterns: [/^craft\\s+(.+)/i, /^make\\s+(.+)/i],
    tool: 'craft',
    extractArgs: (input) => {
      const m = input.match(/^(craft|make)\\s+(.+)/i);
      return m ? { recipe_name: m[2].trim() } : null;
    }
  },
  {
    patterns: [/^talk/i, /^speak/i, /^converse/i, /^greet/i],
    tool: 'talk',
    extractArgs: () => ({})
  },
  {
    patterns: [/^accept quest/i, /^take quest/i, /^yes,? (i )?accept/i, /^i will accept/i, /^i take the quest/i],
    tool: 'accept_quest',
    extractArgs: () => ({})
  },
  {
    patterns: [/^rest/i, /^heal/i, /^sleep/i, /^recover/i, /^camp/i],
    tool: 'rest',
    extractArgs: () => ({})
  },
  {
    patterns: [/^(my )?(stats?|status|hp|health)/i, /^how (am i|is my health)/i],
    tool: 'status',
    extractArgs: () => ({})
  },
  {
    patterns: [/^(my )?(inventory|bag|items|pack)/i, /^what do i (have|carry)/i],
    tool: 'inventory',
    extractArgs: () => ({})
  },
  {
    patterns: [/^quests?/i, /^journal/i, /^log/i],
    tool: 'quest_log',
    extractArgs: () => ({})
  },
  {
    patterns: [/^lore/i, /^knowledge/i, /^story/i],
    tool: 'lore',
    extractArgs: () => ({})
  },
  {
    patterns: [/^roll\\s+(.+)/i, /^roll dice/i],
    tool: 'roll',
    extractArgs: (input) => {
      const m = input.match(/^roll\\s+(.+)/i);
      return m ? { dice: m[1].trim() } : { dice: '1d20' };
    }
  },
  {
    patterns: [/^cast\\s+(.+)/i],
    tool: 'cast',
    extractArgs: (input) => {
      const m = input.match(/^cast\\s+(.+)/i);
      return m ? { spell: m[1].trim() } : null;
    }
  },
  {
    patterns: [/^alignment/i, /^my alignment/i],
    tool: 'alignment',
    extractArgs: () => ({})
  },
  {
    patterns: [/^blacksmith/i, /^forge/i, /^smith/i],
    tool: 'blacksmith_menu',
    extractArgs: () => ({})
  },
  {
    patterns: [/^alchemist/i, /^brew/i, /^potion/i],
    tool: 'alchemist_menu',
    extractArgs: () => ({})
  },
  {
    patterns: [/^recycle/i, /^scrap/i, /^break down/i],
    tool: 'recycle',
    extractArgs: (input) => {
      const m = input.match(/^recycle\\s+(.+)/i);
      return m ? { item_name: m[1].trim() } : {};
    }
  }
];

export interface IntentResult {
  tool: ToolName;
  args: ToolArgs;
  source: 'nli';
}

export function resolveIntent(input: string): IntentResult | null {
  const trimmed = input.trim();
  for (const intent of INTENT_MAP) {
    for (const pat of intent.patterns) {
      if (pat.test(trimmed)) {
        const args = intent.extractArgs(trimmed);
        if (args !== null) return { tool: intent.tool, args, source: 'nli' };
      }
    }
  }
  return null;
}
'''

SOUL_TS = '''// src/soul.ts
import * as fs from 'node:fs/promises';
import path from 'node:path';
import type { Soul } from './types.js';

const SOUL_FILE = process.env.SOUL_FILE ?? path.join(process.cwd(), 'character_soul.md');
let soulWriteQueue = Promise.resolve();

export async function readSoul(): Promise<Soul> {
  try {
    const raw = await fs.readFile(SOUL_FILE, 'utf-8');
    const sections = raw.split(/^## /m);
    let persona = 'You are a brave dungeon adventurer.';
    let memory: string[] = [];
    let directives = '';

    for (const section of sections) {
      if (section.startsWith('VOICE')) {
        persona = section.substring(5).trim();
      } else if (section.startsWith('MEMORY')) {
        const lines = section.split('\\n');
        memory = lines
          .filter(l => l.trim().startsWith('- '))
          .map(l => l.trim().substring(2).trim());
      } else if (section.startsWith('DIRECTIVES')) {
        directives = section.substring(10).trim();
      }
    }
    return { persona, memory, directives };
  } catch {
    const defaultSoul: Soul = {
      persona: 'You are a brave adventurer exploring a vast fantasy dungeon. You are courageous, curious, and eager to find treasure and glory. You speak in first person and respond to the Dungeon Master\'s narration.',
      memory: ['You started your journey in Room 0.'],
      directives: '1. Always suggest 2 next actions.\\n2. If HP < 30, recommend rest.\\n3. If a monster is present, acknowledge it first.\\n4. Do not invent rooms or exits.'
    };
    await writeSoul(defaultSoul);
    return defaultSoul;
  }
}

export async function writeSoul(soul: Soul, playerName?: string): Promise<void> {
  const name = playerName ?? 'Adventurer';
  const content = `# SOUL: ${name}\\n\\n## VOICE\\n${soul.persona}\\n\\n## MEMORY\\n${soul.memory.map(m => `- ${m}`).join('\\n')}\\n\\n## DIRECTIVES\\n${soul.directives}`;
  soulWriteQueue = soulWriteQueue.then(() => fs.writeFile(SOUL_FILE, content));
  return soulWriteQueue;
}

export async function updateMemory(newEntry: string): Promise<void> {
  const soul = await readSoul();
  soul.memory.push(newEntry);
  if (soul.memory.length > 20) soul.memory = soul.memory.slice(-20);
  await writeSoul(soul);
}
'''

LLM_TS = '''// src/llm.ts
import axios from 'axios';
import { error as logError } from './logger.js';

const OLLAMA_ENDPOINT = process.env.OLLAMA_ENDPOINT || 'http://localhost:11434/api/generate';
const MODEL = process.env.MODEL || 'nemotron-3-nano:4b';
const TIMEOUT = parseInt(process.env.LLM_TIMEOUT || '5000');
const MAX_RETRIES = parseInt(process.env.LLM_MAX_RETRIES || '1');

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function callOllama(prompt: string, system: string): Promise<any> {
  const payload = {
    model: MODEL,
    prompt,
    system,
    stream: false,
    format: 'json',
    options: { temperature: 0.3, num_ctx: 512, num_predict: 80 }
  };

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await axios.post(OLLAMA_ENDPOINT, payload, { timeout: TIMEOUT });
      const rawText = response.data.response.trim();

      let parsed = null;
      try {
        parsed = JSON.parse(rawText);
      } catch (e) {
        const jsonBlockMatch = rawText.match(/```(?:json)?\\s*(\\{.*?\\})\\s*```/s);
        if (jsonBlockMatch) {
          try { parsed = JSON.parse(jsonBlockMatch[1]); } catch (inner) {}
        }
        if (!parsed) {
          const firstBrace = rawText.indexOf('{');
          const lastBrace = rawText.lastIndexOf('}');
          if (firstBrace !== -1 && lastBrace > firstBrace) {
            const maybeJson = rawText.substring(firstBrace, lastBrace + 1);
            try { parsed = JSON.parse(maybeJson); } catch (inner) {}
          }
        }
        if (!parsed) {
          await logError('llm_json', 'LLM returned malformed JSON', { raw: rawText, context: `${system}\\n\\n${prompt}` });
          return { error: 'Malformed JSON response' };
        }
      }
      return parsed;
    } catch (err) {
      if (attempt < MAX_RETRIES) {
        const backoff = Math.pow(2, attempt) * 1500;
        await sleep(backoff);
      } else {
        await logError('llm_json', 'LLM unavailable after retries', { raw: (err as Error).message, context: `${system}\\n\\n${prompt}` });
        return { error: 'LLM failed after retries' };
      }
    }
  }
  return null;
}

export async function callOllamaText(prompt: string, system: string = '', temperature: number = 0.7, maxTokens: number = 60): Promise<string> {
  const payload = {
    model: MODEL,
    prompt,
    system,
    stream: false,
    options: { temperature, num_predict: maxTokens }
  };
  try {
    const response = await axios.post(OLLAMA_ENDPOINT, payload, { timeout: TIMEOUT });
    return response.data.response?.trim() || '';
  } catch {
    return '';
  }
}
'''

PYTHON_TS = '''// src/python.ts
import { PythonShell } from 'python-shell';
import { error as logError } from './logger.js';
import type { GameState } from './types.js';

const PYTHON_CMD = process.env.PYTHON_CMD || 'python3';

export async function callPythonTool<T = any>(
  command: string,
  args: Record<string, any> = {},
  state?: GameState
): Promise<T> {
  const fullArgs = { ...args, state };
  return new Promise((resolve, reject) => {
    const options = {
      mode: 'json' as const,
      pythonPath: PYTHON_CMD,
      scriptPath: '.',
      args: [command, JSON.stringify(fullArgs)]
    };

    let stderrOutput = '';
    const pyshell = new PythonShell('game_engine.py', options);

    pyshell.on('stderr', (data) => {
      stderrOutput += data;
    });

    pyshell.on('error', (err) => {
      logError('python_tool', `Python error: ${err.message}`, { raw: stderrOutput });
      reject(new Error(`Python error: ${err.message}\\nStderr: ${stderrOutput}`));
    });

    const results: any[] = [];
    pyshell.on('message', (message) => {
      results.push(message);
    });

    pyshell.end((err) => {
      if (err) {
        logError('python_tool', `Python shell error: ${err.message}`, { raw: stderrOutput });
        reject(new Error(`Python shell error: ${err.message}\\nStderr: ${stderrOutput}`));
      } else if (results.length === 0) {
        logError('python_tool', 'No output from Python', { raw: stderrOutput });
        reject(new Error(`No output from Python\\nStderr: ${stderrOutput}`));
      } else {
        resolve(results[0] as T);
      }
    });
  });
}
'''

TOOLS_TS = '''// src/tools.ts
import { callPythonTool } from './python.js';
import type { GameState, ToolName, ToolArgs, ToolResult, Direction } from './types.js';
import { error } from './logger.js';

export interface ToolDef {
  name: ToolName;
  description: string;
  input_schema: Record<string, { type: string; description: string; required?: boolean }>;
  execute: (args: ToolArgs, state: GameState) => Promise<ToolResult>;
}

async function pythonTool(tool: ToolName, args: ToolArgs, state: GameState): Promise<ToolResult> {
  try {
    return await callPythonTool('execute_tool', { tool, args, state });
  } catch (err) {
    await error('python_tool', `${tool} failed: ${(err as Error).message}`, { tool, room: state.currentRoom, playerLevel: state.player.level });
    return { success: false, message: `Tool '${tool}' encountered an error.` };
  }
}

export const TOOLS: ToolDef[] = [
  {
    name: 'move',
    description: 'Move the player in a cardinal direction.',
    input_schema: {
      direction: { type: 'string', description: 'north | south | east | west', required: true }
    },
    execute: (args, state) => pythonTool('move', args, state)
  },
  {
    name: 'look',
    description: 'Describe the current room, exits, and contents.',
    input_schema: {},
    execute: (args, state) => pythonTool('look', args, state)
  },
  {
    name: 'attack',
    description: 'Attack the monster in the current room.',
    input_schema: {},
    execute: (args, state) => pythonTool('attack', args, state)
  },
  {
    name: 'defend',
    description: 'Take a defensive stance, reducing incoming damage.',
    input_schema: {},
    execute: (args, state) => pythonTool('defend', args, state)
  },
  {
    name: 'flee',
    description: 'Attempt to escape combat in a direction.',
    input_schema: {
      direction: { type: 'string', description: 'north | south | east | west' }
    },
    execute: (args, state) => pythonTool('flee', args, state)
  },
  {
    name: 'search',
    description: 'Search the room for hidden items or loot.',
    input_schema: {},
    execute: (args, state) => pythonTool('search', args, state)
  },
  {
    name: 'take',
    description: 'Pick up a specific item from the ground.',
    input_schema: {
      item_name: { type: 'string', description: 'Name of the item to take', required: true }
    },
    execute: (args, state) => pythonTool('take', args, state)
  },
  {
    name: 'equip',
    description: 'Equip a weapon or armor from your inventory.',
    input_schema: {
      item_name: { type: 'string', description: 'Name of item to equip', required: true }
    },
    execute: (args, state) => pythonTool('equip', args, state)
  },
  {
    name: 'use',
    description: 'Use a consumable item (potion, scroll, etc).',
    input_schema: {
      item_name: { type: 'string', description: 'Name of item to use', required: true }
    },
    execute: (args, state) => pythonTool('use', args, state)
  },
  {
    name: 'talk',
    description: 'Talk to an NPC in the room.',
    input_schema: {},
    execute: (args, state) => pythonTool('talk', args, state)
  },
  {
    name: 'accept_quest',
    description: 'Accept a quest offered by an NPC.',
    input_schema: {},
    execute: (args, state) => pythonTool('accept_quest', args, state)
  },
  {
    name: 'rest',
    description: 'Rest to recover HP (only safe outside combat).',
    input_schema: {},
    execute: (args, state) => pythonTool('rest', args, state)
  },
  {
    name: 'status',
    description: 'Show player status.',
    input_schema: {},
    execute: (args, state) => pythonTool('status', args, state)
  },
  {
    name: 'inventory',
    description: 'Show player inventory.',
    input_schema: {},
    execute: (args, state) => pythonTool('inventory', args, state)
  },
  {
    name: 'quest_log',
    description: 'View all active and completed quests.',
    input_schema: {},
    execute: (args, state) => pythonTool('quest_log', args, state)
  },
  {
    name: 'lore',
    description: 'Read collected lore fragments.',
    input_schema: {},
    execute: (args, state) => pythonTool('lore', args, state)
  },
  {
    name: 'craft',
    description: 'Craft an item from a recipe.',
    input_schema: {
      recipe_name: { type: 'string', description: 'Name of the recipe', required: true }
    },
    execute: (args, state) => pythonTool('craft', args, state)
  },
  {
    name: 'recycle',
    description: 'Break down an item into crafting materials.',
    input_schema: {
      item_name: { type: 'string', description: 'Name of item to recycle', required: true }
    },
    execute: (args, state) => pythonTool('recycle', args, state)
  },
  {
    name: 'blacksmith_menu',
    description: 'Open the blacksmith menu.',
    input_schema: {},
    execute: (args, state) => pythonTool('blacksmith_menu', args, state)
  },
  {
    name: 'blacksmith_action',
    description: 'Perform an action in the blacksmith menu.',
    input_schema: {
      action: { type: 'string', description: 'Action ID', required: true }
    },
    execute: (args, state) => pythonTool('blacksmith_action', args, state)
  },
  {
    name: 'alchemist_menu',
    description: 'Open the alchemist menu.',
    input_schema: {},
    execute: (args, state) => pythonTool('alchemist_menu', args, state)
  },
  {
    name: 'alchemist_action',
    description: 'Perform an action in the alchemist menu.',
    input_schema: {
      action: { type: 'string', description: 'Action ID', required: true }
    },
    execute: (args, state) => pythonTool('alchemist_action', args, state)
  },
  {
    name: 'roll',
    description: 'Roll dice (e.g., "roll d20", "roll 2d6+3").',
    input_schema: {
      dice: { type: 'string', description: 'Dice notation', required: false }
    },
    execute: (args, state) => pythonTool('roll_dice', args, state)
  },
  {
    name: 'cast',
    description: 'Cast a spell (fireball, heal, etc.).',
    input_schema: {
      spell: { type: 'string', description: 'Spell name', required: true }
    },
    execute: (args, state) => pythonTool('cast_spell', args, state)
  },
  {
    name: 'alignment',
    description: 'Check your current alignment.',
    input_schema: {},
    execute: (args, state) => pythonTool('alignment', args, state)
  }
];

export const TOOL_MAP = new Map<ToolName, ToolDef>(TOOLS.map(t => [t.name, t]));

export function getTool(name: string): ToolDef | undefined {
  return TOOL_MAP.get(name as ToolName);
}
'''

AGENT_TS = '''// src/agent.ts
import { resolveIntent } from './nli.js';
import { getTool, TOOLS } from './tools.js';
import { callPythonTool } from './python.js';
import { callOllama } from './llm.js';
import { readSoul } from './soul.js';
import { error, warn } from './logger.js';
import type { AgentStep, GameState, ToolArgs, ToolName, HistoryEntry } from './types.js';

const VALID_TOOLS = new Set<ToolName>(TOOLS.map(t => t.name));

export async function runAgentStep(
  userInput: string,
  history: HistoryEntry[],
  state: GameState
): Promise<AgentStep> {
  const nliResult = resolveIntent(userInput);
  if (nliResult) {
    try {
      const validation = await callPythonTool('validate_intent', {
        tool: nliResult.tool,
        args: nliResult.args,
        state
      });
      if (!validation.valid) {
        return { answer: validation.reason ?? "You can't do that right now.", source: 'nli' };
      }
    } catch (err) {
      await warn('intent', `validate_intent failed: ${(err as Error).message}`, { tool: nliResult.tool });
    }
    return { thought: 'NLI resolved', toolName: nliResult.tool, args: nliResult.args, source: 'nli' };
  }

  let stateSummary = '';
  try {
    const r = await callPythonTool('tool_summary', { state });
    stateSummary = r.summary ?? '';
  } catch { /* non-fatal */ }

  let actionMenu: [string, string][] = [];
  try {
    const r = await callPythonTool('get_action_menu', { state });
    actionMenu = r.menu ?? [];
  } catch { /* non-fatal */ }

  const soul = await readSoul();
  const menuText = actionMenu.map(([, desc], i) => `${i + 1}. ${desc}`).join('\\n');
  const recentCtx = history.slice(-2).map(h => `User: ${h.user}\\nDM: ${h.summary}`).join('\\n');

  const systemPrompt = [
    soul.persona,
    `Current state: ${stateSummary}`,
    menuText,
    'Reply with a single number or short phrase like "move north". No JSON, just text.'
  ].join('\\n');

  const llmResp = await callOllama(`${recentCtx}\\nUser: ${userInput}\\nYour choice:`, systemPrompt);
  if (!llmResp || llmResp.error) {
    await error('agent', 'LLM fallback returned no result', { room: state.currentRoom });
    return { answer: 'The dungeon stirs... (Try: go north, attack, look, rest)', source: 'fallback' };
  }

  const llmText = (llmResp.answer ?? llmResp.choice ?? JSON.stringify(llmResp)).toString();

  let chosenAction: string | null = null;
  try {
    const r = await callPythonTool('parse_llm_choice', { text: llmText, actions: actionMenu });
    chosenAction = r.choice ?? null;
  } catch { /* non-fatal */ }

  if (!chosenAction) {
    return { answer: 'The oracle is unclear. Try something simpler.', source: 'llm' };
  }

  const parts = chosenAction.split(' ');
  const toolName = parts[0] as ToolName;
  if (!VALID_TOOLS.has(toolName)) {
    await warn('agent', `LLM chose unknown tool: ${toolName}`);
    return { answer: `I don't know how to '${toolName}'.`, source: 'llm' };
  }

  let args: ToolArgs = {};
  if (parts.length > 1) {
    const argStr = parts.slice(1).join(' ');
    if (['move', 'flee'].includes(toolName)) args = { direction: argStr };
    else if (['take', 'equip', 'use', 'recycle'].includes(toolName)) args = { item_name: argStr };
    else if (toolName === 'craft') args = { recipe_name: argStr };
    else if (toolName === 'cast') args = { spell: argStr };
    else if (toolName === 'roll') args = { dice: argStr };
    else args = { value: argStr };
  }

  return { thought: `LLM chose ${chosenAction}`, toolName, args, source: 'llm' };
}
'''

QUESTS_TS = '''// src/quests.ts
import type { Quest, QuestObjective, Player, ToolName, ToolResult } from './types.js';
import { warn } from './logger.js';

export function updateQuestProgress(
  quests: Quest[],
  toolName: ToolName,
  result: ToolResult
): Quest[] {
  return quests.map(q => {
    if (q.completed || q.failed) return q;
    const updated = { ...q, objectives: q.objectives.map(obj => {
      if (obj.current >= obj.required) return obj;
      if (toolName === 'attack' && result.success && obj.type === 'kill') {
        const killed = result.message?.toLowerCase().includes(obj.target.toLowerCase());
        return killed ? { ...obj, current: obj.current + 1 } : obj;
      }
      if (toolName === 'take' && obj.type === 'collect') {
        const taken = result.message?.toLowerCase().includes(obj.target.toLowerCase());
        return taken ? { ...obj, current: obj.current + 1 } : obj;
      }
      if (toolName === 'move' && obj.type === 'visit') {
        const visited = result.message?.toLowerCase().includes(obj.target.toLowerCase());
        return visited ? { ...obj, current: obj.current + 1 } : obj;
      }
      if (toolName === 'talk' && obj.type === 'talk') {
        const spoke = result.message?.toLowerCase().includes(obj.target.toLowerCase());
        return spoke ? { ...obj, current: obj.current + 1 } : obj;
      }
      return obj;
    })};
    return updated;
  });
}

export function checkQuestCompletion(
  quests: Quest[],
  player: Player
): { quests: Quest[]; player: Player; completedNames: string[] } {
  const completedNames: string[] = [];
  let p = { ...player };
  const updated = quests.map(q => {
    if (q.completed || q.failed) return q;
    const allDone = q.objectives.every(o => o.current >= o.required);
    if (!allDone) return q;
    completedNames.push(q.name);
    p = {
      ...p,
      gold: p.gold + q.reward.gold,
      xp: p.xp + q.reward.xp,
      inventory: q.reward.item ? [...p.inventory, q.reward.item] : p.inventory
    };
    if (q.alignment_shift) p.alignment = Math.min(10, Math.max(-10, p.alignment + q.alignment_shift));
    return { ...q, completed: true };
  });
  return { quests: updated, player: p, completedNames };
}

export function questSummary(quest: Quest): string {
  const pct = quest.objectives
    .map(o => `${o.type} ${o.target}: ${o.current}/${o.required}`)
    .join(', ');
  return `[${quest.completed ? 'DONE' : 'ACTIVE'}] ${quest.name} – ${pct}`;
}
'''

STORY_TS = '''// src/story.ts
import type { RoomMechanics, Player, Quest, Soul, ToolName, ToolResult } from './types.js';

export interface NarrationContext {
  playerName: string;
  toolName: ToolName;
  result: ToolResult;
  room: RoomMechanics;
  player: Player;
  quests: Quest[];
  lore: string[];
  soul: Soul;
}

export function buildNarrationPrompt(ctx: NarrationContext): string {
  const activeQuests = ctx.quests
    .filter(q => !q.completed && !q.failed)
    .map(q => q.name)
    .join(', ') || 'none';

  const recentLore = ctx.lore.slice(-3).join(' | ') || 'none';
  const hpFrac = ctx.player.hp / ctx.player.maxHp;
  const hpDesc = hpFrac < 0.3 ? 'near death' : hpFrac < 0.6 ? 'wounded' : 'healthy';
  const monsterCtx = ctx.room.monster && ctx.room.monster.hp > 0
    ? `A ${ctx.room.monster.name} (HP ${ctx.room.monster.hp}/${ctx.room.monster.max_hp}) is here.`
    : 'No monsters present.';

  return [
    `You are an epic fantasy Dungeon Master narrating in second-person, vivid prose.`,
    `Player: ${ctx.playerName}, Level ${ctx.player.level}, ${hpDesc}.`,
    `Room: ${ctx.room.description}`,
    `${monsterCtx}`,
    `Active quests: ${activeQuests}.`,
    `Recent lore: ${recentLore}.`,
    `Action taken: ${ctx.toolName}. Result: ${ctx.result.message}`,
    `Soul directive: ${ctx.soul.directives}`,
    `Narrate in 2-3 vivid sentences. Foreshadow quest relevance if appropriate. No JSON.`
  ].join('\\n');
}

export function buildQuestCompletePrompt(playerName: string, questName: string, reward: string): string {
  return [
    `You are a Dungeon Master. The player ${playerName} just completed the quest: "${questName}".`,
    `Reward: ${reward}.`,
    `Write a triumphant 2-sentence narration. Be dramatic and celebratory.`
  ].join('\\n');
}
'''

DUNGEONCLAW_TS = '''// src/dungeonclaw.ts
import * as readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import dotenv from 'dotenv';
import * as fs from 'node:fs/promises';
import path from 'node:path';

import { callPythonTool } from './python.js';
import { callOllamaText } from './llm.js';
import { readSoul, writeSoul, updateMemory } from './soul.js';
import { getTool, TOOLS } from './tools.js';
import { runAgentStep } from './agent.js';
import { updateQuestProgress, checkQuestCompletion } from './quests.js';
import { buildNarrationPrompt, buildQuestCompletePrompt } from './story.js';
import { error, fatal } from './logger.js';
import type { GameState, HistoryEntry, RoomMechanics, Player, Quest } from './types.js';

dotenv.config();

// ---------- Configuration ----------
const OLLAMA_ENDPOINT = process.env.OLLAMA_ENDPOINT || 'http://localhost:11434/api/generate';
let currentModel = process.env.MODEL || 'nemotron-3-nano:4b';
const LLM_TIMEOUT = parseInt(process.env.LLM_TIMEOUT || '5000');
const LLM_MAX_RETRIES = parseInt(process.env.LLM_MAX_RETRIES || '1');
const PYTHON_CMD = process.env.PYTHON_CMD || 'python3';
const DUNGEON_SIZE = parseInt(process.env.DUNGEON_SIZE || '50');
const SOUL_FILE = process.env.SOUL_FILE || path.join(process.cwd(), 'character_soul.md');
const JSON_ERROR_LOG = process.env.JSON_ERROR_LOG || path.join(process.cwd(), 'dungeonclaw_errors.ndjson');
const DEBUG = process.env.DEBUG === 'true';
const NLI_ENABLED = process.env.NLI_ENABLED !== 'false';
const NARRATOR_ENABLED = process.env.NARRATOR_ENABLED !== 'false';

// ---------- Game State ----------
let playerName = '';
let currentRoom = 0;
let player: Player = {
  hp: 100,
  maxHp: 100,
  gold: 50,
  inventory: [],
  level: 1,
  xp: 0,
  xpToNext: 100,
  attack_bonus: 0,
  defense_bonus: 0,
  damage_bonus: 0,
  weapon: null,
  armor: null,
  effects: [],
  alignment: 0
};
let quests: Quest[] = [];
let lore: string[] = [];
let visited = new Set<number>();
let currentRoomMechanics: RoomMechanics | null = null;
let roomCache = new Map<number, RoomMechanics>();
let combatActive = false;

const rl = readline.createInterface({ input, output });

// ---------- Helper Functions ----------
function buildGameState(): GameState {
  return {
    playerName,
    currentRoom,
    player,
    visited: Array.from(visited),
    room_mechanics: currentRoomMechanics,
    roomCache: Array.from(roomCache.entries()),
    quests,
    lore,
    combat_active: combatActive,
    dungeon_size: DUNGEON_SIZE
  };
}

async function switchModel() {
  console.log('\\nFetching installed Ollama models...');
  const result = await callPythonTool('list_models').catch(err => {
    console.log(`\\x1b[31mError fetching models: ${err.message}\\x1b[0m`);
    return null;
  });
  if (!result || result.error) {
    console.log(`\\x1b[31mCould not get model list. Is ollama installed? Error: ${result?.error}\\x1b[0m`);
    return;
  }
  const models = result.models;
  if (!models.length) {
    console.log('\\x1b[31mNo models found. Please install a model with `ollama pull <name>`.\\x1b[0m');
    return;
  }
  console.log('\\nAvailable models:');
  models.forEach((m: string, i: number) => {
    console.log(`  ${i+1}. ${m}`);
  });
  const answer = await rl.question('\\nEnter the number of the model to switch to (or press Enter to cancel): ');
  const choice = parseInt(answer);
  if (isNaN(choice) || choice < 1 || choice > models.length) {
    console.log('No change.');
    return;
  }
  const newModel = models[choice-1];
  currentModel = newModel;
  console.log(`\\x1b[32mSwitched to model: ${currentModel}\\x1b[0m`);
}

async function applyToolResult(state: GameState, result: any): Promise<GameState> {
  const newState = { ...state };
  if (result.new_room !== undefined) {
    newState.currentRoom = result.new_room;
    if (roomCache.has(newState.currentRoom)) {
      newState.room_mechanics = roomCache.get(newState.currentRoom)!;
    } else {
      newState.room_mechanics = result.room_mechanics;
      roomCache.set(newState.currentRoom, newState.room_mechanics);
    }
    newState.visited.push(newState.currentRoom);
    newState.combat_active = false;
    if (newState.room_mechanics.monster && newState.room_mechanics.monster.hp > 0) {
      newState.combat_active = true;
    }
  }
  if (result.updated_room_mechanics) {
    newState.room_mechanics = result.updated_room_mechanics;
    roomCache.set(newState.currentRoom, newState.room_mechanics);
  }
  if (result.player) {
    newState.player = result.player;
  } else {
    if (result.damage) newState.player.hp -= result.damage;
    if (result.heal) newState.player.hp = Math.min(newState.player.maxHp, newState.player.hp + result.heal);
    if (result.gold) newState.player.gold += result.gold;
    if (result.xp) newState.player.xp += result.xp;
    if (result.loot) {
      const lootItems = Array.isArray(result.loot) ? result.loot : [result.loot];
      newState.player.inventory.push(...lootItems);
    }
    if (result.effects) newState.player.effects = result.effects;
    if (result.weapon) newState.player.weapon = result.weapon;
    if (result.armor) newState.player.armor = result.armor;
    if (result.alignment_shift) newState.player.alignment = Math.min(10, Math.max(-10, newState.player.alignment + result.alignment_shift));
  }
  if (result.quests) newState.quests = result.quests;
  if (result.lore) newState.lore = result.lore;

  if (newState.room_mechanics?.monster && newState.room_mechanics.monster.hp <= 0) {
    newState.combat_active = false;
  } else if (newState.room_mechanics?.monster && newState.room_mechanics.monster.hp > 0) {
    newState.combat_active = true;
  }

  return newState;
}

async function checkLevelUp() {
  while (player.xp >= player.xpToNext) {
    player.level++;
    player.xp -= player.xpToNext;
    player.xpToNext = Math.floor(player.xpToNext * 1.5);
    player.maxHp += 15;
    player.hp = player.maxHp;
    player.attack_bonus += 1;
    player.damage_bonus += 1;
    if (player.level % 2 === 0) player.defense_bonus += 1;
    console.log(`\\n\\x1b[33m***** LEVEL UP! *****\\x1b[0m`);
    console.log(`\\x1b[32mYou are now level ${player.level}! Max HP increased to ${player.maxHp}.\\x1b[0m`);
  }
}

async function saveGame() {
  const saveData = {
    playerName,
    currentRoom,
    player,
    visited: Array.from(visited),
    room_mechanics: currentRoomMechanics,
    roomCache: Array.from(roomCache.entries()),
    quests,
    lore
  };
  await fs.writeFile('dungeonclaw_save.json', JSON.stringify(saveData, null, 2));
  console.log('\\x1b[32mAdventure saved!\\x1b[0m');
}

async function loadGame(): Promise<boolean> {
  try {
    const data = JSON.parse(await fs.readFile('dungeonclaw_save.json', 'utf8'));
    playerName = data.playerName;
    currentRoom = data.currentRoom;
    player = data.player;
    visited = new Set(data.visited);
    currentRoomMechanics = data.room_mechanics;
    roomCache = new Map(data.roomCache || []);
    quests = data.quests || [];
    lore = data.lore || [];
    console.log('\\x1b[32mAdventure loaded!\\x1b[0m');
    return true;
  } catch {
    return false;
  }
}

function printIntro() {
  console.log(`
\\u001b[37m
▄               ▜      
▌▌▌▌▛▌▛▌█▌▛▌▛▌▛▘▐ ▀▌▌▌▌
▙▘▙▌▌▌▙▌▙▖▙▌▌▌▙▖▐▖█▌▚▚▘
      ▄▌
\\u001b[0m`);
  console.log('\\u001b[1;37m╔══════════════════════════════════════════════════════════════╗\\u001b[0m');
  console.log('\\u001b[1;37m║        D U N G E O N C L A W    v6.1  (D&D Enhanced)        ║\\u001b[0m');
  console.log('\\u001b[1;37m║     character_soul.md • Deterministic NLI • Tolkien Fantasy   ║\\u001b[0m');
  console.log('\\u001b[1;37m╚══════════════════════════════════════════════════════════════╝\\u001b[0m\\n');
}

async function handleBlacksmith() {
  const menuResult = await callPythonTool('blacksmith_menu', {}, buildGameState());
  if (!menuResult.success) {
    console.log(`\\x1b[31m${menuResult.message}\\x1b[0m`);
    return;
  }
  const menu = menuResult.menu;
  while (true) {
    console.log(`\\n${'\\x1b[1;33m'}Blacksmith Menu${'\\x1b[0m'}`);
    for (let i = 0; i < menu.length; i++) {
      console.log(`${i+1}. ${menu[i].name} - ${menu[i].description}`);
    }
    const choice = await rl.question('Choose an option (or "exit" to leave): ');
    if (choice.toLowerCase() === 'exit') break;
    const idx = parseInt(choice) - 1;
    if (isNaN(idx) || idx < 0 || idx >= menu.length) {
      console.log('Invalid choice.');
      continue;
    }
    const action = menu[idx].id;
    const actionResult = await callPythonTool('blacksmith_action', { action }, buildGameState());
    if (!actionResult.success) {
      console.log(`\\x1b[31m${actionResult.message}\\x1b[0m`);
      continue;
    }
    if (actionResult.type === 'craft_weapon' || actionResult.type === 'craft_armor') {
      const recipes = actionResult.recipes;
      console.log(`\\n${'\\x1b[1;33m'}Available recipes:${'\\x1b[0m'}`);
      for (let i = 0; i < recipes.length; i++) {
        const r = recipes[i];
        const mats = Object.entries(r.materials).map(([name, count]) => `${count}x ${name}`).join(', ');
        console.log(`${i+1}. ${r.name} - Cost: ${r.gold_cost} gold, Materials: ${mats} -> ${r.result.name}`);
      }
      const recipeChoice = await rl.question('Choose recipe number (or 0 to cancel): ');
      const recipeIdx = parseInt(recipeChoice) - 1;
      if (recipeIdx >= 0 && recipeIdx < recipes.length) {
        const recipe = recipes[recipeIdx];
        const craftResult = await callPythonTool('blacksmith_action', { action: 'craft_selected', recipe_name: recipe.name }, buildGameState());
        if (craftResult.success) {
          console.log(`\\x1b[32m${craftResult.message}\\x1b[0m`);
          player = craftResult.player;
        } else {
          console.log(`\\x1b[31m${craftResult.message}\\x1b[0m`);
        }
      }
    } else if (actionResult.type === 'upgrade_artifact') {
      const artifacts = actionResult.artifacts;
      if (artifacts.length === 0) {
        console.log('No artifacts to upgrade.');
        continue;
      }
      console.log(`\\n${'\\x1b[1;33m'}Artifacts:${'\\x1b[0m'}`);
      for (let i = 0; i < artifacts.length; i++) {
        const a = artifacts[i];
        console.log(`${i+1}. ${a.name} (upgrade level ${a.upgrade_level}, +${a.bonus})`);
      }
      const artifactChoice = await rl.question('Choose artifact number (or 0 to cancel): ');
      const artifactIdx = parseInt(artifactChoice) - 1;
      if (artifactIdx >= 0 && artifactIdx < artifacts.length) {
        const artifact = artifacts[artifactIdx];
        const upgradeResult = await callPythonTool('blacksmith_action', { action: 'upgrade_selected', artifact_name: artifact.name }, buildGameState());
        if (upgradeResult.success) {
          console.log(`\\x1b[32m${upgradeResult.message}\\x1b[0m`);
          player = upgradeResult.player;
        } else {
          console.log(`\\x1b[31m${upgradeResult.message}\\x1b[0m`);
        }
      }
    } else if (actionResult.type === 'recycle') {
      const items = actionResult.items;
      if (items.length === 0) {
        console.log('No items to recycle.');
        continue;
      }
      console.log(`\\n${'\\x1b[1;33m'}Items to recycle:${'\\x1b[0m'}`);
      for (let i = 0; i < items.length; i++) {
        console.log(`${i+1}. ${items[i].name} (${items[i].type})`);
      }
      const itemChoice = await rl.question('Choose item number (or 0 to cancel): ');
      const itemIdx = parseInt(itemChoice) - 1;
      if (itemIdx >= 0 && itemIdx < items.length) {
        const item = items[itemIdx];
        const recycleResult = await callPythonTool('recycle', { item_name: item.name }, buildGameState());
        if (recycleResult.success) {
          console.log(`\\x1b[32m${recycleResult.message}\\x1b[0m`);
          player = recycleResult.player;
        } else {
          console.log(`\\x1b[31m${recycleResult.message}\\x1b[0m`);
        }
      }
    }
  }
}

async function handleAlchemist() {
  const menuResult = await callPythonTool('alchemist_menu', {}, buildGameState());
  if (!menuResult.success) {
    console.log(`\\x1b[31m${menuResult.message}\\x1b[0m`);
    return;
  }
  const menu = menuResult.menu;
  while (true) {
    console.log(`\\n${'\\x1b[1;32m'}Alchemist Menu${'\\x1b[0m'}`);
    for (let i = 0; i < menu.length; i++) {
      console.log(`${i+1}. ${menu[i].name} - ${menu[i].description}`);
    }
    const choice = await rl.question('Choose an option (or "exit" to leave): ');
    if (choice.toLowerCase() === 'exit') break;
    const idx = parseInt(choice) - 1;
    if (isNaN(idx) || idx < 0 || idx >= menu.length) {
      console.log('Invalid choice.');
      continue;
    }
    const action = menu[idx].id;
    const actionResult = await callPythonTool('alchemist_action', { action }, buildGameState());
    if (!actionResult.success) {
      console.log(`\\x1b[31m${actionResult.message}\\x1b[0m`);
      continue;
    }
    if (actionResult.type === 'brew_potion' || actionResult.type === 'brew_permanent') {
      const recipes = actionResult.recipes;
      console.log(`\\n${'\\x1b[1;32m'}Available recipes:${'\\x1b[0m'}`);
      for (let i = 0; i < recipes.length; i++) {
        const r = recipes[i];
        const mats = Object.entries(r.materials).map(([name, count]) => `${count}x ${name}`).join(', ');
        console.log(`${i+1}. ${r.name} - Cost: ${r.gold_cost} gold, Materials: ${mats} -> ${r.result.name || r.result.effect}`);
      }
      const recipeChoice = await rl.question('Choose recipe number (or 0 to cancel): ');
      const recipeIdx = parseInt(recipeChoice) - 1;
      if (recipeIdx >= 0 && recipeIdx < recipes.length) {
        const recipe = recipes[recipeIdx];
        const brewResult = await callPythonTool('alchemist_action', { action: 'brew_selected', recipe_name: recipe.name, potion_type: actionResult.type === 'brew_potion' ? 'potion' : 'permanent' }, buildGameState());
        if (brewResult.success) {
          console.log(`\\x1b[32m${brewResult.message}\\x1b[0m`);
          player = brewResult.player;
        } else {
          console.log(`\\x1b[31m${brewResult.message}\\x1b[0m`);
        }
      }
    } else if (actionResult.type === 'recycle') {
      const items = actionResult.items;
      if (items.length === 0) {
        console.log('No items to recycle.');
        continue;
      }
      console.log(`\\n${'\\x1b[1;32m'}Items to recycle:${'\\x1b[0m'}`);
      for (let i = 0; i < items.length; i++) {
        console.log(`${i+1}. ${items[i].name} (${items[i].type})`);
      }
      const itemChoice = await rl.question('Choose item number (or 0 to cancel): ');
      const itemIdx = parseInt(itemChoice) - 1;
      if (itemIdx >= 0 && itemIdx < items.length) {
        const item = items[itemIdx];
        const recycleResult = await callPythonTool('recycle', { item_name: item.name }, buildGameState());
        if (recycleResult.success) {
          console.log(`\\x1b[32m${recycleResult.message}\\x1b[0m`);
          player = recycleResult.player;
        } else {
          console.log(`\\x1b[31m${recycleResult.message}\\x1b[0m`);
        }
      }
    }
  }
}

async function handleRecycle() {
  const recycleMenu = await callPythonTool('blacksmith_action', { action: 'recycle' }, buildGameState());
  if (!recycleMenu.success) {
    console.log(`\\x1b[31m${recycleMenu.message}\\x1b[0m`);
    return;
  }
  const items = recycleMenu.items;
  if (items.length === 0) {
    console.log('No items to recycle.');
    return;
  }
  console.log(`\\n${'\\x1b[1;33m'}Items to recycle:${'\\x1b[0m'}`);
  for (let i = 0; i < items.length; i++) {
    console.log(`${i+1}. ${items[i].name} (${items[i].type})`);
  }
  const itemChoice = await rl.question('Choose item number (or 0 to cancel): ');
  const idx = parseInt(itemChoice) - 1;
  if (idx >= 0 && idx < items.length) {
    const item = items[idx];
    const recycleResult = await callPythonTool('recycle', { item_name: item.name }, buildGameState());
    if (recycleResult.success) {
      console.log(`\\x1b[32m${recycleResult.message}\\x1b[0m`);
      player = recycleResult.player;
    } else {
      console.log(`\\x1b[31m${recycleResult.message}\\x1b[0m`);
    }
  }
}

async function main() {
  printIntro();

  while (true) {
    const nameInput = await rl.question('What is your name, legendary adventurer? ');
    if (nameInput.startsWith('/')) {
      if (nameInput === '/help') {
        console.log('Commands: /help, /inventory, /status, /quests, /lore, /save, /load, /equip, /craft, /dm, /guide, /roll, /cast, /alignment, /blacksmith, /alchemist, /recycle, quit');
        console.log('Enter your name to begin.');
      } else if (nameInput === '/inventory') {
        console.log('You have no inventory yet. Enter your name to start.');
      } else if (nameInput === '/status') {
        console.log('You have no stats yet. Enter your name to start.');
      } else if (nameInput === '/quests') {
        console.log('Quests will appear once you begin your adventure.');
      } else if (nameInput === '/lore') {
        console.log('You have not discovered any lore yet.');
      } else if (nameInput === '/guide') {
        console.log('DungeonClaw Guide: Type actions like "go north", "attack", "search", "craft Goblin Ear Potion". Use /status to see your stats. Save often with /save.');
      } else if (nameInput === '/craft') {
        console.log('Crafting recipes: Goblin Ear Potion (3 Goblin Ears), Minion Essence Potion (2 Minion Essence), Silk Cloth (2 Spider Silk + 5 gold), Orcish Elixir (1 Orc Axe + 10 gold). Also use /blacksmith and /alchemist for advanced crafting.');
      } else if (nameInput === '/dm') {
        console.log('Use /dm once the game starts to switch models.');
      } else {
        console.log('Unknown command. Enter your name to begin.');
      }
    } else {
      playerName = nameInput;
      break;
    }
  }

  console.log(`\\nWelcome, ${playerName}.\\n`);

  let soul = await readSoul();
  await writeSoul(soul, playerName);

  const loaded = await loadGame();
  if (!loaded) {
    currentRoom = 0;
    visited.add(currentRoom);
    try {
      currentRoomMechanics = await callPythonTool('generate_room', { room: currentRoom, dungeon_size: DUNGEON_SIZE, player_level: player.level });
      if (!currentRoomMechanics) throw new Error('Invalid room data');
    } catch (err) {
      console.log('\\x1b[31mError generating initial room. Using default.\\x1b[0m');
      console.error('\\x1b[33mPython error details:\\x1b[0m', (err as Error).message);
      currentRoomMechanics = {
        room_id: 0,
        zone: 'entrance',
        type: 'empty',
        exits: ['north'],
        description: 'A cold, dark room.',
        ambient: '',
        monster: null,
        ground_loot: []
      };
    }
    roomCache.set(currentRoom, currentRoomMechanics);
  }

  const history: HistoryEntry[] = [];

  const lookResult = await callPythonTool('execute_tool', { tool: 'look', args: {}, state: buildGameState() }).catch(err => {
    console.error('\\x1b[33mLook tool Python error:\\x1b[0m', err.message);
    return { description: 'You are in a dark room (fallback).' };
  });
  const initialDesc = lookResult.description || 'You are in a dark room.';
  console.log(`\\nDungeon Master: ${initialDesc}\\n`);

  if (currentRoomMechanics.monster && currentRoomMechanics.monster.hp > 0) {
    combatActive = true;
    console.log(`\\x1b[31m⚔️ Combat starts! ${currentRoomMechanics.monster.name} (HP: ${currentRoomMechanics.monster.hp}) attacks!\\x1b[0m`);
  }

  while (true) {
    const userInput = await rl.question('\\x1b[33m> \\x1b[0m');
    const lower = userInput.toLowerCase().trim();

    if (lower === 'quit' || lower === 'exit') {
      await saveGame();
      console.log('\\nFarewell, legend.\\n');
      break;
    }

    if (lower === '/save') { await saveGame(); continue; }
    if (lower === '/load') { await loadGame(); continue; }
    if (lower === '/dm') { await switchModel(); continue; }
    if (lower === '/status') {
      const alignmentText = player.alignment > 0 ? 'Good' : (player.alignment < 0 ? 'Evil' : 'Neutral');
      console.log(`HP: ${player.hp}/${player.maxHp} | Gold: ${player.gold} | Level: ${player.level} (XP: ${player.xp}/${player.xpToNext}) | Attack: +${player.attack_bonus} | Damage: +${player.damage_bonus} | Defense: +${player.defense_bonus} | Alignment: ${alignmentText}`);
      if (player.weapon) console.log(`Weapon: ${player.weapon.name}`);
      if (player.armor) console.log(`Armor: ${player.armor.name}`);
      if (player.effects.length) console.log(`Effects: ${player.effects.map(e => `${e.name} (${e.duration})`).join(', ')}`);
      continue;
    }
    if (lower === '/inventory') {
      if (player.inventory.length === 0) console.log('Inventory: empty');
      else {
        console.log('Inventory:');
        player.inventory.forEach((item, i) => {
          let name = item.name;
          if (item.tier) name += ` (${item.tier})`;
          if (item.stack && item.stack > 1) name += ` x${item.stack}`;
          console.log(`  ${i+1}. ${name} (${item.type}) - value: ${item.value} gold`);
        });
      }
      continue;
    }
    if (lower === '/quests') {
      if (quests.length === 0) console.log('No active quests.');
      else {
        quests.forEach(q => {
          const status = q.completed ? '✓' : '○';
          console.log(`${status} ${q.name}: ${q.description}`);
          q.objectives.forEach(obj => {
            console.log(`   - ${obj.type} ${obj.target}: ${obj.current}/${obj.required}`);
          });
        });
      }
      continue;
    }
    if (lower === '/lore') {
      if (lore.length === 0) console.log('You have not discovered any lore yet.');
      else {
        console.log('Lore fragments:');
        lore.forEach((frag, i) => console.log(`  ${i+1}. ${frag}`));
      }
      continue;
    }
    if (lower === '/equip') {
      console.log('Equipment:');
      console.log(`  Weapon: ${player.weapon ? player.weapon.name : 'none'}`);
      console.log(`  Armor: ${player.armor ? player.armor.name : 'none'}`);
      console.log('To equip an item, type "equip <item name>"');
      continue;
    }
    if (lower === '/craft') {
      console.log('Crafting recipes:');
      console.log('  - Goblin Ear Potion (3 Goblin Ears)');
      console.log('  - Minion Essence Potion (2 Minion Essence)');
      console.log('  - Silk Cloth (2 Spider Silk + 5 gold)');
      console.log('  - Orcish Elixir (1 Orc Axe + 10 gold)');
      console.log('  - Also use /blacksmith or /alchemist for more crafting options.');
      continue;
    }
    if (lower === '/guide') {
      console.log('Guide: Use commands like "go north", "attack", "search", "craft Goblin Ear Potion". In combat you can also "defend", "flee", "use <item>". Check /status, /inventory, /quests, /lore. Save with /save. Use /dm to change Ollama models. Try /roll d20 for a dice roll, /cast fireball for spells. New: /blacksmith, /alchemist, /recycle for advanced crafting. Good luck!');
      continue;
    }
    if (lower === '/help') {
      console.log('Commands: /status, /inventory, /quests, /lore, /equip, /craft, /dm, /save, /load, /guide, /roll, /cast, /alignment, /blacksmith, /alchemist, /recycle, /help, quit');
      console.log('You can also just tell the agent what to do (e.g., "go north", "attack", "take dagger")');
      continue;
    }
    if (lower === '/roll') {
      const dice = userInput.substring(5).trim() || '1d20';
      const result = await callPythonTool('roll_dice', { dice }).catch(err => ({ error: err.message }));
      if (result.error) console.log(`\\x1b[31mRoll error: ${result.error}\\x1b[0m`);
      else console.log(`\\x1b[36mRoll ${dice}: ${result.total} (${result.rolls.join(', ')})${result.modifier ? (result.modifier > 0 ? `+${result.modifier}` : result.modifier) : ''}\\x1b[0m`);
      continue;
    }
    if (lower === '/cast') {
      const spell = userInput.substring(5).trim();
      if (!spell) console.log('Cast what? Example: /cast fireball');
      else {
        const result = await callPythonTool('cast_spell', { spell, state: buildGameState() }).catch(err => ({ error: err.message }));
        if (result.error) console.log(`\\x1b[31mSpell error: ${result.error}\\x1b[0m`);
        else console.log(`\\x1b[35m${result.message}\\x1b[0m`);
      }
      continue;
    }
    if (lower === '/alignment') {
      const alignmentText = player.alignment > 0 ? 'Good' : (player.alignment < 0 ? 'Evil' : 'Neutral');
      console.log(`Your alignment: ${alignmentText} (${player.alignment})`);
      continue;
    }
    if (lower === '/blacksmith') {
      await handleBlacksmith();
      continue;
    }
    if (lower === '/alchemist') {
      await handleAlchemist();
      continue;
    }
    if (lower === '/recycle') {
      await handleRecycle();
      continue;
    }

    if (combatActive) {
      console.log('(Combat: you can attack, defend, use item, or flee)');
    }

    const step = await runAgentStep(userInput, history, buildGameState());
    if (step.error) {
      console.log(`\\x1b[31mThe agent is confused: ${step.error}. Please try again or rephrase.\\x1b[0m`);
      continue;
    }

    if (step.toolName) {
      const tool = getTool(step.toolName);
      if (!tool) {
        console.log(`\\x1b[31mUnknown tool: ${step.toolName}\\x1b[0m`);
        continue;
      }

      const result = await tool.execute(step.args ?? {}, buildGameState());

      if (result.success) {
        let newState = await applyToolResult(buildGameState(), result);
        player = newState.player;
        currentRoom = newState.currentRoom;
        currentRoomMechanics = newState.room_mechanics;
        visited = new Set(newState.visited);
        quests = newState.quests;
        lore = newState.lore;
        combatActive = newState.combat_active;
        if (newState.room_mechanics) roomCache.set(currentRoom, newState.room_mechanics);

        await checkLevelUp();

        quests = updateQuestProgress(quests, step.toolName, result);
        const { quests: updatedQuests, player: updatedPlayer, completedNames } = checkQuestCompletion(quests, player);
        quests = updatedQuests;
        player = updatedPlayer;

        for (const qname of completedNames) {
          const quest = quests.find(q => q.name === qname);
          if (quest) {
            const rewardStr = `${quest.reward.gold} gold, ${quest.reward.xp} XP${quest.reward.item ? ', ' + quest.reward.item.name : ''}`;
            const prompt = buildQuestCompletePrompt(playerName, qname, rewardStr);
            const narration = await callOllamaText(prompt, '', 0.8, 60);
            console.log(`\\n\\x1b[33mQuest Complete!\\x1b[0m\\n${narration}\\n`);
          }
        }

        await updateMemory(`${step.toolName}: ${result.message.substring(0, 80)}`);

        let outputMessage = result.message;
        if (NARRATOR_ENABLED) {
          const ctx = {
            playerName,
            toolName: step.toolName,
            result,
            room: currentRoomMechanics!,
            player,
            quests,
            lore,
            soul: await readSoul()
          };
          const narrationPrompt = buildNarrationPrompt(ctx);
          const narration = await callOllamaText(narrationPrompt, '', 0.7, 100);
          if (narration) outputMessage = narration;
        }
        console.log(`\\n\\x1b[37mDungeon Master:\\x1b[0m ${outputMessage}\\n`);

        history.push({
          user: userInput,
          agent: `[Used tool ${step.toolName}]`,
          summary: result.message.substring(0, 80),
          toolName: step.toolName,
          timestamp: new Date().toISOString()
        });
        if (history.length > 5) history.shift();

        if (player.hp <= 0) {
          console.log('\\x1b[31mYou have died... Game over.\\x1b[0m');
          break;
        }
      } else {
        console.log(`\\x1b[31mTool error: ${result.message}\\x1b[0m`);
      }
    } else if (step.answer) {
      console.log(`\\nDungeon Master: ${step.answer}\\n`);
      await updateMemory(`Direct answer: ${step.answer.substring(0, 80)}`);
      history.push({
        user: userInput,
        agent: step.answer,
        summary: step.answer.substring(0, 80),
        timestamp: new Date().toISOString()
      });
      if (history.length > 5) history.shift();
    }
  }

  rl.close();
}

main().catch(err => {
  console.error('Fatal error:', err);
  rl.close();
});
'''

# ---------- Python files ----------

GAME_ENGINE_PY = '''#!/usr/bin/env python3
"""
Game Engine for DungeonClaw v6.1 – Full RPG with RAG, dice data, improved combat,
tiered potions, artifacts, crafting, recycling, and NPC menus.
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

# ---------- Minion Name Generation ----------
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
        factor = 1 + (player_level - 1) * 0.3
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
            "loot_table": [{"item": {"name": "Minion Essence", "type": "misc", "value": 3}, "chance": 0.5}],
            "is_minion": True
        }
    else:
        zone_monsters = [m for m in monsters if m.get("zone") == zone]
        if not zone_monsters:
            base = {"name": "Goblin", "base_hp": 10, "base_attack": 3, "base_defense": 2,
                    "damage_range": [2,6], "xp": 25, "gold_range": [5,15], "loot_table": []}
        else:
            base = random.choice(zone_monsters)
        factor = 1 + (player_level - 1) * 0.3
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
    type_weights = {"monster": 60, "treasure": 15, "trap": 10, "shrine": 5, "npc": 5, "empty": 5}
    room_type = random.choices(list(type_weights.keys()), weights=list(type_weights.values()))[0]

    desc_list = templates.get("room_descriptions", ["Room {room_id}"])
    description = random.choice(desc_list).replace("{room_id}", str(room_id))
    ambient_list = templates.get("ambient", [])
    ambient = random.choice(ambient_list) if ambient_list else ""

    monster = None
    if room_type == "monster" or random.random() < 0.7:
        is_minion = random.random() < 0.3
        monster = generate_monster(zone, player_level, is_minion=is_minion)

    ground_loot = generate_ground_loot(zone, player_level)
    npc = generate_npc(zone) if room_type == "npc" and random.random() < 0.5 else None
    trap = generate_trap(zone) if room_type == "trap" else None
    quest_hint = get_quest_hint(zone) if random.random() < 0.2 else None

    pending_quest = None

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
    # Add tiered potions and materials based on zone
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

# ---------- Crafting ----------
RECIPES = {
    "Goblin Ear Potion": {
        "ingredients": [{"name": "Goblin Ear", "count": 3}],
        "result": {"name": "Goblin Ear Potion", "type": "consumable", "effect": "heal", "value": 10, "consumable": True}
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

# ---------- Recycling ----------
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
        count = max(1, value // 10)
        materials.append({"name": scrap_type, "count": count})
        if item.get("unique"):
            materials.append({"name": "Enchanted Dust", "count": 1})
    elif item["type"] == "consumable":
        if "potion" in item["name"].lower():
            materials.append({"name": "Herb Bundle", "count": max(1, value // 10)})
            materials.append({"name": "Essence", "count": 1})
        else:
            materials.append({"name": "Enchanted Dust", "count": max(1, value // 20)})
    else:
        materials.append({"name": "Misc Scrap", "count": 1})
    for mat in materials:
        for _ in range(mat["count"]):
            player["inventory"].append({"name": mat["name"], "type": "misc", "value": 1, "consumable": False})
    player["inventory"] = [i for i in player["inventory"] if i["name"] != item["name"]]
    material_str = ', '.join([f"{m['count']}x {m['name']}" for m in materials])
    return {"success": True, "message": f"You recycle {item['name']} and receive {material_str}.", "player": player}

# ---------- Blacksmith ----------
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
        cost_gold = 100 + (upgrade_level * 50)
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

# ---------- Alchemist ----------
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
def find_item_by_name(item_name, inventory, cutoff=0.6):
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

# ---------- Combat Action ----------
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
            damage = random.randint(monster["damage_range"][0], monster["damage_range"][1]) + damage_bonus
            if roll == 20:
                damage *= 2
                crit_msg = " Critical hit!"
            else:
                crit_msg = ""
            monster["hp"] -= damage
            msg = f"You attack the {monster_name} and hit for {damage} damage!{crit_msg}"
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
                    new_monster = generate_monster(mech["zone"], player["level"], is_minion=random.random()<0.3)
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
                    "dice": {"notation": "1d20", "rolls": rolls, "total": total_attack, "modifier": attack_bonus},
                    "round_summary": {
                        "player_roll": roll, "player_hit": True,
                        "player_damage": damage, "critical": roll == 20
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
                    monster_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
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
                        "player_roll": roll, "player_hit": True, "player_damage": damage,
                        "monster_roll": monster_roll, "monster_hit": monster_attack >= player_ac,
                        "monster_damage": monster_damage, "critical": roll == 20
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
                monster_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
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
            monster_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
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
            monster_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
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
        monster_cr = monster.get("cr", monster["attack"])
        flee_bonus = player.get("level", 1) - monster_cr // 2
        flee_total = flee_roll["total"] + max(-3, min(3, flee_bonus))
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
        monster_damage = random.randint(monster["damage_range"][0], monster["damage_range"][1])
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

# ---------- Other Tools ----------
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
    heal = random.randint(5, 15)
    player = state["player"]
    max_hp = player.get("maxHp", 100)
    player["hp"] = min(max_hp, player["hp"] + heal)
    return {"success": True, "message": f"You rest and recover {heal} HP.", "player": player}

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
    quest["reward"]["xp"] = int(quest["reward"]["xp"] * (1 + player_level/10))
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
'''

STORY_GEN_PY = '''#!/usr/bin/env python3
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
'''

EXPAND_TEMPLATES_PY = '''#!/usr/bin/env python3
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
'''

TEMPLATES_PY = '''#!/usr/bin/env python3
"""
templates.py – Base templates + expansion for DungeonClaw v6.0.
Includes minion generator, crafting recipes, unique artifacts, expanded story/quest content.
Run this script to generate the expanded templates.json file.
"""
import json
import random
import copy

# ======================================================================
# 1. BASE TEMPLATES – v6.0 data (massively expanded)
# ======================================================================
BASE = {
  "room_descriptions": [
    "You enter a dusty chamber lit by flickering torches. Room {room_id} smells of old stone.",
    "This circular room has a high ceiling. Water drips somewhere in the darkness.",
    "A collapsed corridor leads into Room {room_id}. Cobwebs cling to the walls.",
    "Torchlight reveals ancient runes on the walls of Room {room_id}.",
    "You stand in a small stone cell. Chains hang from the ceiling.",
    "The floor of Room {room_id} is covered in shattered tiles that once formed a map.",
    "You step into the majestic Throne Hall of the Lost Empire, Room {room_id}, where the ghost of the king watches.",
    "You enter the Forbidden Temple of Forgotten Gods, Room {room_id}, altars covered in moss and offerings.",
    "You descend into the Goblin King's Lair, Room {room_id}, littered with stolen treasures and crude traps.",
    "You discover the Elven Sanctuary within the dungeon, Room {room_id}, trees growing from stone with magical glow.",
    "You find the Dwarven Forge Hall, Room {room_id}, anvils still hot from ancient craftsmanship.",
    "You arrive at the Necromancer's Crypt, Room {room_id}, coffins lining the walls with eerie green light.",
    "You walk into the Enchanted Library, Room {room_id}, books floating and whispering spells.",
    "You reach the Lava Chamber, Room {room_id}, rivers of molten rock and fire elementals dancing.",
    "You explore the Frozen Vault, Room {room_id}, icicles like spears and frost giants' footprints.",
    "You enter the Underwater Grotto, Room {room_id}, bubbles and sunken ships from ages past.",
    "You stand in the Illusionary Maze, Room {room_id}, mirrors showing your deepest fears.",
    "You come upon the Beast Arena, Room {room_id}, bloodstained sand and cheering echoes.",
    "You discover the Starlit Observatory, Room {room_id}, telescope pointing to otherworldly stars.",
    "You enter the Alchemist's Lab, Room {room_id}, potions bubbling with rainbow colors.",
    "You reach the Portal Room, Room {room_id}, swirling vortexes to parallel dungeons.",
    "You step into the Haunted Ballroom, Room {room_id}, ghostly dancers waltzing in silence.",
    "You find the Armory of Legends, Room {room_id}, weapons of heroes past humming with power.",
    "You enter the Vine-Choked Garden, Room {room_id}, carnivorous plants reaching for you.",
    "You arrive at the Shadow Realm Gate, Room {room_id}, darkness that seems alive.",
    "You explore the Treasure Vault of the Lich, Room {room_id}, traps and riches beyond measure.",
    "You stand in the Rune-Engraved Hall, Room {room_id}, magic words that can be activated.",
    "You enter the Spider Queen's Web, Room {room_id}, sticky strands and egg sacs everywhere.",
    "You reach the Griffin Nest, Room {room_id}, feathers and eggs on a high ledge.",
    "You discover the Oracle's Pool, Room {room_id}, waters that show visions of the future.",
    "You enter the Bandit Hideout, Room {room_id}, campfires and stolen goods in crates.",
    "You step into the Minotaur's Labyrinth extension, Room {room_id}, walls shifting slightly.",
    "You find the Phoenix Altar, Room {room_id}, flames that never die.",
    "You arrive at the Mermaid Lagoon, Room {room_id}, even in the depths.",
    "You explore the Giant's Kitchen, Room {room_id}, huge pots and massive bones.",
    "You enter the Vampire's Coffin Chamber, Room {room_id}, luxurious but deadly.",
    "You reach the Fairy Ring Clearing, Room {room_id}, mushrooms and tiny lights dancing.",
    "You discover the Demon Summoning Circle, Room {room_id}, blood runes still active.",
    "You stand in the Bard's Tavern Ruins, Room {room_id}, broken mugs and songs in the air.",
    "You enter the Knight's Tomb, Room {room_id}, armor standing sentinel over a coffin.",
    "You find the Wizard's Tower Base, Room {room_id}, spiral stairs leading up into shadow.",
    "You arrive at the Orc Warcamp, Room {room_id}, battle banners and war drums.",
    "You explore the Angelic Shrine, Room {room_id}, holy light piercing the dark.",
    "You step into the Troll Bridge Room, Room {room_id}, river rushing below.",
    "You reach the Basilisk Den, Room {room_id}, petrified statues everywhere.",
    "You enter the Harpy Nest, Room {room_id}, feathers and distant screams.",
    "You discover the Golem Factory, Room {room_id}, inactive stone guardians in rows.",
    "You find the Dragon Egg Chamber, Room {room_id}, warmth and immense potential.",
    "You arrive at the Lich's Throne, Room {room_id}, the ultimate boss room hint.",
    "You explore the Time-Warped Room, Room {room_id}, clocks running backward.",
    "You enter the Elemental Convergence, Room {room_id}, all four elements in balance.",
    "You step into the Curse-Breaking Altar, Room {room_id}, glowing with desperate hope.",
    "You reach the Lost City Plaza, Room {room_id}, ruins of a once-great civilization.",
    "You find the Secret Rebel Hideout, Room {room_id}, maps of escape routes pinned to stone.",
    "You discover the Holy Grail Chamber, Room {room_id}, legendary artifact pulsing gold.",
    "You enter the Dark Mirror Realm, Room {room_id}, evil versions of yourself stare back.",
    "You arrive at the Unicorn Grove, Room {room_id}, pure magic fills the air.",
    "You explore the Werewolf Pack Den, Room {room_id}, full moon effect even underground.",
    "You stand in the Sorceress' Boudoir, Room {room_id}, perfumes and forbidden spells.",
    "You descend into the Plague Pit, Room {room_id}, rotting bones and green miasma rise.",
    "You enter the Colosseum of Ancients, Room {room_id}, spectral crowds cheer every move.",
    "You find the Shadowmancer's Study, Room {room_id}, tomes written in blood and starlight.",
    "You arrive at the Sunken Cathedral, Room {room_id}, holy water corrupted to black ink.",
    "You reach the Mindflayer's Sanctum, Room {room_id}, psychic energy warps the very air.",
    "You enter the Abyssal Chasm Rim, Room {room_id}, infinite darkness yawns below.",
    "You discover the War Council Chamber, Room {room_id}, a map of the dungeon carved in bone.",
    "You step into the Corrupted Garden, Room {room_id}, twisted flowers that drain life.",
    "You find the Hall of Fallen Kings, Room {room_id}, stone thrones with skeletal rulers.",
    "You arrive at the Crucible of Souls, Room {room_id}, spirits trapped in crystalline walls.",
    "You enter the Rusted Iron Workshop, Room {room_id}, abandoned siege weapons half-assembled.",
    "You reach the Astral Projection Room, Room {room_id}, your spirit nearly leaves your body.",
    "You discover the Petrified Forest, Room {room_id}, stone trees with eyes that follow you.",
    "You explore the Wyvern Roost, Room {room_id}, acid scorch marks on every surface.",
    "You stand in the Blood Sacrifice Chamber, Room {room_id}, stained altars and broken chains.",
    "You enter the Arcanist's Workshop, Room {room_id}, half-finished enchantments flicker.",
    "You find the Crypt of the Betrayer, Room {room_id}, a traitor's name etched in every stone.",
    "You arrive at the Elemental Prison, Room {room_id}, four cells holding bound spirits.",
    "You reach the Hall of Memories, Room {room_id}, visions of the past play in the walls.",
    "You discover the Broken Clockwork Chamber, Room {room_id}, gears and springs litter the floor.",
    "You enter the Serpent's Coil, Room {room_id}, shed skins the size of boats hang here.",
    "You step into the Tide-Stone Cavern, Room {room_id}, salt and the crash of unseen waves.",
  ],
  "ambient": [
    "You hear distant footsteps.",
    "A rat scurries across the floor.",
    "The torchlight flickers in a sudden draft.",
    "Something scrapes behind the wall.",
    "A low growl echoes from deeper in the dungeon.",
    "The roar of a mighty dragon shakes the walls.",
    "Whispers of lost souls fill the air.",
    "The clink of chains from unseen prisoners echoes.",
    "Magic sparks fly from cracked walls.",
    "A chill wind carries the scent of ancient battles.",
    "Distant war drums thunder through the stone.",
    "The cry of a banshee pierces the silence.",
    "Flames crackle from an unseen brazier.",
    "Water drips like the tears of fallen gods.",
    "A spectral choir chants forgotten hymns.",
    "The ground trembles beneath your boots.",
    "Invisible hands brush against your neck.",
    "The scent of brimstone and roses wafts by.",
    "Echoes of clashing swords ring out.",
    "A raven caws three times from the shadows.",
    "Lightning crackles in the ceiling runes.",
    "The air grows thick with mana.",
    "A lone wolf howls far above.",
    "Chains rattle as if pulled by ghosts.",
    "The walls seem to breathe slowly.",
    "Fairy bells tinkle in the darkness.",
    "A deep bass rumble like a sleeping titan.",
    "The smell of fresh blood and iron.",
    "Wind howls through hidden vents.",
    "A child's laughter echoes eerily.",
    "The temperature drops to freezing.",
    "Golden dust motes swirl in torchlight.",
    "A distant bell tolls for the dead.",
    "The floor vibrates with hoofbeats.",
    "Whispers call your name softly.",
    "A phoenix cry echoes from above.",
    "The scent of old books and decay.",
    "Stalactites drip glowing ichor.",
    "A harp plays a mournful tune alone.",
    "The air tastes of ozone and magic.",
    "Shadows lengthen unnaturally.",
    "A dragon's distant snort rumbles.",
    "The ground cracks with tiny tremors.",
    "Faint elven singing drifts by.",
    "The smell of roasting meat and herbs.",
    "A sudden gust carries rose petals.",
    "The walls weep crimson tears.",
    "A spectral knight passes through you.",
    "Thunder rolls with no storm above.",
    "The smell of sulphur and ash rises from below.",
    "You hear the grinding of massive gears somewhere deep.",
    "A strange purple light pulses rhythmically in the dark.",
    "The echo of an enormous heartbeat fills the room.",
    "You smell fresh pine impossibly far underground.",
    "A coin spins endlessly on the stone floor ahead.",
    "Tiny glowing insects swarm and spell out a warning.",
    "The sound of sobbing comes from inside the walls.",
    "Every shadow moves exactly one second too slow.",
    "A crow lands nearby, stares, then vanishes in smoke.",
    "Ice crystals form on every surface simultaneously.",
    "The floor hums as if the dungeon itself is singing.",
    "You hear a lock turning with no door in sight.",
    "The torches burn green for a fleeting moment.",
    "An invisible presence exhales on your shoulder.",
    "You catch the unmistakable scent of lightning.",
    "The sound of shattering glass echoes with no source.",
    "A mote of pure darkness drifts slowly past.",
    "Something large and heavy rolls through a hidden passage.",
    "You hear whispered counting, backwards from ten.",
    "The temperature spikes to unbearable heat and vanishes.",
    "A drumbeat synchronizes with your heartbeat briefly.",
    "The walls flash with ancient battle scenes for an instant.",
    "You hear the distinct clatter of a dropped weapon nearby.",
    "The runes on the floor glow faintly when you step near.",
    "A distant explosion shakes loose dust from the ceiling.",
    "You detect the faint perfume of something inhuman.",
    "A baby's cry echoes once, then absolute silence falls.",
    "The puddle on the floor ripples with no disturbance.",
  ],
  "action_responses": [
    "You {action}. Nothing happens.",
    "As you {action}, you notice a faint glow in the corner.",
    "Your attempt to {action} fails, but you feel you're on the right track.",
    "You {action}. Rolled 1d20: 15. A lever clicks! The path north glows faintly.",
    "You {action}. Rolled 1d20: 4. The floor creaks but nothing changes. Try looking around.",
    "You {action} and the dungeon responds with a low rumble. A new passage seems to have opened.",
    "You {action}. Rolled 1d20: 20. Critical success! The gods smile upon you as a portal opens.",
    "You {action} and awaken a hidden guardian spirit who grants you a blessing.",
    "Your {action} triggers a cascade of falling gems from the ceiling.",
    "You {action}. Rolled 1d20: 18. The wall slides open revealing a secret vault.",
    "You {action} and the runes flare to life, granting temporary vision of the future.",
    "Your {action} disturbs a nest of glowing fireflies that light the way ahead.",
    "You {action}. Rolled 1d20: 12. A faint draft reveals a hidden alcove.",
    "You {action} and the dungeon itself seems pleased, healing a small wound.",
    "Your {action} summons a spectral guide who points north with a bony finger.",
    "You {action}. Rolled 1d20: 7. Trap springs but you dodge with heroic grace.",
    "You {action} and ancient words appear in the air spelling a clue.",
    "Your {action} causes the floor to shift into a magical elevator.",
    "You {action}. Rolled 1d20: 19. A legendary artifact pulses into existence.",
    "You {action} and the shadows part to reveal a forgotten map.",
    "Your {action} awakens a friendly sprite that offers a riddle.",
    "You {action}. Rolled 1d20: 3. Nothing... but you feel watched.",
    "You {action} and golden coins rain from a crack in the ceiling.",
    "Your {action} aligns the stars above, opening a celestial gate.",
    "You {action}. Rolled 1d20: 16. The beast nearby retreats in fear.",
    "You {action} and the air fills with the scent of victory.",
    "Your {action} causes a suit of armor to bow and offer its sword.",
    "You {action}. Rolled 1d20: 14. A lever clicks and torches ignite ahead.",
    "You {action} and the dungeon whispers a prophecy in your ear.",
    "Your {action} summons a swarm of helpful bats to scout ahead.",
    "You {action}. Rolled 1d20: 9. A minor trap nicks you but reveals loot.",
    "You {action} and the walls bloom with glowing flowers.",
    "Your {action} causes a mirror to show the next room clearly.",
    "You {action}. Rolled 1d20: 17. A secret door swings wide open.",
    "You {action} and the spirit of a fallen hero salutes you.",
    "Your {action} triggers a burst of healing light from above.",
    "You {action}. Rolled 1d20: 11. The path ahead glows faintly.",
    "You {action} and ancient guardians stand aside in respect.",
    "Your {action} summons a tiny dragon that perches on your shoulder.",
    "You {action}. Rolled 1d20: 13. A chest materializes with a click.",
    "You {action} and the dungeon rewards you with a vision of glory.",
    "Your {action} causes runes to burn a map onto your palm.",
    "You {action}. Rolled 1d20: 8. The floor creaks... but a lever appears.",
    "You {action} and the air shimmers with protective magic.",
    "Your {action} awakens a chorus of angelic voices guiding you.",
    "You {action}. Rolled 1d20: 10. Nothing changes... yet.",
    "You {action} and the shadows form a helpful arrow pointing north.",
    "Your {action} causes a fountain of youth to bubble up.",
    "You {action}. Rolled 1d20: 6. A minor setback but you gain wisdom.",
    "You {action} and the dungeon itself bows to your courage.",
    "Your {action} summons a spectral steed for the next leg.",
    "You {action}. Rolled 1d20: 2. The gods test your patience.",
    "You {action} and a rainbow bridge forms across a chasm.",
    "Your {action} causes the ceiling to rain healing herbs.",
    "You {action}. Rolled 1d20: 19. Epic success! The path clears dramatically.",
    "You {action} and the spirit of an ancient king knights you.",
    "Your {action} awakens the dungeon's heart, pulsing with power.",
    "You {action}. Rolled 1d20: 20. The very stars rearrange to guide you forward.",
    "Your {action} breaks a hidden seal — a staircase descends into new territory.",
    "You {action} and the memory of a dead hero floods your mind with tactical insight.",
    "You {action}. Rolled 1d20: 15. A hidden pressure plate clicks — the west wall shatters.",
    "Your {action} resonates with the dungeon's core. You feel stronger, wiser, faster.",
    "You {action} and the floor beneath you turns to glass, revealing a room below.",
    "You {action}. Rolled 1d20: 18. A phantom locksmith appears and opens a sealed chest.",
    "Your {action} causes every torch in this wing to ignite simultaneously.",
    "You {action} and a ghostly hand deposits a key in your palm.",
    "You {action}. Rolled 1d20: 11. The ceiling blooms with star-maps of the dungeon.",
    "Your {action} triggers a cascade of runes that fortify your armor temporarily.",
    "You {action} and a deep voice intones: 'The worthy shall pass.'",
    "You {action}. Rolled 1d20: 16. An ancient booby trap disarms itself before you.",
    "Your {action} summons a phantom merchant offering three rare items.",
    "You {action} and the air solidifies into a stepping-stone path across a pit.",
    "You {action}. Rolled 1d20: 5. The floor shifts — new room layout detected!",
  ],
  "monster_encounters": [
    "A bloodthirsty Orc Berserker charges at you in Room {room_id}!",
    "A ghostly Specter materializes, draining the life from the air around you.",
    "A massive Minotaur snorts and lowers its horns in Room {room_id}.",
    "A pack of glowing Shadow Wolves circles you silently.",
    "A colossal Stone Golem awakens with grinding stone joints.",
    "A seductive Succubus steps from the shadows with a wicked smile.",
    "A fiery Hellhound bounds forward, eyes like burning coals.",
    "A skeletal Lich raises a staff crackling with death magic.",
    "A swarm of giant Venomous Spiders descends from the ceiling.",
    "A majestic but enraged Griffin spreads its wings.",
    "A slimy Tentacle Beast rises from a hidden pool.",
    "A cunning Goblin Shaman chants dark curses at you.",
    "A towering Troll regenerates before your very eyes.",
    "A Basilisk stares with its petrifying gaze.",
    "A Harpy flock screeches overhead.",
    "An ancient Dragon Wyrmling uncoils from its hoard.",
    "A Vampire Lord steps into torchlight with fangs bared.",
    "A pack of Werewolves howls under an unseen moon.",
    "A Demon Knight in blackened plate armor advances.",
    "A Phoenix reborn in flames circles above.",
    "A massive Iron Golem slams its fists into the ground.",
    "A swarm of Undead Skeletons rises from the floor.",
    "A cunning Doppelganger mimics your form perfectly.",
    "A Frost Giant swings a massive icy club.",
    "A swarm of Plague Rats surges forward.",
    "A majestic Unicorn corrupted by shadow charges.",
    "A Cyclops with a single glowing eye blocks the path.",
    "A Wraith Lord floats through the walls.",
    "A pack of Hellcats with flaming tails pounces.",
    "An Elemental of pure lightning crackles into existence.",
    "A Bone Dragon assembles itself from scattered remains in Room {room_id}!",
    "A Chaos Imp laughs maniacally and hurls hexes at you.",
    "A Plague Zombie shuffles forward oozing black bile.",
    "A Rune Golem shakes the floor with each ponderous step.",
    "A Shadow Assassin drops from the ceiling blades-first.",
    "A Soul Devourer opens a void mouth aimed at your chest.",
    "A Spectral Warlord appears astride a phantom warhorse.",
    "A Blood Witch traces sigils in the air with dripping fingers.",
    "A Titan Crab emerges from a crack in Room {room_id}'s floor!",
    "A Serpent Hydra sprouts two new heads every time you strike.",
    "A Mindworm burrows into the air trying to reach your skull.",
    "A Cursed Paladin in broken holy armor advances with divine fury.",
    "A Living Dungeon Wall extends stone limbs to crush you.",
    "An Ancient Revenant rises, remembering every hero it has slain.",
    "A Chaos Elemental rearranges reality around its form.",
    "A Hollow Knight — empty armor animated by dark will — charges.",
    "A Star-Touched Behemoth radiates cosmic energy from its wounds.",
    "A Dream Stalker steps from your own shadow in Room {room_id}.",
    "A Forge Demon of living magma erupts from the floor.",
    "A Thunder Drake spreads wings that generate stormclouds.",
  ],
  "loot_descriptions": [
    "You discover a gleaming Elven Longsword enchanted with +2 to attack rolls in Room {room_id}.",
    "A pouch of 100 ancient gold pieces stamped with lost empire seals.",
    "A shimmering Potion of Healing that glows with inner light.",
    "A Ring of Invisibility carved with dwarven runes.",
    "A Cloak of Protection woven from phoenix feathers.",
    "A Wand of Fireballs etched with draconic script.",
    "A legendary Shield of the Paladin radiating holy light.",
    "A Bag of Holding that seems bottomless.",
    "A Scroll of Teleportation to a safe haven.",
    "A pair of Boots of Speed that hum with magic.",
    "An Amulet of Health that pulses with life energy.",
    "A Helm of True Sight that pierces illusions.",
    "A Gauntlet of Strength forged in the fires of Mount Doom.",
    "A Harp of Charming that plays itself.",
    "A Tome of Ancient Knowledge bound in dragonhide.",
    "A Dagger of Venom dripping with green ichor.",
    "A Crown of Leadership that inspires allies.",
    "A Belt of Giant Strength made from troll hide.",
    "A Necklace of Fireballs ready to explode.",
    "A pair of Gloves of Thievery that never miss.",
    "A Mirror of Scrying that shows distant lands.",
    "A Staff of Healing carved with angelic symbols.",
    "A Bow of the Elven Rangers that never misses.",
    "A set of Plate Armor blessed by the gods.",
    "A Chest overflowing with 500 gold and gems.",
    "A Crystal Ball that shows possible futures.",
    "A Horn of Summoning that calls allies to battle.",
    "A Lute of Inspiration that boosts morale.",
    "A pair of Wings of Flying folded neatly.",
    "A legendary Artifact: the Eye of the Beholder.",
    "You find a Shadowblade that deals bonus damage in darkness in Room {room_id}.",
    "A Philosopher's Stone that turns iron into gold.",
    "A Cloak of the Void that lets you pass through walls once per day.",
    "A Scepter of Storms that calls lightning on command.",
    "A pair of Sandals of the Wind God, granting immense speed.",
    "A Tome of Forbidden Summoning sealed with seven locks.",
    "A Heartstone Pendant that beats with protective life energy.",
    "A Runic Battleaxe etched with names of a hundred fallen foes.",
    "A Goblet of Endurance that permanently boosts stamina.",
    "A set of Shadowweave Armor that repairs itself over time.",
    "A Compass of True North that points to the dungeon's heart.",
    "A Vial of Dragon's Blood that grants temporary fire immunity.",
    "A Bone Whistle that summons a skeletal horse.",
    "A Mask of the Deceiver that changes your appearance.",
    "A Ring of Spell Storing holding three uncast fireballs.",
    "A Pauldron of the Titan, impossibly strong shoulder armor.",
    "A Rune-Scribed Tower Shield carved from the wood of a World Tree.",
    "A Dwarven Master Key that opens any lock in the dungeon.",
    "A Celestial Longbow that fires arrows of pure starlight.",
    "A Bracer of Arcane Deflection that reduces spell damage.",
  ],
  "combat_responses": [
    "You {action} the {monster}. Rolled 1d20: {roll}. It hits hard, the {monster} reels in pain!",
    "Your {action} connects with a thunderous crack against the {monster}!",
    "You {action} the {monster}. Rolled 1d20: {roll}. Critical hit! Blood sprays dramatically.",
    "The {monster} dodges your {action} but you graze its flank.",
    "You {action} the {monster} with divine fury. Rolled 1d20: {roll}. The gods approve!",
    "Your {action} causes the {monster} to roar in agony and stagger back.",
    "You {action} the {monster}. Rolled 1d20: {roll}. The beast is gravely wounded.",
    "The {monster} blocks your {action} but you see fear in its eyes.",
    "You {action} with heroic precision. Rolled 1d20: {roll}. The {monster} collapses!",
    "Your {action} summons a burst of arcane energy that scorches the {monster}.",
    "You {action} the {monster}. Rolled 1d20: {roll}. It howls and flees into the dark.",
    "The {monster} counters your {action} but you stand firm.",
    "You {action} with the fury of ancient heroes. Rolled 1d20: {roll}. Epic strike!",
    "Your {action} causes the {monster} to shatter into shadow and dust.",
    "You {action} the {monster}. Rolled 1d20: {roll}. It bleeds black ichor.",
    "The {monster} laughs at your {action} but then staggers.",
    "You {action} and the dungeon itself aids you with a surge of power.",
    "Your {action} pierces the {monster}'s defenses perfectly.",
    "You {action} the {monster}. Rolled 1d20: {roll}. It falls to one knee.",
    "The {monster} roars in defiance at your {action}.",
    "You {action} with legendary skill. Rolled 1d20: {roll}. Victory is near!",
    "Your {action} causes the {monster} to burst into flames.",
    "You {action} the {monster}. Rolled 1d20: {roll}. It howls and vanishes.",
    "The {monster} takes your {action} and grows even angrier.",
    "You {action} and the {monster} is banished to the void.",
    "Your {action} summons ancestral spirits to strike the {monster}.",
    "You {action} the {monster}. Rolled 1d20: {roll}. The blow echoes forever.",
    "The {monster} is staggered by your mighty {action}.",
    "You {action} with the power of the gods themselves.",
    "Your {action} ends the {monster}'s reign of terror permanently.",
    "You {action} the {monster}. Rolled 1d20: {roll}. The {monster} erupts in spectral flame!",
    "Your {action} freezes the {monster} in a sheath of arcane ice!",
    "You {action} and the {monster} is hurled into the wall by unseen force.",
    "Your {action} disarms the {monster} — its weapon clatters away.",
    "You {action} the {monster}. Rolled 1d20: {roll}. A killing blow echoes through the dungeon!",
    "Your {action} severs the {monster}'s connection to dark power.",
    "You {action} the {monster}. Rolled 1d20: {roll}. It screams in a language not spoken for millennia.",
    "Your {action} draws a roar from the very walls as the {monster} crumbles.",
    "You {action} with ancestral fury. Rolled 1d20: {roll}. The {monster} begs for quarter.",
    "Your {action} leaves the {monster} stunned, and the dungeon holds its breath.",
  ],
  "trap_responses": [
    "You {action} and trigger an arrow trap! Rolled 1d20: {roll}. You dodge most but take 5 damage.",
    "A pit opens beneath you after your {action}! Rolled 1d20: {roll}. You barely hang on.",
    "Poison gas hisses from the walls after you {action}. Rolled 1d20: {roll}.",
    "A swinging blade trap activates from your {action}! Rolled 1d20: {roll}.",
    "You {action} and the ceiling collapses in a shower of boulders.",
    "A magical glyph explodes after your {action}! Rolled 1d20: {roll}.",
    "Spikes shoot from the floor after you {action}. Rolled 1d20: {roll}.",
    "You {action} and awaken a horde of tiny biting imps.",
    "A rolling boulder trap rumbles toward you after your {action}!",
    "Cursed runes burn your skin after you {action}. Rolled 1d20: {roll}.",
    "You {action} and the floor turns to quicksand.",
    "A spectral trap drains your life force after {action}.",
    "You {action} and acid sprays from hidden vents.",
    "A net of enchanted webs drops after your {action}.",
    "You {action} and the walls close in like a vice.",
    "Lightning strikes from the ceiling after you {action}. Rolled 1d20: {roll}.",
    "You {action} and a swarm of spectral bats attacks.",
    "A collapsing bridge trap activates after your {action}!",
    "You {action} and the air fills with paralyzing spores.",
    "A hidden golem guardian activates after you {action}.",
    "You {action} and the room floods with freezing water.",
    "Fire jets erupt from the floor after your {action}.",
    "You {action} and a curse of blindness falls upon you.",
    "A horde of undead hands grab your ankles after {action}.",
    "You {action} and the entire room spins wildly.",
    "A demonic portal opens after your {action}. Rolled 1d20: {roll}.",
    "You {action} and razor-sharp vines entangle you.",
    "A sonic boom trap shatters your eardrums after {action}.",
    "You {action} and the room fills with illusions of terror.",
    "A final ancient trap of pure arcane fury activates!",
    "You {action} and a gravity reversal trap pins you to the ceiling!",
    "A shrieking siren trap after your {action} draws every monster nearby.",
    "You {action} and a memory curse makes you forget the last room.",
    "A teleportation rune triggers after {action} — you arrive in the deepest zone!",
    "You {action} and a time-slow field traps you for one full round.",
    "A leeching mist after {action} drains your gold slowly. Rolled 1d20: {roll}.",
    "You {action} and a cursed mirror creates a hostile copy of you.",
    "Skeletal arms burst from the walls after {action}. Rolled 1d20: {roll}.",
    "You {action} and the torch goes out — total darkness for ten seconds.",
    "A wish trap after your {action} grants one boon and one curse simultaneously.",
  ],
  "npc_dialogues": [
    "The {npc_type} whispers: 'The dragon sleeps... but not for long.'",
    "The {npc_type} says: 'Take the left path, hero. The right leads to certain doom.'",
    "The {npc_type} offers: 'For a single gold coin I will tell you the secret password.'",
    "The {npc_type} chants: 'Beware the one who wears the crown of bones.'",
    "The {npc_type} smiles: 'I was once like you... now I am eternal.'",
    "The {npc_type} warns: 'The lich awaits in Room 49. Bring fire and faith.'",
    "The {npc_type} laughs: 'All who enter leave changed... or not at all.'",
    "The {npc_type} recites: 'Three keys, three trials, three deaths await.'",
    "The {npc_type} murmurs: 'The gods are watching. Make them proud.'",
    "The {npc_type} offers a riddle and a blessing if solved.",
    "The {npc_type} pleads: 'Find my stolen tome and I will teach you a spell.'",
    "The {npc_type} confesses: 'I helped build this dungeon. The lich tricked us all.'",
    "The {npc_type} screams: 'Run! The walls have ears and the ears have teeth!'",
    "The {npc_type} bargains: 'Spare me and I'll show you where they hid the second key.'",
    "The {npc_type} laments: 'I have wandered here for a hundred years. Help me rest.'",
    "The {npc_type} hisses: 'The Goblin King is only a puppet. Look deeper.'",
    "The {npc_type} sings softly: 'Four seals, four guardians, four truths unspoken.'",
    "The {npc_type} warns: 'Do not speak your name aloud in Room 33. It feeds the echo.'",
    "The {npc_type} beams: 'You carry the mark of destiny. Even I can see it.'",
    "The {npc_type} trades: 'A Dragon Scale for a map to the phylactery's hiding spot.'",
    "The {npc_type} mutters: 'The dungeon shifts on the equinox. Today is the equinox.'",
    "The {npc_type} advises: 'Armor of faith repels the lich's touch better than steel.'",
    "The {npc_type} cryptically says: 'The answer lies in the question you haven't asked yet.'",
    "The {npc_type} grins: 'I bet you can't survive Room 40. I've lost that bet before.'",
    "The {npc_type} weeps: 'My companions were taken. Avenge them and take what was theirs.'",
    "The {npc_type} reveals: 'There is a second dungeon beneath this one. Few know it exists.'",
    "The {npc_type} recants: 'I served the lich willingly. Now I suffer for it. Learn from me.'",
    "The {npc_type} entrusts: 'This key opens nothing you have yet found. Keep it safe.'",
    "The {npc_type} urges: 'The sealed door in the deep zone hides the lich's true name.'",
    "The {npc_type} prophesies: 'You will die in this dungeon — but not today. Not here.'",
  ],
  "riddles": [
    "What has keys but can't open locks? (A piano)",
    "I speak without a mouth and hear without ears. I have no eyes, yet I can see the future. What am I? (An echo)",
    "The more you take, the more you leave behind. What am I? (Footsteps)",
    "What can travel around the world while staying in a corner? (A stamp)",
    "I have cities but no houses, forests but no trees, rivers but no water. What am I? (A map)",
    "What has a head, a tail, is brown, and has no legs? (A penny)",
    "What can you break, even if you never pick it up or touch it? (A promise)",
    "What has many keys but can't open a single door? (A keyboard)",
    "I am taken from a mine, shut up in a wooden case, and used by almost every person. What am I? (Pencil lead)",
    "The person who makes it, sells it. The person who buys it never uses it. The person who uses it doesn't know. What is it? (A coffin)",
    "I have no body but I consume all. What am I? (Fire)",
    "I grow shorter as I grow older. What am I? (A candle)",
    "The more you have of me, the less you see. What am I? (Darkness)",
    "I can be cracked, made, told, and played. What am I? (A joke)",
    "I run but have no legs. I have a mouth but never speak. What am I? (A river)",
    "What is always coming but never arrives? (Tomorrow)",
    "I have hands but cannot clap. What am I? (A clock)",
    "What gets wetter as it dries? (A towel)",
    "I have teeth but cannot bite. What am I? (A comb)",
    "What is full of holes but still holds water? (A sponge)",
    "What can you hold in your right hand but not in your left? (Your left hand)",
    "I have one eye but cannot see. What am I? (A needle)",
    "What flies without wings? (Time)",
    "I am not alive, but I can grow. I don't have lungs, but I need air. What am I? (Fire)",
    "What has four legs in the morning, two at noon, and three in the evening? (A person)",
    "I vanish when you name me. What am I? (Silence)",
    "What begins with E, ends with E, and contains one letter? (An envelope)",
    "The king's magician speaks truth, the jester speaks only lies. You may ask one yes/no question. How do you find the right path? (Ask either: what would the other say?)",
    "I have mountains with no stone, oceans with no water, towns with no houses. What am I? (A map)",
    "Feed me and I grow. Give me water and I die. What am I? (A fire)",
  ],
  "prophecies": [
    "The stars foretell: a hero shall rise where the dragon falls.",
    "In the deepest dark, light shall be born from courage alone.",
    "The crown of bones will shatter on the day of the true king.",
    "When the last phoenix sings, the dungeon shall open its heart.",
    "Beware the mirror that lies. Trust only the sword in your hand.",
    "The gods will laugh when the lich begs for mercy.",
    "A single gold coin will decide the fate of empires.",
    "The shadows walk when the moon bleeds red.",
    "Only the pure of heart may claim the Grail of Eternity.",
    "The final room awaits the one who remembers their name.",
    "Three relics scattered, three guardians bound, one hero to free them all.",
    "When fire meets shadow and shadow meets stone, the dungeon shall speak.",
    "The betrayed king shall be avenged by the child of his enemy.",
    "Two seekers shall enter the final door but only one shall carry the name of victor.",
    "The curse breaks only when the last descendant of the dungeon's builder speaks the founding word.",
    "A dragon's tear shed willingly shall unbind the lich's soul from its phylactery.",
    "The dungeon has seven hearts. Six beat with malice. One with sorrow. Find the sorrowful heart.",
    "He who slays without hatred shall be granted the key that opens everything.",
    "The throne of the lost empire shall seat a new ruler before the age turns.",
    "Seek the room where time runs backward. There lies the answer you forgot to ask.",
    "One path leads to glory, one to ruin, and one to truth. Only the brave walk the third.",
    "The walls will bleed when the first seal cracks. Do not mistake destruction for defeat.",
    "You were here before. You will be here again. Remember differently this time.",
    "An army of the dead awaits a living general. Will you be worthy of the command?",
    "The dungeon feeds on fear. Starve it.",
  ],
  "magical_events": [
    "Arcane energies surge through Room {room_id} and heal all wounds!",
    "A portal of pure starlight opens, offering a shortcut to safety.",
    "The walls bloom with glowing flowers that grant temporary invisibility.",
    "Time freezes for a moment, letting you act twice.",
    "A chorus of angels descends and blesses your weapons.",
    "The dungeon itself speaks a single word of power.",
    "A spectral ally materializes to fight at your side.",
    "All traps in the room deactivate with a gentle chime.",
    "Your inventory items glow and gain +1 enchantment.",
    "A vision of the final boss is granted for one brief second.",
    "The floor opens to reveal a hidden cache of ancient gold!",
    "A rift in reality deposits a legendary weapon at your feet.",
    "Every enemy in the room is stunned by a divine shockwave.",
    "The room reshapes — a shortcut corridor appears in the north wall.",
    "A spirit dragon coils around you, granting fire immunity for one battle.",
    "The dungeon rewinds time by three seconds, undoing your last mistake.",
    "A phantom merchant appears offering enchanted goods at half price.",
    "All poison and disease afflictions are purged by cleansing white fire.",
    "The runes on the floor activate a legendary golem that fights for you.",
    "A stormcloud forms inside the room, striking your enemies with lightning.",
    "Your reflection steps out of a mirror and shares half its HP with you.",
    "An ancient blessing permanently increases your maximum HP by 5.",
    "The Dungeon Heart beats — every ally gains two levels simultaneously.",
    "A sealed door nearby shatters, revealing the dungeon's oldest secret.",
    "The Lich's influence wavers — all undead in this zone freeze for one minute.",
  ],
  "nli_fallback_messages": {
    "move": [
      "Your boots echo on ancient stone as you head {direction}.",
      "You press onward {direction}, deeper into the dark.",
      "The passage {direction} opens before you.",
      "You stride {direction} with purpose, torchlight leading the way.",
      "Step by step, you advance {direction} into the unknown.",
      "The corridor {direction} narrows as you push forward.",
      "You move {direction}, senses sharp for threats.",
    ],
    "look": [
      "Your eyes adjust to the gloom...",
      "You scan the chamber carefully.",
      "The torchlight reveals...",
      "You take in every detail of the room.",
      "Your gaze sweeps from wall to wall.",
      "You inspect the surroundings with practiced caution.",
      "The shadows recede slightly under your scrutiny.",
    ],
    "attack": [
      "Steel rings as you charge!",
      "You launch yourself at the creature!",
      "Battle is joined!",
      "Your weapon rises and falls with deadly intent.",
      "You strike with everything you have!",
      "The creature meets your fury head-on.",
      "You commit fully to the assault.",
    ],
    "search": [
      "You run your hands along the walls...",
      "Your eyes search every shadow.",
      "You dig through the rubble...",
      "You tap stones looking for hollow spaces.",
      "You check corners, crevices, and ceiling alike.",
      "Every inch of the room gets your attention.",
      "You probe the floor carefully with your boot.",
    ],
    "rest": [
      "You find a sheltered corner and close your eyes.",
      "The dungeon quiets as you rest.",
      "Sleep comes fitfully, but it comes.",
      "You lean against cool stone and breathe slowly.",
      "Even here, even now, you find a moment of stillness.",
      "You close your eyes, listening for danger, finding none.",
      "Brief rest restores you for what lies ahead.",
    ],
    "use": [
      "You employ the item carefully.",
      "The object hums with use.",
      "You activate it with steady hands.",
      "The item responds to your intention.",
      "Something shifts as you use it.",
    ],
    "talk": [
      "You address the figure cautiously.",
      "Words form between you and the presence.",
      "You speak, and the dungeon listens.",
      "The being regards you before responding.",
      "Dialogue opens — carefully.",
    ],
  },
  "model_unavailable": [
    "The oracle is silent... but your instincts guide you.",
    "The stars give no answer tonight. You act on gut.",
    "The mystic mists part enough to show you the way.",
    "The dungeon holds its breath — you must decide alone.",
    "No prophecy speaks now. Your choices are your own.",
    "The connection to the celestial archive is severed. Press on.",
  ],
  "compact_room_summary": "{type} room {room_id}. {monster_tag}{loot_tag}Exits: {exits}. HP {hp}/{maxHp}.",
  "monster_tag": "Monster: {monster}. ",
  "loot_tag": "Loot: {loot}. ",
  "monsters": [
    {"name": "Goblin", "zone": "entrance", "base_hp": 8, "base_attack": 2, "base_defense": 1, "damage_range": [2,5], "xp": 20, "gold_range": [5,10], "loot_table": [{"item": {"name": "Goblin Ear", "type": "misc", "value": 1}, "chance": 0.8}, {"item": {"name": "Rusty Dagger", "type": "weapon", "bonus": 1, "value": 5}, "chance": 0.2}]},
    {"name": "Skeleton", "zone": "entrance", "base_hp": 10, "base_attack": 3, "base_defense": 2, "damage_range": [2,6], "xp": 25, "gold_range": [3,8], "loot_table": [{"item": {"name": "Bone Fragment", "type": "misc", "value": 2}, "chance": 0.9}]},
    {"name": "Giant Spider", "zone": "entrance", "base_hp": 12, "base_attack": 4, "base_defense": 2, "damage_range": [3,7], "xp": 30, "gold_range": [4,10], "loot_table": [{"item": {"name": "Spider Silk", "type": "misc", "value": 5}, "chance": 0.7}]},
    {"name": "Plague Rat Swarm", "zone": "entrance", "base_hp": 9, "base_attack": 3, "base_defense": 1, "damage_range": [2,5], "xp": 22, "gold_range": [2,6], "loot_table": [{"item": {"name": "Diseased Fur", "type": "misc", "value": 1}, "chance": 0.6}]},
    {"name": "Kobold Scout", "zone": "entrance", "base_hp": 7, "base_attack": 2, "base_defense": 1, "damage_range": [1,4], "xp": 18, "gold_range": [3,7], "loot_table": [{"item": {"name": "Crude Map", "type": "misc", "value": 8}, "chance": 0.3}]},
    {"name": "Orc", "zone": "mid", "base_hp": 18, "base_attack": 5, "base_defense": 3, "damage_range": [4,9], "xp": 45, "gold_range": [10,20], "loot_table": [{"item": {"name": "Orc Axe", "type": "weapon", "bonus": 2, "value": 20}, "chance": 0.3}]},
    {"name": "Wraith", "zone": "mid", "base_hp": 16, "base_attack": 6, "base_defense": 4, "damage_range": [3,8], "xp": 50, "gold_range": [8,15], "loot_table": [{"item": {"name": "Ectoplasm", "type": "misc", "value": 10}, "chance": 0.6}]},
    {"name": "Basilisk", "zone": "mid", "base_hp": 22, "base_attack": 7, "base_defense": 5, "damage_range": [5,10], "xp": 60, "gold_range": [15,25], "loot_table": [{"item": {"name": "Basilisk Eye", "type": "quest", "value": 50}, "chance": 0.4}]},
    {"name": "Goblin King", "zone": "mid", "base_hp": 30, "base_attack": 8, "base_defense": 6, "damage_range": [6,12], "xp": 100, "gold_range": [50,100], "loot_table": [{"item": {"name": "Crown of the Goblin King", "type": "quest", "value": 200}, "chance": 1.0}]},
    {"name": "Troll", "zone": "mid", "base_hp": 28, "base_attack": 7, "base_defense": 4, "damage_range": [6,11], "xp": 80, "gold_range": [20,40], "loot_table": [{"item": {"name": "Troll Hide", "type": "misc", "value": 15}, "chance": 0.5}]},
    {"name": "Cursed Knight", "zone": "mid", "base_hp": 26, "base_attack": 8, "base_defense": 7, "damage_range": [5,11], "xp": 90, "gold_range": [25,50], "loot_table": [{"item": {"name": "Cursed Medallion", "type": "quest", "value": 75}, "chance": 0.45}]},
    {"name": "Vampire", "zone": "deep", "base_hp": 35, "base_attack": 9, "base_defense": 7, "damage_range": [7,14], "xp": 120, "gold_range": [30,60], "loot_table": [{"item": {"name": "Vampire Fang", "type": "misc", "value": 25}, "chance": 0.7}]},
    {"name": "Frost Giant", "zone": "deep", "base_hp": 45, "base_attack": 10, "base_defense": 8, "damage_range": [8,16], "xp": 150, "gold_range": [40,80], "loot_table": [{"item": {"name": "Giant's Toe", "type": "misc", "value": 30}, "chance": 0.5}]},
    {"name": "Dragon Wyrmling", "zone": "deep", "base_hp": 40, "base_attack": 11, "base_defense": 9, "damage_range": [9,18], "xp": 180, "gold_range": [60,120], "loot_table": [{"item": {"name": "Dragon Scale", "type": "quest", "value": 100}, "chance": 0.8}]},
    {"name": "Demon Knight", "zone": "deep", "base_hp": 50, "base_attack": 12, "base_defense": 10, "damage_range": [10,20], "xp": 200, "gold_range": [80,150], "loot_table": [{"item": {"name": "Demon Heart", "type": "misc", "value": 50}, "chance": 0.6}]},
    {"name": "Shadow Dragon", "zone": "deep", "base_hp": 60, "base_attack": 13, "base_defense": 11, "damage_range": [11,22], "xp": 250, "gold_range": [100,200], "loot_table": [{"item": {"name": "Shadow Dragon Scale", "type": "quest", "value": 150}, "chance": 0.9}]},
    {"name": "Blood Witch", "zone": "deep", "base_hp": 38, "base_attack": 12, "base_defense": 8, "damage_range": [10,18], "xp": 220, "gold_range": [70,130], "loot_table": [{"item": {"name": "Blood Grimoire", "type": "quest", "value": 180}, "chance": 0.5}]},
    {"name": "Void Revenant", "zone": "deep", "base_hp": 55, "base_attack": 14, "base_defense": 10, "damage_range": [12,20], "xp": 230, "gold_range": [90,160], "loot_table": [{"item": {"name": "Void Shard", "type": "misc", "value": 80}, "chance": 0.6}]},
    {"name": "Ancient Lich", "zone": "boss", "base_hp": 100, "base_attack": 15, "base_defense": 12, "damage_range": [12,24], "xp": 500, "gold_range": [200,500], "loot_table": [{"item": {"name": "Lich's Phylactery", "type": "quest", "value": 1000}, "chance": 1.0}]},
    {"name": "Dungeon Heart Guardian", "zone": "boss", "base_hp": 120, "base_attack": 16, "base_defense": 14, "damage_range": [14,28], "xp": 700, "gold_range": [300,600], "loot_table": [{"item": {"name": "Heart Shard", "type": "quest", "value": 800}, "chance": 1.0}]},
    {"name": "Betrayer King", "zone": "boss", "base_hp": 90, "base_attack": 14, "base_defense": 13, "damage_range": [13,26], "xp": 600, "gold_range": [250,550], "loot_table": [{"item": {"name": "Crown of Betrayal", "type": "quest", "value": 900}, "chance": 1.0}]},
  ],
  "items": [
    {"name": "Rusty Dagger", "type": "weapon", "bonus": 1, "value": 5, "consumable": False},
    {"name": "Iron Sword", "type": "weapon", "bonus": 2, "value": 20, "consumable": False},
    {"name": "Elven Longsword", "type": "weapon", "bonus": 3, "value": 50, "consumable": False},
    {"name": "Shadowblade", "type": "weapon", "bonus": 4, "value": 80, "consumable": False},
    {"name": "Runic Battleaxe", "type": "weapon", "bonus": 4, "value": 75, "consumable": False},
    {"name": "Celestial Longbow", "type": "weapon", "bonus": 5, "value": 120, "consumable": False},
    {"name": "Leather Armor", "type": "armor", "bonus": 1, "value": 15, "consumable": False},
    {"name": "Chainmail", "type": "armor", "bonus": 2, "value": 30, "consumable": False},
    {"name": "Plate Armor", "type": "armor", "bonus": 3, "value": 60, "consumable": False},
    {"name": "Shadowweave Armor", "type": "armor", "bonus": 4, "value": 90, "consumable": False},
    {"name": "Rune-Scribed Tower Shield", "type": "armor", "bonus": 3, "value": 70, "consumable": False},
    {"name": "Bracer of Arcane Deflection", "type": "armor", "bonus": 2, "value": 45, "consumable": False},
    {"name": "Health Potion", "type": "consumable", "effect": "heal", "value": 15, "consumable": True},
    {"name": "Greater Health Potion", "type": "consumable", "effect": "heal_large", "value": 40, "consumable": True},
    {"name": "Antidote", "type": "consumable", "effect": "cure", "value": 10, "consumable": True},
    {"name": "Blessed Scroll", "type": "consumable", "effect": "buff", "value": 2, "consumable": True},
    {"name": "Scroll of Fireball", "type": "consumable", "effect": "damage_fire", "value": 35, "consumable": True},
    {"name": "Scroll of Teleportation", "type": "consumable", "effect": "teleport", "value": 50, "consumable": True},
    {"name": "Elixir of Strength", "type": "consumable", "effect": "str_buff", "value": 30, "consumable": True},
    {"name": "Vial of Dragon's Blood", "type": "consumable", "effect": "fire_immunity", "value": 60, "consumable": True},
    {"name": "Gold Coins", "type": "misc", "value": 1, "consumable": False},
    {"name": "Goblin Ear", "type": "misc", "value": 1, "consumable": False},
    {"name": "Spider Silk", "type": "misc", "value": 5, "consumable": False},
    {"name": "Orc Axe", "type": "weapon", "bonus": 2, "value": 20, "consumable": False},
    {"name": "Ectoplasm", "type": "misc", "value": 10, "consumable": False},
    {"name": "Basilisk Eye", "type": "quest", "value": 50, "consumable": False},
    {"name": "Crown of the Goblin King", "type": "quest", "value": 200, "consumable": False},
    {"name": "Vampire Fang", "type": "misc", "value": 25, "consumable": False},
    {"name": "Giant's Toe", "type": "misc", "value": 30, "consumable": False},
    {"name": "Dragon Scale", "type": "quest", "value": 100, "consumable": False},
    {"name": "Demon Heart", "type": "misc", "value": 50, "consumable": False},
    {"name": "Lich's Phylactery", "type": "quest", "value": 1000, "consumable": False},
    {"name": "Void Shard", "type": "misc", "value": 80, "consumable": False},
    {"name": "Blood Grimoire", "type": "quest", "value": 180, "consumable": False},
    {"name": "Shadow Dragon Scale", "type": "quest", "value": 150, "consumable": False},
    {"name": "Heart Shard", "type": "quest", "value": 800, "consumable": False},
    {"name": "Crown of Betrayal", "type": "quest", "value": 900, "consumable": False},
    {"name": "Dwarven Master Key", "type": "misc", "value": 200, "consumable": False},
    {"name": "Compass of True North", "type": "misc", "value": 75, "consumable": False},
    {"name": "Cursed Medallion", "type": "quest", "value": 75, "consumable": False},
    {"name": "Crude Map", "type": "misc", "value": 8, "consumable": False},
    {"name": "Ring of Invisibility", "type": "misc", "value": 150, "consumable": False},
    {"name": "Amulet of Health", "type": "misc", "value": 100, "consumable": False},
    {"name": "Helm of True Sight", "type": "armor", "bonus": 1, "value": 80, "consumable": False},
  ],
  "ground_loot": {
    "entrance": {
      "items": [
        {"name": "Rusty Dagger", "type": "weapon", "bonus": 1, "value": 5},
        {"name": "Health Potion", "type": "consumable", "effect": "heal", "value": 15},
        {"name": "Gold Coins", "type": "misc", "value": 1},
        {"name": "Leather Armor", "type": "armor", "bonus": 1, "value": 15},
        {"name": "Crude Map", "type": "misc", "value": 8},
        {"name": "Antidote", "type": "consumable", "effect": "cure", "value": 10},
      ],
      "chances": [0.25, 0.2, 0.3, 0.1, 0.1, 0.05]
    },
    "mid": {
      "items": [
        {"name": "Iron Sword", "type": "weapon", "bonus": 2, "value": 20},
        {"name": "Chainmail", "type": "armor", "bonus": 2, "value": 30},
        {"name": "Health Potion", "type": "consumable", "effect": "heal", "value": 15},
        {"name": "Antidote", "type": "consumable", "effect": "cure", "value": 10},
        {"name": "Gold Coins", "type": "misc", "value": 5},
        {"name": "Blessed Scroll", "type": "consumable", "effect": "buff", "value": 2},
        {"name": "Compass of True North", "type": "misc", "value": 75},
      ],
      "chances": [0.18, 0.12, 0.22, 0.1, 0.25, 0.08, 0.05]
    },
    "deep": {
      "items": [
        {"name": "Elven Longsword", "type": "weapon", "bonus": 3, "value": 50},
        {"name": "Plate Armor", "type": "armor", "bonus": 3, "value": 60},
        {"name": "Blessed Scroll", "type": "consumable", "effect": "buff", "value": 2},
        {"name": "Health Potion", "type": "consumable", "effect": "heal", "value": 15},
        {"name": "Gold Coins", "type": "misc", "value": 10},
        {"name": "Greater Health Potion", "type": "consumable", "effect": "heal_large", "value": 40},
        {"name": "Shadowblade", "type": "weapon", "bonus": 4, "value": 80},
        {"name": "Scroll of Fireball", "type": "consumable", "effect": "damage_fire", "value": 35},
      ],
      "chances": [0.12, 0.1, 0.1, 0.2, 0.3, 0.08, 0.05, 0.05]
    },
    "boss": {
      "items": [
        {"name": "Lich's Phylactery", "type": "quest", "value": 1000},
        {"name": "Heart Shard", "type": "quest", "value": 800},
        {"name": "Crown of Betrayal", "type": "quest", "value": 900},
        {"name": "Celestial Longbow", "type": "weapon", "bonus": 5, "value": 120},
      ],
      "chances": [0.4, 0.2, 0.2, 0.2]
    }
  },
  "traps": [
    {"name": "Pit", "zone": "entrance", "effect": "damage", "save_dc": 10, "damage": 5},
    {"name": "Poison Dart", "zone": "entrance", "effect": "poison", "save_dc": 12, "damage": 3},
    {"name": "Tripwire Alarm", "zone": "entrance", "effect": "alert", "save_dc": 11, "damage": 0},
    {"name": "Swinging Blade", "zone": "mid", "effect": "damage", "save_dc": 14, "damage": 8},
    {"name": "Fire Trap", "zone": "mid", "effect": "burn", "save_dc": 13, "damage": 6},
    {"name": "Confusion Glyph", "zone": "mid", "effect": "confusion", "save_dc": 14, "damage": 0},
    {"name": "Net Trap", "zone": "mid", "effect": "paralyze", "save_dc": 13, "damage": 2},
    {"name": "Lightning Rune", "zone": "deep", "effect": "damage", "save_dc": 16, "damage": 12},
    {"name": "Curse Glyph", "zone": "deep", "effect": "curse", "save_dc": 15, "damage": 0},
    {"name": "Gravity Inversion", "zone": "deep", "effect": "stun", "save_dc": 17, "damage": 10},
    {"name": "Soul Drain Circle", "zone": "deep", "effect": "weaken", "save_dc": 16, "damage": 8},
    {"name": "Teleport Trap", "zone": "deep", "effect": "teleport", "save_dc": 18, "damage": 0},
  ],
  "npcs": [
    {"name": "Old Sage", "zone": "entrance", "dialogue": "The path ahead is dangerous. Seek the Goblin King's crown.", "quest_giver": True},
    {"name": "Mysterious Stranger", "zone": "entrance", "dialogue": "I sense a great evil in the deep.", "quest_giver": False},
    {"name": "Goblin Prisoner", "zone": "mid", "dialogue": "The King keeps the key in his throne room.", "quest_giver": True},
    {"name": "Ghost of a Knight", "zone": "mid", "dialogue": "Avenge my death, slay the Vampire Lord.", "quest_giver": True},
    {"name": "Dragon Priest", "zone": "deep", "dialogue": "Bring me three Dragon Scales and I will forge a weapon.", "quest_giver": True},
    {"name": "Lich's Echo", "zone": "boss", "dialogue": "You cannot defeat me without the Phylactery.", "quest_giver": False},
    {"name": "Wandering Bard", "zone": "entrance", "dialogue": "I've composed a song about the dungeon's seven seals. Shall I sing it?", "quest_giver": False},
    {"name": "Trapped Merchant", "zone": "mid", "dialogue": "I was robbed by goblins! Retrieve my stolen wares and I'll give you a discount.", "quest_giver": True},
    {"name": "Dungeon Architect", "zone": "mid", "dialogue": "I built these halls. I know where every secret room is. My price is freedom.", "quest_giver": True},
    {"name": "Penitent Cultist", "zone": "deep", "dialogue": "I helped the Lich take power. Let me help you destroy his phylactery.", "quest_giver": True},
    {"name": "Soul Collector", "zone": "deep", "dialogue": "I hold the souls of four heroes. Free them and their power is yours.", "quest_giver": True},
    {"name": "Bound Spirit", "zone": "boss", "dialogue": "I am the dungeon's original master. The Lich imprisoned me here. You are my only hope.", "quest_giver": True},
  ],
  "quest_hints": {
    "entrance": [
      "You see a crude map marking the Goblin King's lair.",
      "A dying adventurer whispers: 'The crown... in the mid zone...'",
      "Scratched into the stone: 'The bard knows the way through the first three rooms.'",
      "A child's drawing on the wall shows a stick figure king wearing a large crown.",
      "You find a torn journal page: 'Day 7 — the goblins patrol the eastern corridor.'",
      "A ghost briefly materializes and points south, then disappears.",
    ],
    "mid": [
      "A mural depicts a goblin wearing a crown.",
      "Scratches on the wall read: 'The King's chamber is guarded.'",
      "The ghost of a knight follows you, pointing toward the sealed vault.",
      "You find a prison log: 'Cell 12 — the architect knows the vault combination.'",
      "A coded message on the floor spells out: 'The crown is not the only key.'",
      "You discover a half-burned map showing a hidden passage to the deep zone.",
    ],
    "deep": [
      "A glowing inscription: 'Three scales shall light the way to the Lich.'",
      "You find a journal detailing the Lich's phylactery location.",
      "A dragon skull's eye socket glows — insert a Dragon Scale to reveal a path.",
      "The cultist's robe has a symbol matching the seal on the final door.",
      "An inscription: 'The phylactery was split into three. Find the fragments.'",
      "You discover notes in the Dragon Priest's hand: 'The Blood Grimoire holds the banishing rite.'",
    ]
  },
  "quests": [
    {
      "id": "q_goblin_king",
      "name": "Slay the Goblin King",
      "description": "Find and defeat the Goblin King in the Mid zone.",
      "objectives": [{"type": "kill", "target": "Goblin King", "current": 0, "required": 1}],
      "reward": {"gold": 200, "xp": 150, "item": {"name": "Crown of the Goblin King", "type": "quest", "value": 200}}
    },
    {
      "id": "q_dragon_scales",
      "name": "Dragon Scale Collector",
      "description": "Collect 3 Dragon Scales from the Deep zone.",
      "objectives": [{"type": "collect", "target": "Dragon Scale", "current": 0, "required": 3}],
      "reward": {"gold": 500, "xp": 300, "item": {"name": "Dragon Slayer Sword", "type": "weapon", "bonus": 5, "value": 400}}
    },
    {
      "id": "q_lich",
      "name": "The Lich's End",
      "description": "Defeat the Ancient Lich in Room 49.",
      "objectives": [{"type": "kill", "target": "Ancient Lich", "current": 0, "required": 1}],
      "reward": {"gold": 1000, "xp": 1000, "item": {"name": "Lich's Phylactery", "type": "quest", "value": 1000}}
    },
    {
      "id": "q_minion",
      "name": "Slay a Minion",
      "description": "Defeat any minion to prove your strength.",
      "objectives": [{"type": "kill", "target": "Minion", "current": 0, "required": 1}],
      "reward": {"gold": 100, "xp": 80, "item": {"name": "Minion's Tooth", "type": "misc", "value": 20}}
    },
    {
      "id": "q_explore_deep",
      "name": "Explore the Deep",
      "description": "Reach the Deep zone (room >= 28).",
      "objectives": [{"type": "explore", "target": "deep", "current": 0, "required": 1}],
      "reward": {"gold": 200, "xp": 150}
    },
    {
      "id": "q_collect_essence",
      "name": "Collect Minion Essence",
      "description": "Gather 3 Minion Essences from fallen minions.",
      "objectives": [{"type": "collect", "target": "Minion Essence", "current": 0, "required": 3}],
      "reward": {"gold": 150, "xp": 120, "item": {"name": "Essence Potion", "type": "consumable", "effect": "heal", "value": 30}}
    },
    {
      "id": "q_seven_seals",
      "name": "The Seven Seals",
      "description": "Find and break all seven ancient seals hidden throughout the dungeon. Each broken seal weakens the Lich and reveals a dungeon secret.",
      "objectives": [{"type": "collect", "target": "Broken Seal", "current": 0, "required": 7}],
      "reward": {"gold": 800, "xp": 600, "item": {"name": "Sealbreaker's Gauntlet", "type": "weapon", "bonus": 6, "value": 600}}
    },
    {
      "id": "q_architect_freedom",
      "name": "Free the Architect",
      "description": "The dungeon's original Architect is imprisoned in the Mid zone. Defeat his guards and escort him to the entrance.",
      "objectives": [
        {"type": "kill", "target": "Dungeon Guard", "current": 0, "required": 3},
        {"type": "escort", "target": "Dungeon Architect", "current": 0, "required": 1}
      ],
      "reward": {"gold": 400, "xp": 350, "item": {"name": "Dwarven Master Key", "type": "misc", "value": 200}}
    },
    {
      "id": "q_soul_liberation",
      "name": "Liberate the Fallen Heroes",
      "description": "Four heroes were trapped as soul-crystals by the Lich. Find their crystals and bring them to the Sunken Cathedral's altar to free them.",
      "objectives": [{"type": "collect", "target": "Hero Soul Crystal", "current": 0, "required": 4}],
      "reward": {"gold": 600, "xp": 500, "item": {"name": "Banner of the Fallen", "type": "misc", "value": 500}}
    },
    {
      "id": "q_blood_grimoire",
      "name": "The Blood Grimoire",
      "description": "The Blood Witch guards an ancient grimoire that contains the banishing rite for the Lich. Defeat her and retrieve the tome.",
      "objectives": [
        {"type": "kill", "target": "Blood Witch", "current": 0, "required": 1},
        {"type": "collect", "target": "Blood Grimoire", "current": 0, "required": 1}
      ],
      "reward": {"gold": 500, "xp": 400, "item": {"name": "Banishing Scroll", "type": "consumable", "effect": "banish", "value": 300}}
    },
    {
      "id": "q_betrayer_king",
      "name": "The Betrayed Throne",
      "description": "The Betrayer King sold his kingdom to the Lich for immortality. Defeat him in the Hall of Fallen Kings and reclaim the stolen crown.",
      "objectives": [
        {"type": "kill", "target": "Betrayer King", "current": 0, "required": 1},
        {"type": "collect", "target": "Crown of Betrayal", "current": 0, "required": 1}
      ],
      "reward": {"gold": 750, "xp": 650, "item": {"name": "Redeemer's Crown", "type": "armor", "bonus": 4, "value": 700}}
    },
    {
      "id": "q_dungeon_heart",
      "name": "Shatter the Dungeon Heart",
      "description": "At the deepest point of the dungeon pulses the Dungeon Heart — the source of all undead power. Defeat its guardian and shatter it to free the dungeon forever.",
      "objectives": [
        {"type": "kill", "target": "Dungeon Heart Guardian", "current": 0, "required": 1},
        {"type": "destroy", "target": "Dungeon Heart", "current": 0, "required": 1}
      ],
      "reward": {"gold": 2000, "xp": 2000, "item": {"name": "Heartbreaker Warhammer", "type": "weapon", "bonus": 8, "value": 1500}}
    },
    {
      "id": "q_three_artifacts",
      "name": "Reunite the Three Relics",
      "description": "Long ago three relics — the Sunblade, the Moonshield, and the Star Compass — were scattered to prevent the Lich's rise. Reunite them at the ancient altar.",
      "objectives": [
        {"type": "collect", "target": "Sunblade Fragment", "current": 0, "required": 1},
        {"type": "collect", "target": "Moonshield Fragment", "current": 0, "required": 1},
        {"type": "collect", "target": "Star Compass Fragment", "current": 0, "required": 1}
      ],
      "reward": {"gold": 1200, "xp": 900, "item": {"name": "Reforged Sunblade", "type": "weapon", "bonus": 7, "value": 1200}}
    },
    {
      "id": "q_map_cartographer",
      "name": "The Lost Cartographer",
      "description": "A renowned mapmaker vanished in the dungeon. Find her seven map fragments scattered across all zones and piece together the complete dungeon layout.",
      "objectives": [{"type": "collect", "target": "Map Fragment", "current": 0, "required": 7}],
      "reward": {"gold": 350, "xp": 280, "item": {"name": "Complete Dungeon Map", "type": "misc", "value": 400}}
    },
    {
      "id": "q_cursed_knight_redemption",
      "name": "Redeem the Cursed Knight",
      "description": "Sir Aldric was cursed by the Lich and forced to serve. Find the Curse-Breaking Altar, collect a purification crystal, and lift the curse.",
      "objectives": [
        {"type": "collect", "target": "Purification Crystal", "current": 0, "required": 1},
        {"type": "use", "target": "Curse-Breaking Altar", "current": 0, "required": 1}
      ],
      "reward": {"gold": 300, "xp": 250, "item": {"name": "Aldric's Holy Lance", "type": "weapon", "bonus": 5, "value": 450}}
    },
  ],
  "lore_fragments": [
    "The dungeon was once a great dwarven city, lost to a curse.",
    "The Lich was once a powerful wizard who sought immortality.",
    "Three ancient artifacts were scattered to prevent the Lich's rise.",
    "The Goblin King forged his crown from the melted gold of fallen heroes.",
    "Dragons once roamed these halls, now only their scales remain.",
    "The original dungeon architect was imprisoned for refusing to serve the Lich.",
    "Seven seals bind an ancient evil beneath the deepest floor.",
    "The Dungeon Heart is a living organ that pumps dark energy through the stone.",
    "A great battle was fought in the Colosseum of Ancients — the winner was cursed with immortality.",
    "The Betrayer King traded his kingdom for undeath; the Lich gave him eternity as a slave.",
    "Four heroes tried to stop the Lich three centuries ago. Three were slain. One was imprisoned as a soul-crystal.",
    "The Blood Grimoire was written in the Lich's own hand before he lost his mortality.",
    "The dungeon shifts its layout every century, but the Dungeon Heart never moves.",
    "Goblin shamans paint themselves red to honor their fallen king.",
    "The Void Revenant was once a paladin who stared into the abyss too long.",
    "Shadow Dragons are what happens when a dragon's corpse absorbs enough dark energy to reanimate.",
    "The Blood Witch was the Lich's apprentice before she was betrayed and imprisoned in the Deep zone.",
    "Three keys exist in the dungeon; together they open the Chamber of First Truths.",
    "The founding rune of the dwarven city is carved somewhere in the deepest hall.",
    "An ancient prophecy says only a mortal who has broken all seven seals can enter the Lich's inner sanctum.",
    "The Soul Collector harvests the essence of dead adventurers. He is not evil — just hungry.",
    "The dungeon has a back door that no map shows. The architect knows its location.",
    "Time moves differently in the Time-Warped Room — every minute inside is five outside.",
    "The Unicorn was not always corrupted. It was the dungeon's guardian before the Lich arrived.",
    "Dwarven script on the Forge Hall walls reads: 'We built to last. We did not build well enough.'",
    "The Mermaid Lagoon exists because the dungeon was built over a sea cave thousands of years ago.",
    "Phoenix feathers grow back; only by retrieving a feather freely given can a hero earn fire resistance.",
    "The Starlit Observatory once guided ships on the surface. Now it guides lost souls through the dark.",
    "The seven seal locations correspond to the seven sins of the dungeon's original architect.",
    "When the Dungeon Heart shatters, every undead creature in the dungeon will fall simultaneously.",
  ],
  "quest_templates": [
    {
      "id": "q_minion_hunter",
      "name": "Minion Hunter",
      "description": "Defeat any minion to prove your strength.",
      "objectives": [{"type": "kill", "target": "Minion", "current": 0, "required": 1}],
      "reward": {"gold": 100, "xp": 80, "item": {"name": "Minion's Tooth", "type": "misc", "value": 20}}
    },
    {
      "id": "q_explore_deep_template",
      "name": "Explore the Deep",
      "description": "Reach the Deep zone (room >= 28).",
      "objectives": [{"type": "explore", "target": "deep", "current": 0, "required": 1}],
      "reward": {"gold": 200, "xp": 150}
    },
    {
      "id": "q_collect_essence_template",
      "name": "Collect Minion Essence",
      "description": "Gather 3 Minion Essences from fallen minions.",
      "objectives": [{"type": "collect", "target": "Minion Essence", "current": 0, "required": 3}],
      "reward": {"gold": 150, "xp": 120, "item": {"name": "Essence Potion", "type": "consumable", "effect": "heal", "value": 30}}
    },
    {
      "id": "q_veteran_template",
      "name": "Clear the Zone",
      "description": "Defeat five enemies in a single zone without leaving.",
      "objectives": [{"type": "kill_in_zone", "target": "any", "current": 0, "required": 5}],
      "reward": {"gold": 300, "xp": 200}
    },
    {
      "id": "q_survivor_template",
      "name": "Survive the Gauntlet",
      "description": "Complete three consecutive battles without using a health potion.",
      "objectives": [{"type": "survive_battles", "target": "no_potion", "current": 0, "required": 3}],
      "reward": {"gold": 250, "xp": 180, "item": {"name": "Endurance Charm", "type": "misc", "value": 60}}
    },
  ],
  "story_arcs": [
    {
      "id": "arc_lich_war",
      "name": "The Lich War",
      "description": "The overarching story of the dungeon. The Ancient Lich seeks to extend his dark rule beyond the dungeon walls. A series of quests leads the player to discover the Lich's origin, find his phylactery, shatter the Dungeon Heart, and end his reign.",
      "quest_chain": ["q_goblin_king", "q_dragon_scales", "q_blood_grimoire", "q_lich"],
      "lore_unlocks": [1, 5, 8, 12, 20, 28]
    },
    {
      "id": "arc_ancient_betrayal",
      "name": "The Ancient Betrayal",
      "description": "Uncover the dark history of the Betrayer King who sold his people to the Lich. Restore his stolen crown to the rightful bloodline and free his cursed subjects.",
      "quest_chain": ["q_cursed_knight_redemption", "q_architect_freedom", "q_betrayer_king"],
      "lore_unlocks": [9, 10, 14, 24]
    },
    {
      "id": "arc_relic_restoration",
      "name": "Restoration of the Relics",
      "description": "The three ancient relics that once kept the dungeon safe were scattered across its zones. Reunite them to unlock the Chamber of First Truths and learn the dungeon's founding secret.",
      "quest_chain": ["q_three_artifacts", "q_seven_seals", "q_dungeon_heart"],
      "lore_unlocks": [2, 6, 17, 19, 29]
    },
    {
      "id": "arc_hero_legacy",
      "name": "Legacy of the Fallen Heroes",
      "description": "Four brave heroes fell fighting the Lich. Their souls were imprisoned in crystals. Freeing them unlocks their combined power and reveals the final weakness of the Ancient Lich.",
      "quest_chain": ["q_soul_liberation", "q_map_cartographer", "q_dungeon_heart"],
      "lore_unlocks": [11, 15, 18, 22, 30]
    },
  ],
  "boss_intros": [
    {
      "boss": "Ancient Lich",
      "intro": "The doors to the inner sanctum grind open. On a throne of skulls sits the Ancient Lich, his hollow eyes burning with green fire. 'Another mortal. How... predictable.' His staff rises. Dark magic crackles. This is what you came for."
    },
    {
      "boss": "Goblin King",
      "intro": "The Goblin King lounges on his pile of stolen gold, crown askew. He spots you and his grin turns feral. 'Fresh meat! GUARDS!' Twenty goblins flood the room. Then he rises — bigger than any goblin should be — and the guards scatter in fear of what their king becomes when angry."
    },
    {
      "boss": "Betrayer King",
      "intro": "In the Hall of Fallen Kings, one throne is not empty. The Betrayer King turns his rotting crowned head toward you. 'You dare enter my hall?' His voice is dust and regret. 'I gave everything for immortality. I am owed everything in return.' His rusted blade scrapes the stone as he rises."
    },
    {
      "boss": "Dungeon Heart Guardian",
      "intro": "At the bottom of the deepest stair, a colossal shape unfurls. The Dungeon Heart Guardian — stone and shadow and stolen life — has protected this pulsing crimson crystal since before anyone alive can remember. It has no name. It has no mercy. It only has purpose."
    },
    {
      "boss": "Blood Witch",
      "intro": "She does not look up as you enter. Her fingers trace sigils in the air, each one dripping red. 'The Lich sent me here as punishment,' she says quietly. 'Would you like to help me take my revenge?' Then she looks up, and her eyes are wrong — too many pupils, too much red. 'Too late to answer.'"
    },
  ],
  "cinematic_events": [
    {
      "trigger": "first_monster_kill",
      "text": "As the creature falls, something shifts in the dungeon. Torches flare. The walls shiver. You get the feeling the dungeon noticed what you did — and that it is not pleased."
    },
    {
      "trigger": "first_loot_found",
      "text": "You hold the item up in the torchlight. Somewhere deep below, you hear a sound like slow applause. The dungeon acknowledges your find. Whether that is a good thing remains to be seen."
    },
    {
      "trigger": "reach_mid_zone",
      "text": "The air changes as you cross into the Mid zone. Heavier. Older. The entrance feels very far away. For the first time, you understand that the dungeon did not end — it only deepened."
    },
    {
      "trigger": "reach_deep_zone",
      "text": "A sound you cannot place echoes from every direction at once. Your torch dims to a sliver and holds there. Something ancient became aware of your presence. You are not the hunter here. You are the intruder."
    },
    {
      "trigger": "phylactery_found",
      "text": "When your hand closes around the Phylactery, every undead creature in the dungeon freezes for three full seconds. Then, from far above and far below, you hear the Lich's voice: 'Give. It. Back.' The dungeon shudders."
    },
    {
      "trigger": "dungeon_heart_shatter",
      "text": "The crack of the Dungeon Heart echoes for a full minute. Green light floods every corridor. Every undead form in the dungeon collapses simultaneously. The dungeon exhales — centuries of held breath. Somewhere above, the sun is shining. You think you can feel it."
    },
  ],
}

# ======================================================================
# 2. EXPANSION FUNCTIONS
# ======================================================================
def expand_list(base_list, target_min=400):
    """Multiply a list to at least target_min items by inserting variations."""
    if len(base_list) >= target_min:
        return base_list[:]
    expanded = base_list[:]
    synonyms = {
        "dark": ["gloomy", "shadowy", "murky", "tenebrous", "ebony", "obsidian", "sable"],
        "cold": ["chilly", "icy", "frigid", "frosty", "arctic", "glacial", "wintry"],
        "stone": ["rock", "granite", "marble", "basalt", "slate", "limestone", "obsidian"],
        "ancient": ["old", "forgotten", "eldritch", "primordial", "antediluvian", "archaic", "hoary"],
        "room": ["chamber", "hall", "cavern", "cell", "vault", "sanctum", "grotto"],
        "hear": ["perceive", "detect", "notice", "sense", "discern", "catch", "overhear"],
        "see": ["spot", "glimpse", "observe", "behold", "espy", "discern", "witness"],
        "small": ["tiny", "compact", "cramped", "modest", "diminutive", "petite"],
        "large": ["huge", "massive", "enormous", "colossal", "gigantic", "immense"],
        "door": ["portal", "gate", "entrance", "opening", "egress", "threshold"],
        "walk": ["stroll", "pace", "stride", "traverse", "roam", "tread"],
        "monster": ["creature", "beast", "fiend", "abomination", "menace", "horror"],
        "treasure": ["hoard", "booty", "riches", "wealth", "spoils", "plunder"],
        "magic": ["arcane", "eldritch", "thaumaturgic", "sorcerous", "mystical", "occult"],
        "sword": ["blade", "longsword", "claymore", "rapier", "scimitar", "sabre"],
        "armor": ["armour", "plate", "mail", "cuirass", "carapace", "protection"],
        "potion": ["elixir", "philter", "draught", "tonic", "brew", "decoction"],
        "hero": ["champion", "warrior", "adventurer", "fighter", "brave", "crusader"],
        "dungeon": ["labyrinth", "crypt", "catacomb", "vault", "depths", "underhold"],
        "light": ["glow", "illumination", "gleam", "radiance", "shimmer", "glimmer"],
    }
    while len(expanded) < target_min:
        for s in base_list:
            if len(expanded) >= target_min:
                break
            words = s.split()
            new_words = []
            for w in words:
                if random.random() < 0.2:
                    if w.startswith('{') and w.endswith('}'):
                        new_words.append(w)
                        continue
                    for key, syns in synonyms.items():
                        if key in w.lower():
                            w = random.choice(syns)
                            break
                new_words.append(w)
            new_s = " ".join(new_words)
            if '{room_id}' in s and '{room_id}' not in new_s:
                continue
            if new_s not in expanded and new_s not in base_list:
                expanded.append(new_s)
    return expanded[:target_min]


def expand_monsters(base_list, target=100):
    """Generate more monsters by tweaking names and stats."""
    if len(base_list) >= target:
        return base_list[:]
    monsters = base_list[:]
    names = ["Goblin", "Orc", "Skeleton", "Zombie", "Ghost", "Vampire", "Werewolf",
             "Demon", "Elemental", "Golem", "Dragon", "Giant", "Spider", "Snake",
             "Rat", "Bat", "Cultist", "Necromancer", "Warlock", "Berserker", "Troll",
             "Ogre", "Harpy", "Gargoyle", "Manticore", "Chimera", "Hydra", "Wyvern",
             "Beholder", "Mind Flayer", "Lich", "Dracolich", "Phoenix", "Griffin",
             "Sphinx", "Centaur", "Minotaur", "Kobold", "Gnoll", "Bugbear", "Hobgoblin",
             "Revenant", "Wraith", "Specter", "Banshee", "Ghoul", "Shade", "Phantom",
             "Djinn", "Efrit", "Marid", "Dao", "Salamander", "Cockatrice", "Basilisk"]
    prefixes = ["Shadow", "Fire", "Ice", "Venom", "Ancient", "Elder", "Cursed",
                "Blessed", "Raging", "Savage", "Vicious", "Plague", "Stone", "Iron",
                "Steel", "Crystal", "Chaos", "Void", "Soul", "Night", "Doom", "Frost",
                "Abyssal", "Ethereal", "Blood", "Storm", "Arcane", "Runic", "Bone"]
    suffixes = ["King", "Queen", "Lord", "Priest", "Shaman", "Warrior", "Mage",
                "Hunter", "Stalker", "Guardian", "Avenger", "Tyrant", "Berserker",
                "Warlord", "Champion", "Cultist", "Fanatic", "Prophet", "Oracle",
                "Assassin", "Ravager", "Desecrator", "Colossus", "Dreadnought"]
    zones = ["entrance", "mid", "deep", "boss"]
    while len(monsters) < target:
        base = random.choice(base_list)
        name = random.choice(names)
        if random.random() < 0.5:
            name = random.choice(prefixes) + " " + name
        if random.random() < 0.3:
            name = name + " " + random.choice(suffixes)
        new_monster = copy.deepcopy(base)
        new_monster["name"] = name
        new_monster["zone"] = random.choice(zones)
        new_monster["base_hp"] = int(base["base_hp"] * random.uniform(0.8, 1.5))
        new_monster["base_attack"] = int(base["base_attack"] * random.uniform(0.8, 1.5))
        new_monster["base_defense"] = int(base["base_defense"] * random.uniform(0.8, 1.5))
        new_monster["xp"] = int(base["xp"] * random.uniform(0.8, 1.5))
        if random.random() < 0.2:
            new_monster["loot_table"].append({
                "item": {"name": f"{name} Essence", "type": "misc", "value": random.randint(2, 10)},
                "chance": 0.5
            })
        if new_monster not in monsters:
            monsters.append(new_monster)
    return monsters[:target]


def expand_items(base_list, target=200):
    """Generate more items."""
    if len(base_list) >= target:
        return base_list[:]
    items = base_list[:]
    types = ["weapon", "armor", "consumable", "misc", "quest"]
    prefixes = ["Iron", "Steel", "Bronze", "Silver", "Golden", "Crystal", "Wooden",
                "Bone", "Dragon", "Demon", "Angelic", "Shadow", "Flaming", "Frozen",
                "Venomous", "Blessed", "Cursed", "Ethereal", "Obsidian", "Mithril",
                "Adamant", "Elven", "Dwarven", "Orcish", "Goblin", "Vampiric",
                "Storm", "Void", "Runic", "Ancient", "Blood", "Soul", "Star"]
    suffixes = ["of Might", "of Swiftness", "of Wisdom", "of the Ancients", "of the Phoenix",
                "of the Void", "of Protection", "of Healing", "of Thorns", "of Accuracy",
                "of Vitality", "of the Eagle", "of the Wolf", "of the Bear", "of the Serpent",
                "of the Dungeon", "of Forgotten Kings", "of the Final Seal", "of the Lich",
                "of Eternal Flame", "of the Abyss", "of Shattered Stars"]
    while len(items) < target:
        base = random.choice(base_list)
        name = random.choice(prefixes) + " " + base["name"]
        if random.random() < 0.3:
            name = name + " " + random.choice(suffixes)
        new_item = copy.deepcopy(base)
        new_item["name"] = name
        new_item["type"] = random.choice(types)
        new_item["value"] = int(base["value"] * random.uniform(0.8, 1.5))
        if new_item not in items:
            items.append(new_item)
    return items[:target]


def expand_ground_loot(base_loot):
    """Expand each zone's loot table with more items."""
    expanded = {}
    for zone, data in base_loot.items():
        items = data["items"]
        chances = data["chances"]
        new_items = items[:]
        for _ in range(50):
            base_item = random.choice(items)
            new_item = copy.deepcopy(base_item)
            new_item["name"] = random.choice(
                ["Strange", "Glowing", "Faint", "Cracked", "Shiny", "Dusty",
                 "Ancient", "Runed", "Bloodied", "Spectral", "Frostbitten"]
            ) + " " + new_item["name"]
            new_items.append(new_item)
        new_chances = chances * (len(new_items) // len(chances) + 1)
        new_chances = new_chances[:len(new_items)]
        total = sum(new_chances)
        new_chances = [c / total for c in new_chances]
        expanded[zone] = {"items": new_items, "chances": new_chances}
    return expanded


def expand_traps(base_list, target=60):
    """Expand traps."""
    if len(base_list) >= target:
        return base_list[:]
    traps = base_list[:]
    effects = ["damage", "poison", "burn", "curse", "paralyze", "slow", "blind",
               "silence", "confusion", "fear", "weakness", "stun", "teleport",
               "weaken", "drain_mana", "drain_gold", "summon_enemy"]
    zones = ["entrance", "mid", "deep"]
    names = ["Pit", "Spike", "Arrow", "Blade", "Gas", "Rune", "Glyph", "Web", "Net",
             "Boulder", "Chasm", "Flame", "Frost", "Lightning", "Acid", "Sonic",
             "Gravity", "Teleport", "Illusion", "Curse", "Venom", "Soul", "Shadow",
             "Mirror", "Time", "Void", "Summoning"]
    while len(traps) < target:
        base = random.choice(base_list)
        new_trap = copy.deepcopy(base)
        new_trap["name"] = random.choice(names) + " Trap"
        new_trap["zone"] = random.choice(zones)
        new_trap["effect"] = random.choice(effects)
        new_trap["save_dc"] = random.randint(8, 18)
        new_trap["damage"] = random.randint(3, 15)
        if new_trap not in traps:
            traps.append(new_trap)
    return traps[:target]


def expand_npcs(base_list, target=80):
    """Expand NPCs."""
    if len(base_list) >= target:
        return base_list[:]
    npcs = base_list[:]
    names = ["Old Sage", "Mysterious Stranger", "Goblin Prisoner", "Ghost Knight",
             "Dragon Priest", "Lich Echo", "Wandering Bard", "Merchant",
             "Healer", "Blacksmith", "Alchemist", "Ranger", "Thief",
             "Paladin", "Wizard", "Sorceress", "Cleric", "Druid",
             "Barbarian", "Monk", "Necromancer", "Summoner", "Enchanter",
             "Diviner", "Illusionist", "Transmuter", "Abjurer", "Warden",
             "Cartographer", "Architect", "Spy", "Penitent", "Oracle"]
    zones = ["entrance", "mid", "deep", "boss"]
    quest_giver = [True, False]
    dialogues = [
        "The {name} says: 'Beware the shadows.'",
        "The {name} whispers: 'Seek the three keys.'",
        "The {name} offers: 'I can sell you supplies.'",
        "The {name} warns: 'The Lich is immortal without his phylactery.'",
        "The {name} chants: 'Fire will cleanse the curse.'",
        "The {name} murmurs: 'Follow the river of stars.'",
        "The {name} grins: 'For a price, I'll share a secret.'",
        "The {name} prays: 'May the light guide you.'",
        "The {name} sneers: 'You think you can survive here?'",
        "The {name} laughs: 'I've seen heroes come and go.'",
        "The {name} confesses: 'I helped the Lich. I regret it with every breath.'",
        "The {name} urges: 'The seven seals must all be broken before you face him.'",
        "The {name} reveals: 'There is a back door. The architect knows it.'",
        "The {name} begs: 'Free the souls trapped in the crystals. Please.'",
        "The {name} trades: 'A Map Fragment for a Greater Health Potion.'",
    ]
    while len(npcs) < target:
        name = random.choice(names)
        zone = random.choice(zones)
        dialogue = random.choice(dialogues).replace("{name}", name)
        quest = random.choice(quest_giver)
        npc = {"name": name, "zone": zone, "dialogue": dialogue, "quest_giver": quest}
        if npc not in npcs:
            npcs.append(npc)
    return npcs[:target]


def expand_quest_hints(base_hints):
    """Expand quest hints per zone."""
    expanded = {}
    for zone, hints in base_hints.items():
        new_hints = hints[:]
        more_hints = [
            f"A mysterious note: 'The {zone} holds the key.'",
            f"You overhear a ghost: 'In the {zone}, you will find the truth.'",
            f"A carving on the wall: '{zone.upper()} awaits the worthy.'",
            f"Scratched into the floor: '{zone} is where the artifact lies.'",
            f"A dying adventurer gasps: 'Go to the {zone}...'",
            f"An oracle's voice echoes: 'Your destiny lies in the {zone}.'",
            f"A bloodstained journal entry: 'The seal in the {zone} must break first.'",
            f"An etching: 'Only those who survive the {zone} are worthy of what comes next.'",
        ]
        new_hints.extend(more_hints * 20)
        expanded[zone] = new_hints[:40]
    return expanded


def expand_quests(base_list, target=40):
    """Generate more quests."""
    if len(base_list) >= target:
        return base_list[:]
    quests = base_list[:]
    types = ["kill", "collect", "threshold", "explore", "talk", "use", "lore", "escort", "destroy"]
    targets = ["Goblin", "Skeleton", "Orc", "Dragon", "Lich", "Giant", "Spider",
               "Gold Coins", "Health Potion", "Ancient Sword", "Dragon Scale",
               "Minion Essence", "Demon Heart", "Vampire Fang", "Soul Crystal",
               "Map Fragment", "Seal Fragment", "Blood Grimoire", "Purification Crystal",
               "Entrance", "Mid", "Deep", "Boss", "Old Sage", "Dragon Priest"]
    while len(quests) < target:
        q = copy.deepcopy(random.choice(base_list))
        q["id"] = f"q_{random.randint(1000, 9999)}"
        verb = random.choice(["Slay", "Collect", "Find", "Defeat", "Explore", "Talk to", "Retrieve"])
        noun = random.choice(targets)
        q["name"] = f"Quest {len(quests)+1}: {verb} {noun}"
        q["description"] = "A new quest has been discovered in the depths."
        obj_type = random.choice(types)
        obj_target = random.choice(targets)
        required = random.randint(1, 5)
        q["objectives"] = [{"type": obj_type, "target": obj_target, "current": 0, "required": required}]
        if q not in quests:
            quests.append(q)
    return quests[:target]


def expand_lore(base_list, target=100):
    """Generate more lore fragments."""
    if len(base_list) >= target:
        return base_list[:]
    lore = base_list[:]
    topics = [
        "The dungeon was built by the dwarves.",
        "A great battle was fought here centuries ago.",
        "The Lich was once a righteous king.",
        "Three heroes sealed the evil long ago.",
        "The Goblin King stole the crown of the fallen empire.",
        "Dragons helped shape the caverns with their breath.",
        "A curse turns the living into undead at midnight.",
        "The stars predicted the Lich's return.",
        "An oracle lives deep within the dungeon's heart.",
        "The phylactery is hidden in the final boss room.",
        "Minions are created from the Lich's own shadow.",
        "Red minions are the most ferocious and loyal.",
        "Ancient runes speak of a seven-part prophecy.",
        "The dungeon shifts its layout every century.",
        "A hidden treasure awaits the champion who breaks all seals.",
        "The walls are soaked in centuries of blood and magic.",
        "Legends tell of a weapon that can slay the Lich in one blow.",
        "The crown of bones is a key to the final door.",
        "Three dragon scales unlock the path to the Lich's sanctum.",
        "The spirit of the dungeon is ancient, sorrowful, and wise.",
        "The seven seals were placed by the dungeon's original architect.",
        "The Dungeon Heart beats once per hour. Listen for it.",
        "The Blood Witch was betrayed by the Lich and seeks revenge.",
        "The Betrayer King sold his kingdom for a immortality he regrets.",
        "Four souls wait to be freed from their crystal prisons.",
    ]
    while len(lore) < target:
        new_lore = (random.choice(topics) + " " +
                    random.choice(["Legends say...", "You recall...", "The walls whisper...",
                                   "A ghost tells you...", "An inscription reads...",
                                   "A dying adventurer confirmed it."]))
        if new_lore not in lore:
            lore.append(new_lore)
    return lore[:target]


def build_expanded():
    templates = copy.deepcopy(BASE)
    # Expand descriptive lists to ~400 items
    for key in ["room_descriptions", "ambient", "action_responses", "monster_encounters",
                "loot_descriptions", "combat_responses", "trap_responses", "npc_dialogues",
                "riddles", "prophecies", "magical_events", "model_unavailable"]:
        if key in templates:
            templates[key] = expand_list(templates[key], target_min=400)
    # Expand structured data
    templates["monsters"] = expand_monsters(templates["monsters"], target=100)
    templates["items"] = expand_items(templates["items"], target=200)
    templates["ground_loot"] = expand_ground_loot(templates["ground_loot"])
    templates["traps"] = expand_traps(templates["traps"], target=60)
    templates["npcs"] = expand_npcs(templates["npcs"], target=80)
    templates["quest_hints"] = expand_quest_hints(templates["quest_hints"])
    templates["quests"] = expand_quests(templates["quests"], target=40)
    templates["lore_fragments"] = expand_lore(templates["lore_fragments"], target=100)
    # Expand nli_fallback_messages
    for tool, msgs in templates["nli_fallback_messages"].items():
        expanded_msgs = msgs[:]
        for _ in range(20):
            for m in msgs:
                new_m = m + " " + random.choice([
                    "The dungeon hums.", "Shadows flicker.", "You feel a chill.",
                    "Mystic energy swirls.", "An unseen presence watches.",
                    "Time seems to slow.", "A distant rune glows briefly.",
                    "Stone groans underfoot.", "The air tastes of old magic."
                ])
                if new_m not in expanded_msgs:
                    expanded_msgs.append(new_m)
        templates["nli_fallback_messages"][tool] = expanded_msgs[:30]
    return templates


# ======================================================================
# 3. MAIN: GENERATE TEMPLATES.JSON
# ======================================================================
if __name__ == "__main__":
    random.seed(42)  # for reproducibility
    expanded = build_expanded()
    with open("templates.json", "w") as f:
        json.dump(expanded, f, indent=2, ensure_ascii=False)
    total = sum(
        len(v) if isinstance(v, list) else
        sum(len(sv) if isinstance(sv, list) else 1 for sv in v.values()) if isinstance(v, dict) else 1
        for v in expanded.values()
    )
    print(f"templates.json generated with {total} total items across {len(expanded)} sections.")
    print(f"  Quests: {len(expanded.get('quests', []))}")
    print(f"  Monsters: {len(expanded.get('monsters', []))}")
    print(f"  Items: {len(expanded.get('items', []))}")
    print(f"  Story Arcs: {len(expanded.get('story_arcs', []))}")
    print(f"  Boss Intros: {len(expanded.get('boss_intros', []))}")
    print(f"  Cinematic Events: {len(expanded.get('cinematic_events', []))}")
'''

# ---------- JSON files ----------

CRAFTING_RECIPES_JSON = '''{
  "weapons": {
    "Iron Sword": {
      "materials": { "Metal Scrap": 3, "Leather Scrap": 1 },
      "gold_cost": 10,
      "result": {
        "name": "Iron Sword",
        "type": "weapon",
        "bonus": 2,
        "value": 20,
        "consumable": false
      }
    },
    "Steel Axe": {
      "materials": { "Metal Scrap": 4 },
      "gold_cost": 15,
      "result": {
        "name": "Steel Axe",
        "type": "weapon",
        "bonus": 3,
        "value": 30,
        "consumable": false
      }
    },
    "Elven Bow": {
      "materials": { "Wood Scrap": 2, "Essence": 1 },
      "gold_cost": 25,
      "result": {
        "name": "Elven Bow",
        "type": "weapon",
        "bonus": 4,
        "value": 50,
        "consumable": false
      }
    }
  },
  "armor": {
    "Leather Armor": {
      "materials": { "Leather Scrap": 3 },
      "gold_cost": 10,
      "result": {
        "name": "Leather Armor",
        "type": "armor",
        "bonus": 1,
        "value": 15,
        "consumable": false
      }
    },
    "Chainmail": {
      "materials": { "Metal Scrap": 3, "Leather Scrap": 1 },
      "gold_cost": 20,
      "result": {
        "name": "Chainmail",
        "type": "armor",
        "bonus": 2,
        "value": 30,
        "consumable": false
      }
    },
    "Plate Armor": {
      "materials": { "Metal Scrap": 6 },
      "gold_cost": 40,
      "result": {
        "name": "Plate Armor",
        "type": "armor",
        "bonus": 3,
        "value": 60,
        "consumable": false
      }
    }
  },
  "potions": {
    "Lesser Health Potion": {
      "materials": { "Herb Bundle": 2, "Essence": 1 },
      "gold_cost": 5,
      "result": {
        "name": "Lesser Health Potion",
        "type": "consumable",
        "effect": "heal",
        "value": 10,
        "tier": "lesser",
        "consumable": true
      }
    },
    "Normal Health Potion": {
      "materials": { "Herb Bundle": 3, "Essence": 2 },
      "gold_cost": 10,
      "result": {
        "name": "Normal Health Potion",
        "type": "consumable",
        "effect": "heal",
        "value": 20,
        "tier": "normal",
        "consumable": true
      }
    },
    "Greater Health Potion": {
      "materials": { "Herb Bundle": 4, "Essence": 3 },
      "gold_cost": 20,
      "result": {
        "name": "Greater Health Potion",
        "type": "consumable",
        "effect": "heal",
        "value": 40,
        "tier": "greater",
        "consumable": true
      }
    },
    "Superior Health Potion": {
      "materials": { "Herb Bundle": 6, "Essence": 5 },
      "gold_cost": 40,
      "result": {
        "name": "Superior Health Potion",
        "type": "consumable",
        "effect": "heal",
        "value": 70,
        "tier": "superior",
        "consumable": true
      }
    },
    "Supreme Health Potion": {
      "materials": { "Herb Bundle": 8, "Essence": 7, "Gem Shard": 1 },
      "gold_cost": 80,
      "result": {
        "name": "Supreme Health Potion",
        "type": "consumable",
        "effect": "heal",
        "value": 100,
        "tier": "supreme",
        "consumable": true
      }
    }
  },
  "permanent_potions": {
    "Potion of Vitality": {
      "materials": { "Dragon Scale": 1, "Essence": 3 },
      "gold_cost": 200,
      "result": { "effect": "permanent_hp_boost", "value": 10 },
      "max_consumed": 1
    },
    "Elixir of Strength": {
      "materials": { "Ogre Tooth": 1, "Essence": 2 },
      "gold_cost": 150,
      "result": { "effect": "permanent_attack_boost", "value": 1 },
      "max_consumed": 1
    },
    "Potion of Resilience": {
      "materials": { "Troll Hide": 1, "Essence": 2 },
      "gold_cost": 150,
      "result": { "effect": "permanent_defense_boost", "value": 1 },
      "max_consumed": 1
    }
  }
}'''

ENV_EXAMPLE = '''# Ollama Configuration
OLLAMA_ENDPOINT=http://localhost:11434/api/generate
MODEL=nemotron-3-nano:4b

# Small‑model tuning
LLM_TIMEOUT=8000
LLM_MAX_RETRIES=1

# Game Configuration
PYTHON_CMD=python3
TEMPLATES_FILE=./templates.json
CRAFTING_RECIPES_FILE=./crafting_recipes.json
DUNGEON_SIZE=50
SOUL_FILE=./character_soul.md
CHARACTER_HISTORY=./character_history.md
DEEP_STORY_MODE=false

# Feature flags
NLI_ENABLED=true
NARRATOR_ENABLED=true

# Debug
DEBUG=false
JSON_ERROR_LOG=./dungeonclaw_errors.ndjson
'''

SKILL_MD = '''# DungeonClaw SKILL.md – Game Knowledge Base

## Commands
- move / go <direction> – move between rooms (north, south, east, west)
- look / examine – describe the current room
- attack / fight – attack the current monster
- defend / block – take a defensive stance (reduces damage this round)
- flee [direction] – attempt to escape combat
- search / loot – search the room for hidden items
- take <item> – pick up a named item
- equip <item> – equip a weapon or armor from inventory
- use <item> – use a consumable item
- craft <recipe> – craft an item from ingredients
- talk / speak – talk to any NPC in the room
- rest / heal – rest to recover HP (costs a turn)
- status / stats – view your current stats
- inventory / bag – view your inventory
- quests / journal – view active and completed quests
- lore / knowledge – view discovered lore fragments
- accept quest – accept a pending quest from an NPC
- /blacksmith – Open the blacksmith menu to craft weapons/armor, upgrade artifacts, or recycle items.
- /alchemist – Open the alchemist menu to brew potions (including permanent stat boosters) or recycle items.
- /recycle – Quickly recycle an item from your inventory into crafting materials.

## Combat Rules
- Each round: player attacks, then monster counter-attacks
- Attack roll: 1d20 + attack_bonus vs monster AC (10 + defense)
- Damage roll: monster.damage_range + damage_bonus
- Critical hit on natural 20: damage doubled
- Fumble on natural 1: automatic miss
- Defend: disadvantage on monster attack roll (rolls 2d20, takes lower)
- Flee: success chance = 50% + 5% per level above monster
- Death: HP reaches 0 — game over

## Crafting Recipes
| Recipe                | Ingredients                        | Effect         |
|-----------------------|------------------------------------|----------------|
| Goblin Ear Potion     | 3× Goblin Ear                      | Heal 20 HP     |
| Minion Essence Potion | 2× Minion Essence                  | +2 ATK (3 rnd) |
| Silk Cloth            | 2× Spider Silk + 5 gold            | Armor +1 DEF   |
| Orcish Elixir         | 1× Orc Axe + 10 gold               | Heal 40 HP     |

## Zones
| Zone     | Rooms   | Difficulty | Notes                     |
|----------|---------|------------|---------------------------|
| entrance | 0–12    | Easy       | Goblins, basic loot       |
| mid      | 13–27   | Medium     | Orcs, traps, NPCs         |
| deep     | 28–48   | Hard       | Trolls, rare artifacts    |
| boss     | 49+     | Lethal     | Unique boss monsters      |

## Items by Type
- weapon: adds to attack_bonus and damage_bonus
- armor: adds to defense_bonus
- consumable: one-use item (potions, scrolls)
- misc: quest items, crafting ingredients

## Model Tier Hints
- Sub-1B (TinyLlama, Qwen2.5-0.5B): Use NLI-only mode (NLI_ENABLED=true, NARRATOR_ENABLED=false)
- 1–4B (nemotron-nano, Qwen2.5-1.5B): NARRATOR_ENABLED=true, LLM_TIMEOUT=6000
- 4–8B (Mistral-7B, Llama3-8B): Full features, richer narration, LLM_TIMEOUT=10000
- 13B+: Enable DEEP_STORY_MODE=true for multi-paragraph narration
'''

PACKAGE_JSON = '''{
  "name": "dungeonclaw",
  "version": "6.1.0",
  "description": "Epic Fantasy AI Dungeon Master – Full RPG with TUI, spell correction, and model-tier scaling",
  "type": "module",
  "main": "dist/dungeonclaw.js",
  "scripts": {
    "start": "tsx src/dungeonclaw.ts",
    "build": "tsc",
    "start:compiled": "node dist/dungeonclaw.js"
  },
  "dependencies": {
    "axios": "^1.6.0",
    "dotenv": "^16.3.1",
    "python-shell": "5.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "tsx": "^4.0.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}'''

TUI_JS = '''// tui.js
import * as rl from 'readline';

const W = process.stdout.columns || 80;

// ANSI escape codes
export const C = {
  reset: '\\x1b[0m',
  bold:  '\\x1b[1m',
  red:   '\\x1b[31m',
  green: '\\x1b[32m',
  yellow:'\\x1b[33m',
  cyan:  '\\x1b[36m',
  white: '\\x1b[37m',
  gray:  '\\x1b[90m',
  bg_red: '\\x1b[41m',
  bg_blue:'\\x1b[44m',
};

// Box drawing
export function box(title, lines, color = C.white) {
  const inner = W - 4;
  const top    = `${color}╔${'═'.repeat(inner)}╗${C.reset}`;
  const bottom = `${color}╚${'═'.repeat(inner)}╝${C.reset}`;
  const pad = (s) => {
    // Strip ANSI codes to calculate visible length
    const vis = s.replace(/\\x1b\\[[0-9;]*m/g, '').length;
    return `${color}║${C.reset} ${s}${' '.repeat(Math.max(0, inner - vis - 2))} ${color}║${C.reset}`;
  };
  const titleLine = pad(`${C.bold}${color} ${title} ${C.reset}`);
  console.log([top, titleLine, `${color}╠${'═'.repeat(inner)}╣${C.reset}`, ...lines.map(pad), bottom].join('\\n'));
}

// Progress bar (correctly handles ANSI colors in label)
export function bar(label, current, max, width = 20, fillColor = C.green) {
  const pct  = Math.max(0, Math.min(1, current / max));
  const fill = Math.round(pct * width);
  const empty = width - fill;
  const b = `${fillColor}${'█'.repeat(fill)}${C.gray}${'░'.repeat(empty)}${C.reset}`;
  // Remove ANSI from label for alignment
  const labelVis = label.replace(/\\x1b\\[[0-9;]*m/g, '');
  const padLen = Math.max(0, 8 - labelVis.length);
  const paddedLabel = label + ' '.repeat(padLen);
  return `${paddedLabel} ${b} ${current}/${max}`;
}

// Dice animation (Unicode die faces)
const D20_FACES = ['⚀','⚁','⚂','⚃','⚄','⚅'];
const sleep = ms => new Promise(r => setTimeout(r, ms));

export async function animateDiceRoll(rolls, notation, total, modifier = 0) {
  const frames = 8;
  process.stdout.write('\\n  ');
  for (let i = 0; i < frames; i++) {
    rl.clearLine(process.stdout, 0);
    rl.cursorTo(process.stdout, 0);
    const face = D20_FACES[Math.floor(Math.random() * 6)];
    process.stdout.write(`  ${C.yellow}Rolling ${notation}... ${face}  ${C.reset}`);
    await sleep(60);
  }
  rl.clearLine(process.stdout, 0);
  rl.cursorTo(process.stdout, 0);

  const rollStr = rolls.map(r => {
    if (r === 20) return `${C.green}${C.bold}[20!]${C.reset}`;
    if (r === 1)  return `${C.red}${C.bold}[1]${C.reset}`;
    return `${C.yellow}[${r}]${C.reset}`;
  }).join(' + ');

  const modStr = modifier !== 0 ? ` ${modifier >= 0 ? '+' : ''}${modifier}` : '';
  console.log(`  ${C.bold}🎲 ${notation}${C.reset}  ${rollStr}${modStr} = ${C.bold}${C.white}${total}${C.reset}\\n`);
}

// Status strip
export function printStatus(player, roomZone, model) {
  const hpColor = player.hp < player.maxHp * 0.3 ? C.red : C.green;
  const hp  = bar('HP', player.hp, player.maxHp, 15, hpColor);
  const xp  = bar('XP', player.xp, player.xpToNext, 12, C.cyan);
  const line = [
    `${C.bold}Lv.${player.level}${C.reset}`,
    hp, xp,
    `${C.yellow}⚔ +${player.attack_bonus}${C.reset}`,
    `${C.cyan}🛡 +${player.defense_bonus}${C.reset}`,
    `${C.yellow}💰${player.gold}g${C.reset}`,
    `${C.gray}[${roomZone}]${C.reset}`,
    `${C.gray}${model}${C.reset}`,
  ].join('  ');
  console.log('\\n' + line + '\\n');
}

// Dungeon Master speech
export function dm(text) {
  console.log(`${C.bold}${C.white}Dungeon Master:${C.reset} ${text}\\n`);
}

// Combat theater
export function combatHeader(playerHp, playerMaxHp, monsterName, monsterHp, monsterMaxHp) {
  const lines = [
    bar('YOU', playerHp, playerMaxHp, 20),
    bar(monsterName.substring(0, 8), monsterHp, monsterMaxHp, 20, C.red),
    '',
    `${C.gray}  Actions: [A]ttack  [D]efend  [U]se item  [F]lee${C.reset}`,
  ];
  box('⚔  COMBAT', lines, C.red);
}

// Room entry
export function printRoom(mechanics) {
  const exits = mechanics.exits?.join(', ') || 'none';
  const lines = [
    `${C.white}${mechanics.description}${C.reset}`,
    mechanics.ambient ? `${C.gray}${mechanics.ambient}${C.reset}` : '',
    '',
    `${C.cyan}Exits: ${C.bold}${exits}${C.reset}`,
    mechanics.monster ? `${C.red}⚠  ${mechanics.monster.name} lurks here!${C.reset}` : '',
    mechanics.npc ? `${C.yellow}🗣  ${mechanics.npc.name} is here.${C.reset}` : '',
  ].filter(Boolean);
  box(`Room ${mechanics.room_id} — ${mechanics.zone.toUpperCase()}`, lines, C.cyan);
}
'''

FUZZ_JS = '''// fuzzy.js – Levenshtein-based command spell checker

const VOCAB = [
  'north','south','east','west','go','move','exit','leave',
  'look','examine','describe','search','loot','find',
  'attack','fight','hit','strike','kill','slay',
  'defend','block','parry','guard',
  'flee','run','retreat','escape',
  'take','get','pick',
  'use','equip','wield','wear',
  'craft','make',
  'talk','speak','converse','greet',
  'rest','heal','sleep','recover','camp',
  'status','stats','hp','health','inventory','bag','items',
  'quests','journal','log','lore','knowledge',
  'accept','save','load','help',
  'blacksmith','alchemist','recycle','forge','brew',
];

function levenshtein(a, b) {
  const m = a.length, n = b.length;
  const dp = Array.from({length: m+1}, (_,i) => Array.from({length: n+1}, (_,j) => i===0?j:j===0?i:0));
  for (let i=1;i<=m;i++) for (let j=1;j<=n;j++)
    dp[i][j] = a[i-1]===b[j-1] ? dp[i-1][j-1] : 1+Math.min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1]);
  return dp[m][n];
}

export function spellCorrectTokens(input) {
  const tokens = input.trim().toLowerCase().split(/\\s+/);
  const corrected = tokens.map(token => {
    if (VOCAB.includes(token)) return token;
    if (token.length < 2) return token;
    let best = token, bestDist = Infinity;
    for (const word of VOCAB) {
      if (Math.abs(word.length - token.length) > 3) continue;
      const d = levenshtein(token, word);
      if (d < bestDist && d <= Math.max(1, Math.floor(token.length / 3))) {
        bestDist = d; best = word;
      }
    }
    return best;
  });
  const result = corrected.join(' ');
  return result !== input.trim().toLowerCase() ? { corrected: result, original: input } : { corrected: input, original: input };
}
'''

MODEL_TIER_JS = '''// model_tier.js

export function detectTier(modelName) {
  const name = modelName.toLowerCase();
  // Explicit size suffixes take priority
  if (/\\b(0\\.5b|0\\.4b|1b|tiny)\\b/.test(name)) return 'tiny';
  if (/\\b(1\\.5b|2b|3b|4b|nano)\\b/.test(name)) return 'small';   // nano → small
  if (/\\b(7b|8b)\\b/.test(name)) return 'medium';
  if (/\\b(13b|14b|20b|30b|70b)\\b/.test(name)) return 'large';
  // Fallback to small if nothing matches
  return 'small';
}

export const TIER_CONFIG = {
  tiny: {
    narrator: false,
    questGen: false,
    llmFallback: false,
    maxTokens: 60,
    temperature: 0.3,
    combatFlavor: false,
    nliOnly: true,
  },
  small: {
    narrator: true,
    questGen: false,
    llmFallback: true,
    maxTokens: 80,
    temperature: 0.4,
    combatFlavor: true,
    nliOnly: false,
  },
  medium: {
    narrator: true,
    questGen: true,
    llmFallback: true,
    maxTokens: 120,
    temperature: 0.6,
    combatFlavor: true,
    nliOnly: false,
  },
  large: {
    narrator: true,
    questGen: true,
    llmFallback: true,
    maxTokens: 200,
    temperature: 0.75,
    combatFlavor: true,
    deepStory: true,
    nliOnly: false,
  },
};
'''

NLI_JS = '''// nli.js – deterministic intent mapper, zero latency, plus shorthand

const INTENT_MAP = [
  // Movement – includes single letters
  {
    patterns: [
      /^go\\s+(north|south|east|west)/i,
      /^move\\s+(north|south|east|west)/i,
      /^exit\\s+(north|south|east|west)/i,
      /^leave\\s+(north|south|east|west)/i,
      /^(north|south|east|west)$/i,
      /^n$/i, /^s$/i, /^e$/i, /^w$/i,
    ],
    tool: 'move',
    extractArgs: (input) => {
      const m = input.match(/\\b(north|south|east|west)\\b/i);
      return m ? { direction: m[1].toLowerCase() } : null;
    }
  },
  // Look
  {
    patterns: [/^look/i, /^describe/i, /^what('?s| is) here/i, /^where am i/i, /^examine/i, /^l$/i],
    tool: 'look',
    extractArgs: () => ({})
  },
  // Take specific item
  {
    patterns: [/^take\\s+(.+)/i, /^get\\s+(.+)/i],
    tool: 'take',
    extractArgs: (input) => {
      const m = input.match(/^take\\s+(.+)/i) || input.match(/^get\\s+(.+)/i);
      return m ? { item_name: m[1].trim() } : null;
    }
  },
  // Search / loot
  {
    patterns: [/^search/i, /^loot/i, /^find/i, /^check for/i, /^pick up/i],
    tool: 'search',
    extractArgs: () => ({})
  },
  // Attack – includes single 'a'
  {
    patterns: [/^attack/i, /^fight/i, /^hit/i, /^strike/i, /^kill/i, /^slay/i, /^a$/i],
    tool: 'attack',
    extractArgs: () => ({})
  },
  // Defend
  {
    patterns: [/^defend/i, /^block/i, /^parry/i, /^guard/i],
    tool: 'defend',
    extractArgs: () => ({})
  },
  // Flee – includes single 'f'
  {
    patterns: [/^flee/i, /^run\\s*(away)?$/i, /^retreat/i, /^escape/i, /^f$/i],
    tool: 'flee',
    extractArgs: (input) => {
      const m = input.match(/\\b(north|south|east|west)\\b/i);
      return m ? { direction: m[1].toLowerCase() } : {};
    }
  },
  // Use item
  {
    patterns: [/^use\\s+(.+)/i],
    tool: 'use',
    extractArgs: (input) => {
      const m = input.match(/^use\\s+(.+)/i);
      return m ? { item_name: m[1].trim() } : null;
    }
  },
  // Equip item
  {
    patterns: [/^equip\\s+(.+)/i, /^wield\\s+(.+)/i, /^wear\\s+(.+)/i],
    tool: 'equip',
    extractArgs: (input) => {
      const m = input.match(/^(equip|wield|wear)\\s+(.+)/i);
      return m ? { item_name: m[2].trim() } : null;
    }
  },
  // Craft item
  {
    patterns: [/^craft\\s+(.+)/i, /^make\\s+(.+)/i],
    tool: 'craft',
    extractArgs: (input) => {
      const m = input.match(/^(craft|make)\\s+(.+)/i);
      return m ? { recipe_name: m[2].trim() } : null;
    }
  },
  // Talk to NPC
  {
    patterns: [/^talk/i, /^speak/i, /^converse/i, /^greet/i],
    tool: 'talk',
    extractArgs: () => ({})
  },
  // Accept quest
  {
    patterns: [/^accept quest/i, /^take quest/i, /^yes,? (i )?accept/i, /^i will accept/i, /^i take the quest/i],
    tool: 'accept_quest',
    extractArgs: () => ({})
  },
  // Rest
  {
    patterns: [/^rest/i, /^heal/i, /^sleep/i, /^recover/i, /^camp/i],
    tool: 'rest',
    extractArgs: () => ({})
  },
  // Status
  {
    patterns: [/^(my )?(stats?|status|hp|health)/i, /^how (am i|is my health)/i],
    tool: 'status',
    extractArgs: () => ({})
  },
  // Inventory
  {
    patterns: [/^(my )?(inventory|bag|items|pack)/i, /^what do i (have|carry)/i],
    tool: 'inventory',
    extractArgs: () => ({})
  },
  // Quests
  {
    patterns: [/^quests?/i, /^journal/i, /^log/i],
    tool: 'quest_log',
    extractArgs: () => ({})
  },
  // Lore
  {
    patterns: [/^lore/i, /^knowledge/i, /^story/i],
    tool: 'lore',
    extractArgs: () => ({})
  },
  // Blacksmith
  {
    patterns: [/^blacksmith/i, /^forge/i, /^smith/i],
    tool: 'blacksmith_menu',
    extractArgs: () => ({})
  },
  // Alchemist
  {
    patterns: [/^alchemist/i, /^brew/i, /^potion/i],
    tool: 'alchemist_menu',
    extractArgs: () => ({})
  },
  // Recycle
  {
    patterns: [/^recycle/i, /^scrap/i, /^break down/i],
    tool: 'recycle',
    extractArgs: (input) => {
      const m = input.match(/^recycle\\s+(.+)/i);
      return m ? { item_name: m[1].trim() } : {};
    }
  },
];

export function resolveIntent(input) {
  const trimmed = input.trim();
  for (const intent of INTENT_MAP) {
    for (const pat of intent.patterns) {
      if (pat.test(trimmed)) {
        const args = intent.extractArgs(trimmed);
        if (args !== null) return { tool: intent.tool, args, source: 'nli' };
      }
    }
  }
  return null;
}
'''

# ======================================================================
# Main bootstrapper
# ======================================================================
def main():
    base_dir = Path("dungeonclaw")
    src_dir = base_dir / "src"

    base_dir.mkdir(exist_ok=True)
    src_dir.mkdir(exist_ok=True)

    # Write all files
    file_map = {
        # TypeScript source
        "src/types.ts": TYPES_TS,
        "src/logger.ts": LOGGER_TS,
        "src/nli.ts": NLI_TS,
        "src/soul.ts": SOUL_TS,
        "src/llm.ts": LLM_TS,
        "src/python.ts": PYTHON_TS,
        "src/tools.ts": TOOLS_TS,
        "src/agent.ts": AGENT_TS,
        "src/quests.ts": QUESTS_TS,
        "src/story.ts": STORY_TS,
        "src/dungeonclaw.ts": DUNGEONCLAW_TS,
        # Python
        "game_engine.py": GAME_ENGINE_PY,
        "story_gen.py": STORY_GEN_PY,
        "expand_templates.py": EXPAND_TEMPLATES_PY,
        "templates.py": TEMPLATES_PY,
        # JSON
        "crafting_recipes.json": CRAFTING_RECIPES_JSON,
        # JavaScript (UI, fuzzy, etc)
        "tui.js": TUI_JS,
        "fuzz.js": FUZZ_JS,
        "model_tier.js": MODEL_TIER_JS,
        "nli.js": NLI_JS,
        # Other
        "SKILL.md": SKILL_MD,
        "package.json": PACKAGE_JSON,
        ".env.example": ENV_EXAMPLE,
    }

    for rel_path, content in file_map.items():
        file_path = base_dir / rel_path
        file_path.write_text(content)
        print(f"Created {file_path}")

    # Create tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "ES2022",
            "module": "NodeNext",
            "moduleResolution": "NodeNext",
            "outDir": "dist",
            "rootDir": "src",
            "strict": True,
            "esModuleInterop": True,
            "resolveJsonModule": True,
            "skipLibCheck": True,
            "allowJs": False
        },
        "include": ["src/**/*"],
        "exclude": ["node_modules", "dist"]
    }
    (base_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))
    print("Created tsconfig.json")

    print("\\nDungeonClaw v6.1 project created successfully!")
    print("To run, cd into dungeonclaw and run:")
    print("  npm install")
    print("  npm start")
    print("\\nIf you need the full templates.json, run: python expand_templates.py")

if __name__ == "__main__":
    main()
