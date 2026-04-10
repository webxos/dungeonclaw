// dungeonclaw.js – Full RPG with TUI, fuzzy matching, model-tier scaling, story arcs
import axios from 'axios';
import * as readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { PythonShell } from 'python-shell';
import dotenv from 'dotenv';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { resolveIntent } from './nli.js';
import { spellCorrectTokens } from './fuzz.js';
import { detectTier, TIER_CONFIG } from './model_tier.js';
import { C, box, dm, printStatus, printRoom, combatHeader, animateDiceRoll, restAnimation } from './tui.js';

dotenv.config();

// ---------- Configuration ----------
const OLLAMA_ENDPOINT = process.env.OLLAMA_ENDPOINT || 'http://localhost:11434/api/generate';
let currentModel = process.env.MODEL || 'nemotron-3-nano:4b';
const LLM_TIMEOUT = parseInt(process.env.LLM_TIMEOUT) || 8000;
const LLM_MAX_RETRIES = parseInt(process.env.LLM_MAX_RETRIES) || 1;
const PYTHON_CMD = process.env.PYTHON_CMD || 'python3';
const DUNGEON_SIZE = parseInt(process.env.DUNGEON_SIZE) || 50;
const SOUL_FILE = process.env.SOUL_FILE || path.join(process.cwd(), 'character_soul.md');
const ERROR_LOG = process.env.JSON_ERROR_LOG || path.join(process.cwd(), 'dungeonclaw_errors.ndjson');
const HISTORY_FILE = process.env.CHARACTER_HISTORY || path.join(process.cwd(), 'character_history.md');
const DEBUG = process.env.DEBUG === 'true';
const NLI_ENABLED = process.env.NLI_ENABLED !== 'false';
const DEEP_STORY_MODE = process.env.DEEP_STORY_MODE === 'true';

// Model tier detection
const MODEL_TIER = process.env.MODEL_TIER || 'auto';
let tierCfg;
if (MODEL_TIER === 'auto') {
  const tier = detectTier(currentModel);
  tierCfg = TIER_CONFIG[tier] || TIER_CONFIG.small;
} else {
  tierCfg = TIER_CONFIG[MODEL_TIER] || TIER_CONFIG.small;
}
const NARRATOR_ENABLED = process.env.NARRATOR_ENABLED !== 'false' && tierCfg.narrator;
const QUEST_GEN_ENABLED = tierCfg.questGen;
const LLM_FALLBACK_ENABLED = tierCfg.llmFallback;

// ---------- Game State ----------
let playerName = '';
let currentRoom = 0;
let player = {
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
  alignment: 0,
  stat_choices: []   // track level-up bonuses
};
let quests = [];
let lore = [];
let visited = new Set();
let currentRoomMechanics = null;
let roomCache = new Map();
let combatActive = false;
let consecutiveBattlesNoPotion = 0;   // for survivor quests

const rl = readline.createInterface({ input, output });

// ---------- Enhanced Error Logging ----------
async function logError(severity, category, context, opts = {}) {
  const entry = {
    timestamp: new Date().toISOString(),
    severity,
    category,
    context: context.substring(0, 2000),
    raw: opts.raw,
    stack: opts.stack,
    tool: opts.tool,
    room: opts.room,
    playerLevel: opts.playerLevel,
    ...opts
  };
  try {
    await fs.appendFile(ERROR_LOG, JSON.stringify(entry) + '\n');
  } catch (err) {
    console.error('Failed to write error log:', err.message);
  }
}

// ---------- Soul File Management ----------
let soulWriteQueue = Promise.resolve();

