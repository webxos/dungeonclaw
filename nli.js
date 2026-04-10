// nli.js – deterministic intent mapper, zero latency, plus shorthand

const INTENT_MAP = [
  // Movement – includes single letters
  {
    patterns: [
      /^go\s+(north|south|east|west)/i,
      /^move\s+(north|south|east|west)/i,
      /^exit\s+(north|south|east|west)/i,
      /^leave\s+(north|south|east|west)/i,
      /^(north|south|east|west)$/i,
      /^n$/i, /^s$/i, /^e$/i, /^w$/i,
    ],
    tool: 'move',
    extractArgs: (input) => {
      const m = input.match(/\b(north|south|east|west)\b/i);
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
    patterns: [/^take\s+(.+)/i, /^get\s+(.+)/i],
    tool: 'take',
    extractArgs: (input) => {
      const m = input.match(/^take\s+(.+)/i) || input.match(/^get\s+(.+)/i);
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
  // Defend (added)
  {
    patterns: [/^defend/i, /^block/i, /^parry/i, /^guard/i, /^d$/i],
    tool: 'defend',
    extractArgs: () => ({})
  },
  // Flee – includes single 'f'
  {
    patterns: [/^flee/i, /^run\s*(away)?$/i, /^retreat/i, /^escape/i, /^f$/i],
    tool: 'flee',
    extractArgs: (input) => {
      const m = input.match(/\b(north|south|east|west)\b/i);
      return m ? { direction: m[1].toLowerCase() } : {};
    }
  },
  // Use item
  {
    patterns: [/^use\s+(.+)/i],
    tool: 'use',
    extractArgs: (input) => {
      const m = input.match(/^use\s+(.+)/i);
      return m ? { item_name: m[1].trim() } : null;
    }
  },
  // Equip item
  {
    patterns: [/^equip\s+(.+)/i, /^wield\s+(.+)/i, /^wear\s+(.+)/i],
    tool: 'equip',
    extractArgs: (input) => {
      const m = input.match(/^(equip|wield|wear)\s+(.+)/i);
      return m ? { item_name: m[2].trim() } : null;
    }
  },
  // Craft item
  {
    patterns: [/^craft\s+(.+)/i, /^make\s+(.+)/i],
    tool: 'craft',
    extractArgs: (input) => {
      const m = input.match(/^(craft|make)\s+(.+)/i);
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
      const m = input.match(/^recycle\s+(.+)/i);
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