async function readSoul() {
  try {
    const raw = await fs.readFile(SOUL_FILE, 'utf-8');
    const sections = raw.split(/^## /m);
    let persona = 'You are a brave dungeon adventurer.';
    let memory = [];
    let directives = '';

    for (const section of sections) {
      if (section.startsWith('VOICE')) {
        persona = section.substring(5).trim();
      } else if (section.startsWith('MEMORY')) {
        const lines = section.split('\n');
        memory = lines
          .filter(l => l.trim().startsWith('- '))
          .map(l => l.trim().substring(2).trim());
      } else if (section.startsWith('DIRECTIVES')) {
        directives = section.substring(10).trim();
      }
    }
    return { persona, memory, directives };
  } catch (err) {
    const defaultSoul = {
      persona: 'You are a brave adventurer exploring a vast fantasy dungeon. You are courageous, curious, and eager to find treasure and glory. You speak in first person and respond to the Dungeon Master\'s narration.',
      memory: [`[${new Date().toISOString()}] You started your journey in Room 0.`],
      directives: '1. Always suggest 2 next actions.\n2. If HP < 30, recommend rest.\n3. If a monster is present, acknowledge it first.\n4. Do not invent rooms or exits.'
    };
    await writeSoul(defaultSoul, playerName);
    return defaultSoul;
  }
}

async function writeSoul(soul, playerName) {
  const name = playerName || 'Adventurer';
  const content = `# SOUL: ${name}\n\n## VOICE\n${soul.persona}\n\n## MEMORY\n${soul.memory.map(m => `- ${m}`).join('\n')}\n\n## DIRECTIVES\n${soul.directives}`;
  soulWriteQueue = soulWriteQueue.then(() => fs.writeFile(SOUL_FILE, content));
  return soulWriteQueue;
}

async function updateMemory(newEntry) {
  const soul = await readSoul();
  const timestamped = `[${new Date().toISOString()}] ${newEntry}`;
  soul.memory.push(timestamped);
  if (soul.memory.length > 20) soul.memory = soul.memory.slice(-20);
  await writeSoul(soul, playerName);
}

// ---------- Character History Log ----------
async function appendHistory(entry) {
  const timestamp = new Date().toISOString();
  const markdown = `- **${timestamp}** ${entry}\n`;
  await fs.appendFile(HISTORY_FILE, markdown);
}

// ---------- Quest Helpers (Overhauled) ----------
function updateQuestProgress(quests, toolName, result, player, roomId, itemUsed, loreDiscovered = null) {
  return quests.map(q => {
    if (q.completed || q.failed) return q;
    const objectives = q.objectives.map(obj => {
      if (obj.current >= obj.required) return obj;

      switch (obj.type) {
        case 'kill':
          if (toolName === 'attack' && result.success && result.monster_defeated) {
            const killedName = result.monster_name;
            if (obj.target === 'any' || killedName === obj.target || (obj.target === 'Minion' && result.is_minion))
              return { ...obj, current: obj.current + 1 };
          }
          break;
        case 'collect':
          if (toolName === 'take' && result.loot && result.loot.some(i => i.name === obj.target))
            return { ...obj, current: obj.current + 1 };
          break;
        case 'explore':
          if (toolName === 'move' && roomId === obj.target)
            return { ...obj, current: obj.current + 1 };
          break;
        case 'use':
          if (toolName === 'use' && itemUsed === obj.target)
            return { ...obj, current: obj.current + 1 };
          break;
        case 'lore':
          if (loreDiscovered && loreDiscovered === obj.target)
            return { ...obj, current: obj.current + 1 };
          break;
        case 'talk':
          if (toolName === 'talk' && result.message && result.message.includes(obj.target))
            return { ...obj, current: obj.current + 1 };
          break;
        case 'escort':
          if (result.escort_completed && obj.target === result.escort_npc)
            return { ...obj, current: obj.current + 1 };
          break;
        case 'destroy':
          if (result.destroyed_object === obj.target)
            return { ...obj, current: obj.current + 1 };
          break;
        case 'kill_in_zone':
          if (toolName === 'attack' && result.monster_defeated && result.zone === obj.target)
            return { ...obj, current: obj.current + 1 };
          break;
        case 'survive_battles':
          if (toolName === 'attack' && result.monster_defeated && !itemUsed?.includes('potion'))
            return { ...obj, current: obj.current + 1 };
          break;
      }
      return obj;
    });
    return { ...q, objectives };
  });
}

function checkQuestCompletion(quests, player) {
  const completedNames = [];
  let p = { ...player };
  const updated = quests.map(q => {
    if (q.completed || q.failed) return q;
    const allDone = q.objectives.every(o => o.current >= o.required);
    if (!allDone) return q;
    completedNames.push(q.name);
    // scale rewards by player level
    const goldReward = Math.floor(q.reward.gold * (1 + player.level / 10));
    const xpReward = Math.floor(q.reward.xp * (1 + player.level / 8));
    p = {
      ...p,
      gold: p.gold + goldReward,
      xp: p.xp + xpReward,
      inventory: q.reward.item ? [...p.inventory, q.reward.item] : p.inventory
    };
    if (q.alignment_shift) p.alignment = Math.min(10, Math.max(-10, p.alignment + q.alignment_shift));
    return { ...q, completed: true };
  });
  return { quests: updated, player: p, completedNames };
}

function checkQuestFailure(quests, player, currentRoom, combatResult) {
  return quests.map(q => {
    if (q.completed || q.failed) return q;
    if (q.fail_conditions) {
      if (q.fail_conditions.time_limit_rooms && (currentRoom - q.started_room) > q.fail_conditions.time_limit_rooms)
        return { ...q, failed: true };
      if (q.fail_conditions.avoid_kill && combatResult && combatResult.monster_name === q.fail_conditions.avoid_kill)
        return { ...q, failed: true };
      if (q.fail_conditions.alignment_required && Math.abs(player.alignment) < q.fail_conditions.alignment_required)
        return { ...q, failed: true };
    }
    return q;
  });
}

// ---------- Utility ----------
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

function printIntro() {
  const title = `
\u001b[37m
▄               ▜      
▌▌▌▌▛▌▛▌█▌▛▌▛▌▛▘▐ ▀▌▌▌▌
▙▘▙▌▌▌▙▌▙▖▙▌▌▌▙▖▐▖█▌▚▚▘
      ▄▌
\u001b[0m`;
  console.log(title);
  console.log('\u001b[1;37m╔══════════════════════════════════════════════════════════════╗\u001b[0m');
  console.log('\u001b[1;37m║        D U N G E O N C L A W    v6.2  (Balanced & Overhauled) ║\u001b[0m');
  console.log('\u001b[1;37m║     Fixed quests • Better economy • Balanced combat           ║\u001b[0m');
  console.log('\u001b[1;37m╚══════════════════════════════════════════════════════════════╝\u001b[0m\n');
}

// ---------- Python Tool Call with Safety ----------
async function callPythonTool(command, args = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      mode: 'json',
      pythonPath: PYTHON_CMD,
      scriptPath: '.',
      args: [command, JSON.stringify(args)]
    };
    let stderrOutput = '';
    const pyshell = new PythonShell('game_engine.py', options);
    pyshell.on('stderr', data => { stderrOutput += data; });
    pyshell.on('error', err => {
      logError('error', 'python_tool', `Python error: ${err.message}`, { raw: stderrOutput });
      reject(new Error(`Python error: ${err.message}\nStderr: ${stderrOutput}`));
    });
    const results = [];
    pyshell.on('message', message => { results.push(message); });
    pyshell.end(err => {
      if (err) {
        logError('error', 'python_tool', `Python shell error: ${err.message}`, { raw: stderrOutput });
        reject(new Error(`Python shell error: ${err.message}\nStderr: ${stderrOutput}`));
      } else if (results.length === 0) {
        logError('error', 'python_tool', 'No output from Python', { raw: stderrOutput });
        reject(new Error(`No output from Python\nStderr: ${stderrOutput}`));
      } else {
        resolve(results[0]);
      }
    });
  });
}

async function safeToolCall(tool, args, fallback = null) {
  try {
    return await callPythonTool('execute_tool', { tool, args, state: buildGameState() });
  } catch (err) {
    await logError('error', 'python_tool', err.message, { tool, args: JSON.stringify(args) });
    if (fallback !== null) return fallback;
    return { success: false, message: `Tool "${tool}" failed: ${err.message}` };
  }
}

// ---------- LLM Calls with Timeout ----------
async function callOllama(prompt, system) {
  const payload = {
    model: currentModel,
    prompt: prompt,
    system: system,
    stream: false,
    format: 'json',
    options: { temperature: tierCfg.temperature, num_ctx: 768, num_predict: tierCfg.maxTokens }
  };
  for (let attempt = 1; attempt <= LLM_MAX_RETRIES; attempt++) {
    try {
      const response = await axios.post(OLLAMA_ENDPOINT, payload, { timeout: LLM_TIMEOUT });
      const rawText = response.data.response.trim();
      let parsed = null;
      try {
        parsed = JSON.parse(rawText);
      } catch (e) {
        const jsonBlockMatch = rawText.match(/```(?:json)?\s*(\{.*?\})\s*```/s);
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
          await logError('error', 'llm_json', 'LLM returned malformed JSON', { raw: rawText, context: `${system}\n\n${prompt}` });
          return { error: 'Malformed JSON response' };
        }
      }
      return parsed;
    } catch (err) {
      if (attempt < LLM_MAX_RETRIES) {
        const backoff = Math.pow(2, attempt) * 1500;
        await sleep(backoff);
      } else {
        await logError('error', 'llm_json', 'LLM unavailable after retries', { raw: err.message, context: `${system}\n\n${prompt}` });
        return { error: 'LLM failed after retries' };
      }
    }
  }
  return null;
}

async function callOllamaWithTimeout(prompt, system, ms = LLM_TIMEOUT) {
  const timer = new Promise(resolve =>
    setTimeout(() => resolve({ error: 'timeout', message: 'The oracle did not respond in time.' }), ms)
  );
  return Promise.race([callOllama(prompt, system), timer]);
}

async function callOllamaText(prompt, system = '', temperature = null, maxTokens = null) {
  const temp = temperature ?? tierCfg.temperature;
  const tokens = maxTokens ?? tierCfg.maxTokens;
  const payload = {
    model: currentModel,
    prompt,
    system,
    stream: false,
    options: { temperature: temp, num_predict: tokens }
  };
  try {
    const response = await axios.post(OLLAMA_ENDPOINT, payload, { timeout: 5000 });
    return response.data.response?.trim() || '';
  } catch (err) {
    await logError('warn', 'llm_json', 'Text generation failed', { raw: err.message, context: prompt });
    return '';
  }
}

// ---------- Narration with Quest Hints ----------
async function narrateResult(toolName, toolResult, playerName, roomDesc, activeQuestHint = '') {
  if (!NARRATOR_ENABLED) return toolResult.message || "The dungeon stirs...";
  const activeQuest = quests.find(q => !q.completed && !q.failed);
  const questHint = activeQuest ? `Active quest: ${activeQuest.name} — ${activeQuest.description}. ${activeQuestHint}` : '';
  const prompt = `Dungeon Master narration (1-2 sentences, second person, vivid fantasy).
Player: ${playerName}. Action: ${toolName}. Result: ${toolResult.message || "No result"}.
Room: ${roomDesc}. ${questHint}
Hint the quest if relevant. End with a sensory detail.`;
  try {
    const res = await axios.post(OLLAMA_ENDPOINT, { model: currentModel, prompt, stream: false, options: { temperature: 0.7, num_predict: 80 } }, { timeout: 5000 });
    return res.data.response?.trim() || toolResult.message || "The dungeon stirs...";
  } catch { return toolResult.message || "The dungeon stirs..."; }
}

// ---------- Agent Step with Fuzzy and RAG ----------
const VALID_TOOLS = ['move', 'look', 'attack', 'search', 'rest', 'status', 'inventory', 'take', 'equip', 'use', 'flee', 'defend', 'talk', 'quest_log', 'lore', 'craft', 'accept_quest', 'recycle', 'blacksmith_menu', 'alchemist_menu'];

async function runAgentStep(userInput, conversationHistory, state) {
  const { corrected, original } = spellCorrectTokens(userInput);
  if (corrected !== original.trim().toLowerCase()) {
    console.log(`${C.gray}(Understood: "${corrected}")${C.reset}`);
  }
  const effectiveInput = corrected;

  if (NLI_ENABLED) {
    const nliResult = resolveIntent(effectiveInput);
    if (nliResult) {
      const validation = await callPythonTool('validate_intent', {
        tool: nliResult.tool,
        args: nliResult.args,
        state
      }).catch(() => ({ valid: true }));
      if (!validation.valid) {
        return { answer: validation.reason || "You can't do that right now." };
      }
      return { thought: 'NLI resolved', toolName: nliResult.tool, args: nliResult.args, source: 'nli' };
    }
  }

  if (!LLM_FALLBACK_ENABLED) {
    return { answer: `The dungeon doesn't understand "${userInput}". Try: move north/south/east/west, attack, search, rest, look.` };
  }

  // LLM fallback
  const stateSummary = await callPythonTool('tool_summary', { state }).then(r => r.summary || '').catch(() => '');
  const actionMenu = await callPythonTool('get_action_menu', { state }).then(r => r.menu || []).catch(() => []);
  const menuText = actionMenu.map(([key, desc], i) => `${i+1}. ${desc}`).join('\n');
  const soul = await readSoul();

  // RAG context
  let ragContext = '';
  if (LLM_FALLBACK_ENABLED) {
    const ragResults = await callPythonTool('rag_search', { query: effectiveInput, top_k: 3 }).catch(() => ({ results: [] }));
    ragContext = ragResults.results.map(r => `[${r.source}] ${r.text}`).join('\n');
  }

  const systemPrompt = [
    soul.persona,
    ragContext ? `Known facts:\n${ragContext}` : '',
    `Current state: ${stateSummary}`,
    `What do you do? Choose a number or describe your action.`,
    menuText,
    `Reply with a single number or a short phrase (e.g., 'move north', 'attack', 'craft Goblin Ear Potion'). No JSON, just text.`
  ].filter(Boolean).join('\n');
  const recentCtx = conversationHistory.slice(-2).map(h => `User: ${h.user}\nDM: ${h.summary || h.agent}`).join('\n');
  const userPrompt = `${recentCtx}\nUser: ${effectiveInput}\nYour choice:`;
  const response = await callOllamaWithTimeout(userPrompt, systemPrompt);
  if (!response || response.error) {
    return { answer: "The dungeon stirs... (Try: go north, attack, look, rest, craft)" };
  }
  const llmText = (response.answer || response.choice || JSON.stringify(response)).toString();
  const chosenAction = await callPythonTool('parse_llm_choice', { text: llmText, actions: actionMenu }).then(r => r.choice).catch(() => null);
  if (!chosenAction) {
    return { answer: "The oracle is unclear. Perhaps try something simpler?" };
  }
  const parts = chosenAction.split(' ');
  const toolName = parts[0];
  let args = {};
  if (parts.length > 1) {
    const argString = parts.slice(1).join(' ');
    if (toolName === 'move' || toolName === 'flee') args = { direction: argString };
    else if (toolName === 'take' || toolName === 'equip' || toolName === 'use' || toolName === 'recycle') args = { item_name: argString };
    else if (toolName === 'craft') args = { recipe_name: argString };
    else if (toolName === 'accept_quest') args = {};
    else args = { value: argString };
  }
  if (!VALID_TOOLS.includes(toolName)) {
    return { answer: `I don't know how to '${toolName}'.` };
  }
  return { thought: `Chose ${chosenAction}`, toolName, args, source: 'llm' };
}

// ---------- Model Switching ----------
async function switchModel() {
  console.log('\nFetching installed Ollama models...');
  const result = await callPythonTool('list_models').catch(err => {
    console.log(`\x1b[31mError fetching models: ${err.message}\x1b[0m`);
    return null;
  });
  if (!result || result.error) {
    console.log(`\x1b[31mCould not get model list. Is ollama installed? Error: ${result?.error}\x1b[0m`);
    return;
  }
  const models = result.models;
  if (!models.length) {
    console.log('\x1b[31mNo models found. Please install a model with `ollama pull <name>`.\x1b[0m');
    return;
  }
  console.log('\nAvailable models:');
  models.forEach((m, i) => {
    console.log(`  ${i+1}. ${m}`);
  });
  const answer = await rl.question('\nEnter the number of the model to switch to (or press Enter to cancel): ');
  const choice = parseInt(answer);
  if (isNaN(choice) || choice < 1 || choice > models.length) {
    console.log('No change.');
    return;
  }
  const newModel = models[choice-1];
  currentModel = newModel;
  // Re-detect tier
  const newTier = detectTier(currentModel);
  const newCfg = TIER_CONFIG[newTier] || TIER_CONFIG.small;
  tierCfg = newCfg;
  console.log(`\x1b[32mSwitched to model: ${currentModel} (tier: ${newTier})\x1b[0m`);
}

// ---------- Save/Load with deep copy ----------
async function saveGame() {
  const saveData = {
    playerName,
    currentRoom,
    player: JSON.parse(JSON.stringify(player)), // deep copy
    visited: Array.from(visited),
    room_mechanics: currentRoomMechanics ? JSON.parse(JSON.stringify(currentRoomMechanics)) : null,
    roomCache: Array.from(roomCache.entries()),
    quests,
    lore,
    combat_active: combatActive
  };
  await fs.writeFile('dungeonclaw_save.json', JSON.stringify(saveData, null, 2));
  console.log('\x1b[32mAdventure saved!\x1b[0m');
}

async function loadGame() {
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
    combatActive = data.combat_active || false;
    // Validate current room mechanics
    if (!currentRoomMechanics) {
      console.log('\x1b[33mWarning: Saved room mechanics missing. Regenerating...\x1b[0m');
      currentRoomMechanics = await callPythonTool('generate_room', { room: currentRoom, dungeon_size: DUNGEON_SIZE, player_level: player.level });
      roomCache.set(currentRoom, currentRoomMechanics);
    }
    console.log('\x1b[32mAdventure loaded!\x1b[0m');
    return true;
  } catch {
    return false;
  }
}

// ---------- Level Up with choice ----------
async function chooseLevelUpBonus() {
  console.log(`\n${C.bold}${C.yellow}Choose your level ${player.level} bonus:${C.reset}`);
  console.log(`1. +2 Attack Bonus`);
  console.log(`2. +2 Defense Bonus`);
  console.log(`3. +4 Damage Bonus`);
  console.log(`4. +10 Max HP`);
  const answer = await rl.question('Your choice (1-4): ');
  const choice = parseInt(answer);
  switch (choice) {
    case 1: player.attack_bonus += 2; break;
    case 2: player.defense_bonus += 2; break;
    case 3: player.damage_bonus += 4; break;
    case 4: player.maxHp += 10; player.hp += 10; break;
    default: player.attack_bonus += 2; // fallback
  }
  player.stat_choices.push(choice);
}

async function checkLevelUp() {
  while (player.xp >= player.xpToNext) {
    player.level++;
    player.xp -= player.xpToNext;
    // linear XP curve: 100 + 20*(level-1)
    player.xpToNext = 100 + 20 * (player.level - 1);
    // base HP increase reduced to +10
    player.maxHp += 10;
    player.hp = player.maxHp;
    console.log(`\n\x1b[33m***** LEVEL UP! *****\x1b[0m`);
    console.log(`\x1b[32mYou are now level ${player.level}! Max HP increased to ${player.maxHp}.\x1b[0m`);
    await chooseLevelUpBonus();
    await appendHistory(`Reached level ${player.level} and gained a bonus.`);
    await updateMemory(`Reached level ${player.level}!`);
  }
}

// ---------- Apply Tool Result (updated for quests) ----------
async function applyToolResult(state, toolResult, toolName) {
  let newState = { ...state };
  if (!(newState.visited instanceof Set)) {
    newState.visited = new Set(newState.visited);
  }
  if (toolResult.new_room !== undefined) {
    newState.currentRoom = toolResult.new_room;
    newState.room = newState.currentRoom;
    if (roomCache.has(newState.currentRoom)) {
      newState.room_mechanics = roomCache.get(newState.currentRoom);
    } else {
      newState.room_mechanics = toolResult.room_mechanics;
      roomCache.set(newState.currentRoom, newState.room_mechanics);
    }
    newState.visited.add(newState.currentRoom);
    await appendHistory(`Moved to Room ${newState.currentRoom} (${newState.room_mechanics.zone})`);
  }
  if (toolResult.updated_room_mechanics) {
    newState.room_mechanics = toolResult.updated_room_mechanics;
    roomCache.set(newState.currentRoom, newState.room_mechanics);
  }
  if (toolResult.player) {
    newState.player = toolResult.player;
  } else {
    if (toolResult.damage) newState.player.hp -= toolResult.damage;
    if (toolResult.heal) newState.player.hp = Math.min(newState.player.maxHp, newState.player.hp + toolResult.heal);
    if (toolResult.gold) newState.player.gold += toolResult.gold;
    if (toolResult.xp) newState.player.xp += toolResult.xp;
    if (toolResult.loot) {
      const lootItems = Array.isArray(toolResult.loot) ? toolResult.loot : [toolResult.loot];
      newState.player.inventory.push(...lootItems);
      await appendHistory(`Found: ${lootItems.map(i => i.name).join(', ')}`);
    }
    if (toolResult.effects) newState.player.effects = toolResult.effects;
    if (toolResult.weapon) newState.player.weapon = toolResult.weapon;
    if (toolResult.armor) newState.player.armor = toolResult.armor;
  }
  if (toolResult.quests) newState.quests = toolResult.quests;
  if (toolResult.lore) newState.lore = toolResult.lore;

  // Update combat flag
  if (newState.room_mechanics?.monster && newState.room_mechanics.monster.hp > 0) {
    newState.combat_active = true;
  } else {
    newState.combat_active = false;
    if (toolName === 'attack' && toolResult.monster_defeated) {
      consecutiveBattlesNoPotion++;
    } else if (toolName === 'use' && toolResult.item_used?.includes('potion')) {
      consecutiveBattlesNoPotion = 0;
    }
  }

  // Quest updates: pass lore fragment if discovered
  let loreDiscovered = null;
  if (toolResult.lore && toolResult.lore.length) {
    loreDiscovered = toolResult.lore[0]; // simplistic: first new lore
  }
  let updatedQuests = updateQuestProgress(newState.quests, toolName, toolResult, newState.player, newState.currentRoom, toolResult.item_used, loreDiscovered);
  // Check failure conditions
  updatedQuests = checkQuestFailure(updatedQuests, newState.player, newState.currentRoom, toolResult);
  const { quests: completedQuests, player: updatedPlayer, completedNames } = checkQuestCompletion(updatedQuests, newState.player);
  newState.quests = completedQuests;
  newState.player = updatedPlayer;
  for (const qname of completedNames) {
    await appendHistory(`Completed quest: ${qname}`);
    await updateMemory(`Completed quest: ${qname}`);
    const quest = newState.quests.find(q => q.name === qname);
    if (quest) {
      const rewardStr = `${quest.reward.gold} gold, ${quest.reward.xp} XP${quest.reward.item ? ', ' + quest.reward.item.name : ''}`;
      const prompt = `You are a Dungeon Master. The player ${playerName} just completed the quest: "${qname}". Reward: ${rewardStr}. Write a triumphant 2-sentence narration. Be dramatic and celebratory.`;
      const narration = await callOllamaText(prompt, '', 0.8, 60);
      console.log(`\n\x1b[33mQuest Complete!\x1b[0m\n${narration}\n`);
    }
  }

  return newState;
}

// ---------- Build Game State ----------
function buildGameState() {
  return {
    room: currentRoom,
    currentRoom: currentRoom,
    room_mechanics: currentRoomMechanics,
    player: player,
    dungeon_size: DUNGEON_SIZE,
    combat_active: combatActive,
    quests: quests,
    lore: lore
  };
}

// ---------- Blacksmith Menu (unchanged, but uses updated crafting recipes) ----------
async function handleBlacksmith() {
  const menuResult = await safeToolCall('blacksmith_menu', {});
  if (!menuResult.success) {
    console.log(`\x1b[31m${menuResult.message}\x1b[0m`);
    return;
  }
  const menu = menuResult.menu;
  while (true) {
    console.log(`\n${C.bold}${C.yellow}Blacksmith Menu${C.reset}`);
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
    const actionResult = await safeToolCall('blacksmith_action', { action });
    if (!actionResult.success) {
      console.log(`\x1b[31m${actionResult.message}\x1b[0m`);
      continue;
    }
    if (actionResult.type === 'craft_weapon' || actionResult.type === 'craft_armor') {
      const recipes = actionResult.recipes;
      console.log(`\n${C.bold}Available recipes:${C.reset}`);
      for (let i = 0; i < recipes.length; i++) {
        const r = recipes[i];
        const mats = Object.entries(r.materials).map(([name, count]) => `${count}x ${name}`).join(', ');
        console.log(`${i+1}. ${r.name} - Cost: ${r.gold_cost} gold, Materials: ${mats} -> ${r.result.name}`);
      }
      const recipeChoice = await rl.question('Choose recipe number (or 0 to cancel): ');
      const recipeIdx = parseInt(recipeChoice) - 1;
      if (recipeIdx >= 0 && recipeIdx < recipes.length) {
        const recipe = recipes[recipeIdx];
        const craftResult = await safeToolCall('blacksmith_action', { action: 'craft_selected', recipe_name: recipe.name });
        if (craftResult.success) {
          console.log(`\x1b[32m${craftResult.message}\x1b[0m`);
          player = craftResult.player;
        } else {
          console.log(`\x1b[31m${craftResult.message}\x1b[0m`);
        }
      }
    } else if (actionResult.type === 'upgrade_artifact') {
      const artifacts = actionResult.artifacts;
      if (artifacts.length === 0) {
        console.log('No artifacts to upgrade.');
        continue;
      }
      console.log(`\n${C.bold}Artifacts:${C.reset}`);
      for (let i = 0; i < artifacts.length; i++) {
        const a = artifacts[i];
        console.log(`${i+1}. ${a.name} (upgrade level ${a.upgrade_level}, +${a.bonus})`);
      }
      const artifactChoice = await rl.question('Choose artifact number (or 0 to cancel): ');
      const artifactIdx = parseInt(artifactChoice) - 1;
      if (artifactIdx >= 0 && artifactIdx < artifacts.length) {
        const artifact = artifacts[artifactIdx];
        const upgradeResult = await safeToolCall('blacksmith_action', { action: 'upgrade_selected', artifact_name: artifact.name });
        if (upgradeResult.success) {
          console.log(`\x1b[32m${upgradeResult.message}\x1b[0m`);
          player = upgradeResult.player;
        } else {
          console.log(`\x1b[31m${upgradeResult.message}\x1b[0m`);
        }
      }
    } else if (actionResult.type === 'recycle') {
      const items = actionResult.items;
      if (items.length === 0) {
        console.log('No items to recycle.');
        continue;
      }
      console.log(`\n${C.bold}Items to recycle:${C.reset}`);
      for (let i = 0; i < items.length; i++) {
        console.log(`${i+1}. ${items[i].name} (${items[i].type})`);
      }
      const itemChoice = await rl.question('Choose item number (or 0 to cancel): ');
      const itemIdx = parseInt(itemChoice) - 1;
      if (itemIdx >= 0 && itemIdx < items.length) {
        const item = items[itemIdx];
        const recycleResult = await safeToolCall('blacksmith_action', { action: 'recycle_selected', item_name: item.name });
        if (recycleResult.success) {
          console.log(`\x1b[32m${recycleResult.message}\x1b[0m`);
          player = recycleResult.player;
        } else {
          console.log(`\x1b[31m${recycleResult.message}\x1b[0m`);
        }
      }
    }
  }
}

// ---------- Alchemist Menu ----------
async function handleAlchemist() {
  const menuResult = await safeToolCall('alchemist_menu', {});
  if (!menuResult.success) {
    console.log(`\x1b[31m${menuResult.message}\x1b[0m`);
    return;
  }
  const menu = menuResult.menu;
  while (true) {
    console.log(`\n${C.bold}${C.green}Alchemist Menu${C.reset}`);
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
    const actionResult = await safeToolCall('alchemist_action', { action });
    if (!actionResult.success) {
      console.log(`\x1b[31m${actionResult.message}\x1b[0m`);
      continue;
    }
    if (actionResult.type === 'brew_potion' || actionResult.type === 'brew_permanent') {
      const recipes = actionResult.recipes;
      console.log(`\n${C.bold}Available recipes:${C.reset}`);
      for (let i = 0; i < recipes.length; i++) {
        const r = recipes[i];
        const mats = Object.entries(r.materials).map(([name, count]) => `${count}x ${name}`).join(', ');
        console.log(`${i+1}. ${r.name} - Cost: ${r.gold_cost} gold, Materials: ${mats} -> ${r.result.name || r.result.effect}`);
      }
      const recipeChoice = await rl.question('Choose recipe number (or 0 to cancel): ');
      const recipeIdx = parseInt(recipeChoice) - 1;
      if (recipeIdx >= 0 && recipeIdx < recipes.length) {
        const recipe = recipes[recipeIdx];
        const brewResult = await safeToolCall('alchemist_action', { action: 'brew_selected', recipe_name: recipe.name, potion_type: actionResult.type === 'brew_potion' ? 'potion' : 'permanent' });
        if (brewResult.success) {
          console.log(`\x1b[32m${brewResult.message}\x1b[0m`);
          player = brewResult.player;
        } else {
          console.log(`\x1b[31m${brewResult.message}\x1b[0m`);
        }
      }
    } else if (actionResult.type === 'recycle') {
      const items = actionResult.items;
      if (items.length === 0) {
        console.log('No items to recycle.');
        continue;
      }
      console.log(`\n${C.bold}Items to recycle:${C.reset}`);
      for (let i = 0; i < items.length; i++) {
        console.log(`${i+1}. ${items[i].name} (${items[i].type})`);
      }
      const itemChoice = await rl.question('Choose item number (or 0 to cancel): ');
      const itemIdx = parseInt(itemChoice) - 1;
      if (itemIdx >= 0 && itemIdx < items.length) {
        const item = items[itemIdx];
        const recycleResult = await safeToolCall('alchemist_action', { action: 'recycle_selected', item_name: item.name });
        if (recycleResult.success) {
          console.log(`\x1b[32m${recycleResult.message}\x1b[0m`);
          player = recycleResult.player;
        } else {
          console.log(`\x1b[31m${recycleResult.message}\x1b[0m`);
        }
      }
    }
  }
}

// ---------- Direct Recycle ----------
async function handleRecycle() {
  const recycleMenu = await safeToolCall('blacksmith_action', { action: 'recycle' });
  if (!recycleMenu.success) {
    console.log(`\x1b[31m${recycleMenu.message}\x1b[0m`);
    return;
  }
  const items = recycleMenu.items;
  if (items.length === 0) {
    console.log('No items to recycle.');
    return;
  }
  console.log(`\n${C.bold}Items to recycle:${C.reset}`);
  for (let i = 0; i < items.length; i++) {
    console.log(`${i+1}. ${items[i].name} (${items[i].type})`);
  }
  const itemChoice = await rl.question('Choose item number (or 0 to cancel): ');
  const idx = parseInt(itemChoice) - 1;
  if (idx >= 0 && idx < items.length) {
    const item = items[idx];
    const recycleResult = await safeToolCall('recycle', { item_name: item.name });
    if (recycleResult.success) {
      console.log(`\x1b[32m${recycleResult.message}\x1b[0m`);
      player = recycleResult.player;
    } else {
      console.log(`\x1b[31m${recycleResult.message}\x1b[0m`);
    }
  }
}

// ---------- Rest Command (balanced) ----------
async function handleRest() {
  if (combatActive) {
    dm("You cannot rest while enemies are nearby! Fight or flee first.");
    return;
  }
  if (player.hp === player.maxHp) {
    dm("You are already at full health.");
    return;
  }
  // Only heal 40% + 2 per level
  const healAmount = Math.floor(player.maxHp * 0.4) + player.level * 2;
  const oldHp = player.hp;
  player.hp = Math.min(player.maxHp, player.hp + healAmount);
  const actualHeal = player.hp - oldHp;
  dm(`You rest and recover ${actualHeal} HP.`);

  // In mid/deep zones, chance of random encounter
  const zone = currentRoomMechanics?.zone;
  if (zone && (zone === 'mid' || zone === 'deep') && Math.random() < 0.3) {
    dm("Your rest is disturbed by a wandering monster!");
    const newMonster = await callPythonTool('generate_monster', { zone, player_level: player.level, is_minion: Math.random() < 0.2 });
    if (newMonster) {
      currentRoomMechanics.monster = newMonster;
      combatActive = true;
      console.log(`\x1b[31m⚔️ A ${newMonster.name} attacks!${C.reset}`);
    }
  }

  await updateMemory(`Rested and healed ${actualHeal} HP.`);
  await appendHistory(`Rested and healed ${actualHeal} HP.`);
  // No animation delay
}

// ---------- Main Game Loop ----------
async function gameLoop() {
  printIntro();

  // Get player name
  while (true) {
    const nameInput = await rl.question('What is your name, legendary adventurer? ');
    if (nameInput.startsWith('/')) {
      if (nameInput === '/help') console.log('Commands: /help, /inventory, /status, /quests, /lore, /save, /load, /equip, /craft, /dm, /guide, /roll, /cast, /alignment, /blacksmith, /alchemist, /recycle, quit');
      else if (nameInput === '/inventory') console.log('You have no inventory yet. Enter your name to start.');
      else if (nameInput === '/status') console.log('You have no stats yet. Enter your name to start.');
      else if (nameInput === '/quests') console.log('Quests will appear once you begin your adventure.');
      else if (nameInput === '/lore') console.log('You have not discovered any lore yet.');
      else if (nameInput === '/guide') console.log('DungeonClaw Guide: Type actions like "go north", "attack", "search", "craft Goblin Ear Potion". Use /status to see your stats. Save often with /save.');
      else if (nameInput === '/craft') console.log('Crafting recipes: Goblin Ear Potion (3 Goblin Ears), Minion Essence Potion (2 Minion Essence), Silk Cloth (2 Spider Silk + 5 gold), Orcish Elixir (1 Orc Axe + 10 gold)');
      else if (nameInput === '/dm') console.log('Use /dm once the game starts to switch models.');
      else console.log('Unknown command. Enter your name to begin.');
    } else {
      playerName = nameInput;
      break;
    }
  }

  console.log(`\nWelcome, ${playerName}.\n`);
  await readSoul();
  await writeSoul({ persona: `You are ${playerName}, a brave adventurer.`, memory: [`[${new Date().toISOString()}] You started your journey in Room 0.`], directives: '...' }, playerName);
  await appendHistory(`Started adventure as ${playerName}`);

  const loaded = await loadGame();
  if (!loaded) {
    currentRoom = 0;
    visited.add(currentRoom);
    try {
      currentRoomMechanics = await callPythonTool('generate_room', { room: currentRoom, dungeon_size: DUNGEON_SIZE, player_level: player.level });
      if (!currentRoomMechanics) throw new Error('Invalid room data');
    } catch (err) {
      console.log('\x1b[31mError generating initial room. Using default.\x1b[0m');
      await logError('error', 'python_tool', 'Initial room generation failed', { raw: err.message });
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

    // Generate story arc (if enabled)
    if (QUEST_GEN_ENABLED) {
      const arc = await callPythonTool('generate_arc', {
        player_name: playerName,
        player_level: player.level,
        zone: currentRoomMechanics.zone
      }).catch(() => null);
      if (arc && arc.hook) {
        box('YOUR ADVENTURE BEGINS', [arc.hook, '', `Theme: ${arc.theme}   Villain: ${arc.villain?.name || 'Unknown'}`], C.yellow);
        if (arc.quests?.length) {
          quests.push(...arc.quests.map(q => ({ ...q, completed: false, failed: false, started_room: currentRoom })));
        }
      }
    }
  } else {
    if (!currentRoomMechanics) {
      console.log('\x1b[31mLoaded game has no room mechanics. Generating fallback.\x1b[0m');
      try {
        currentRoomMechanics = await callPythonTool('generate_room', { room: currentRoom, dungeon_size: DUNGEON_SIZE, player_level: player.level });
      } catch {
        currentRoomMechanics = {
          room_id: currentRoom,
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
  }

  const history = [];

  // Initial look
  const initialState = buildGameState();
  const lookResult = await safeToolCall('look', {}, { description: 'You are in a dark room (fallback).' });
  const initialDesc = lookResult.description || 'You are in a dark room.';
  dm(initialDesc);
  printRoom(currentRoomMechanics);
  printStatus(player, currentRoomMechanics?.zone, currentModel);

  if (currentRoomMechanics.monster && currentRoomMechanics.monster.hp > 0) {
    combatActive = true;
    console.log(`\x1b[31m⚔️ Combat starts! ${currentRoomMechanics.monster.name} (HP: ${currentRoomMechanics.monster.hp}) attacks!\x1b[0m`);
    combatHeader(player.hp, player.maxHp, currentRoomMechanics.monster.name, currentRoomMechanics.monster.hp, currentRoomMechanics.monster.max_hp);
  }

  while (true) {
    const userInput = await rl.question('\x1b[33m> \x1b[0m');
    const lower = userInput.toLowerCase().trim();

    if (lower === 'quit' || lower === 'exit') {
      await saveGame();
      console.log('\nFarewell, legend.\n');
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
          const status = q.completed ? '✓' : (q.failed ? '✗' : '○');
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
      const helpLines = [
        `${C.bold}MOVEMENT${C.reset}`,
        '  go north/south/east/west   n s e w',
        '',
        `${C.bold}EXPLORATION${C.reset}`,
        '  look  examine  search  loot  find',
        '',
        `${C.bold}COMBAT${C.reset}`,
        '  attack  fight  hit  strike',
        '  defend  block  parry',
        '  flee [direction]  run  retreat',
        '  use <item>',
        '',
        `${C.bold}INVENTORY & GEAR${C.reset}`,
        '  inventory  bag  items',
        '  take <item>   equip <item>   use <item>',
        '  craft <recipe>',
        '',
        `${C.bold}CRAFTING NPCs${C.reset}`,
        '  /blacksmith – forge weapons/armor, upgrade artifacts, recycle',
        '  /alchemist – brew potions (incl. permanent stat boosters), recycle',
        '  /recycle – quickly recycle an item',
        '',
        `${C.bold}INFO${C.reset}`,
        '  status  stats  hp',
        '  quests  journal',
        '  lore  knowledge',
        '',
        `${C.bold}NEW FEATURES${C.reset}`,
        '  rest        – partial heal (40% + 2/level)',
        '  Quest Books – rare loot that generates custom quests via local model',
        '  Flee improved: 40% + 6% per level above monster',
        '  Minions now spawn 15% of rooms, loot chance reduced',
        '',
        `${C.bold}SYSTEM${C.reset}`,
        '  /save  /load  /dm (model switch)  /help  quit',
        '',
        `${C.gray}Tip: Spell mistakes are auto-corrected. Try "attac" → "attack"${C.reset}`,
      ];
      box('DUNGEONCLAW COMMANDS', helpLines, C.cyan);
      continue;
    }
    if (lower === '/roll') {
      const dice = userInput.substring(5).trim() || '1d20';
      const result = await safeToolCall('roll_dice', { dice }).catch(err => ({ error: err.message }));
      if (result.error) console.log(`\x1b[31mRoll error: ${result.error}\x1b[0m`);
      else {
        await animateDiceRoll(result.rolls, dice, result.total, result.modifier);
        console.log(`Result: ${result.total}`);
      }
      continue;
    }
    if (lower === '/cast') {
      const spell = userInput.substring(5).trim();
      if (!spell) console.log('Cast what? Example: /cast fireball');
      else {
        const result = await safeToolCall('cast_spell', { spell }).catch(err => ({ error: err.message }));
        if (result.error) console.log(`\x1b[31mSpell error: ${result.error}\x1b[0m`);
        else console.log(`\x1b[35m${result.message}\x1b[0m`);
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
    if (lower === 'rest' || lower === '/rest') {
      await handleRest();
      continue;
    }

    if (combatActive) {
      console.log('(Combat: you can attack, defend, use item, or flee)');
    }

    const state = buildGameState();
    const step = await runAgentStep(userInput, history, state);
    if (step.error) {
      console.log(`\x1b[31mThe agent is confused: ${step.error}. Please try again or rephrase.\x1b[0m`);
      continue;
    }

    if (step.toolName) {
      try {
        const toolResult = await safeToolCall(step.toolName, step.args);

        if (toolResult.success) {
          let newState = await applyToolResult(state, toolResult, step.toolName);
          player = newState.player;
          currentRoom = newState.currentRoom;
          currentRoomMechanics = newState.room_mechanics;
          visited = new Set(newState.visited);
          quests = newState.quests;
          lore = newState.lore;
          combatActive = newState.combat_active;
          roomCache.set(currentRoom, currentRoomMechanics);

          await checkLevelUp();

          await updateMemory(`${step.toolName}: ${toolResult.message.substring(0, 80)}`);
          await appendHistory(`${step.toolName}: ${toolResult.message.substring(0, 120)}`);

          // Animate dice if present
          if (toolResult.dice) {
            const { notation, rolls, total, modifier } = toolResult.dice;
            await animateDiceRoll(rolls, notation, total, modifier);
          }
          if (toolResult.monster_dice) {
            const { notation, rolls, total, modifier } = toolResult.monster_dice;
            await animateDiceRoll(rolls, notation, total, modifier);
          }

          let outputMessage = toolResult.message;
          if (NARRATOR_ENABLED) {
            const activeQuestHint = currentRoomMechanics?.quest_hint || '';
            const narration = await narrateResult(step.toolName, toolResult, playerName, currentRoomMechanics?.description || '', activeQuestHint);
            outputMessage = narration;
          }
          dm(outputMessage);
          printStatus(player, currentRoomMechanics?.zone, currentModel);
          if (toolResult.new_room !== undefined) {
            printRoom(currentRoomMechanics);
          }
          if (combatActive && currentRoomMechanics.monster && currentRoomMechanics.monster.hp > 0) {
            combatHeader(player.hp, player.maxHp, currentRoomMechanics.monster.name, currentRoomMechanics.monster.hp, currentRoomMechanics.monster.max_hp);
          }

          history.push({ user: userInput, agent: `[Used tool ${step.toolName}]`, summary: toolResult.message.substring(0, 80), toolName: step.toolName, timestamp: new Date().toISOString() });
          if (history.length > 5) history.shift();

          if (player.hp <= 0) {
            console.log('\x1b[31mYou have died... Game over.\x1b[0m');
            break;
          }
        } else {
          console.log(`\x1b[31mTool error: ${toolResult.error || toolResult.message}\x1b[0m`);
        }
      } catch (err) {
        await logError('error', 'python_tool', `Tool execution failed: ${err.message}`, { tool: step.toolName, room: currentRoom, playerLevel: player.level, raw: err.stack, state: JSON.stringify(state) });
        console.log(`\x1b[31mPython call failed: ${err.message}\x1b[0m`);
      }
    } else if (step.answer) {
      console.log(`\nDungeon Master: ${step.answer}\n`);
      await updateMemory(`Direct answer: ${step.answer.substring(0, 80)}`);
      await appendHistory(`Direct answer: ${step.answer.substring(0, 120)}`);
      history.push({ user: userInput, agent: step.answer, summary: step.answer.substring(0, 80), timestamp: new Date().toISOString() });
      if (history.length > 5) history.shift();
    }
  }

  rl.close();
}

gameLoop().catch(err => {
  console.error('Fatal error:', err);
  rl.close();
});
