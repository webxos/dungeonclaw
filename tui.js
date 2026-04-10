// tui.js
import * as rl from 'readline';

const W = process.stdout.columns || 80;

// ANSI escape codes
export const C = {
  reset: '\x1b[0m',
  bold:  '\x1b[1m',
  red:   '\x1b[31m',
  green: '\x1b[32m',
  yellow:'\x1b[33m',
  cyan:  '\x1b[36m',
  white: '\x1b[37m',
  gray:  '\x1b[90m',
  bg_red: '\x1b[41m',
  bg_blue:'\x1b[44m',
};

// Box drawing
export function box(title, lines, color = C.white) {
  const inner = W - 4;
  const top    = `${color}╔${'═'.repeat(inner)}╗${C.reset}`;
  const bottom = `${color}╚${'═'.repeat(inner)}╝${C.reset}`;
  const pad = (s) => {
    // Strip ANSI codes to calculate visible length
    const vis = s.replace(/\x1b\[[0-9;]*m/g, '').length;
    return `${color}║${C.reset} ${s}${' '.repeat(Math.max(0, inner - vis - 2))} ${color}║${C.reset}`;
  };
  const titleLine = pad(`${C.bold}${color} ${title} ${C.reset}`);
  console.log([top, titleLine, `${color}╠${'═'.repeat(inner)}╣${C.reset}`, ...lines.map(pad), bottom].join('\n'));
}

// Progress bar (correctly handles ANSI colors in label)
export function bar(label, current, max, width = 20, fillColor = C.green) {
  const pct  = Math.max(0, Math.min(1, current / max));
  const fill = Math.round(pct * width);
  const empty = width - fill;
  const b = `${fillColor}${'█'.repeat(fill)}${C.gray}${'░'.repeat(empty)}${C.reset}`;
  // Remove ANSI from label for alignment
  const labelVis = label.replace(/\x1b\[[0-9;]*m/g, '');
  const padLen = Math.max(0, 8 - labelVis.length);
  const paddedLabel = label + ' '.repeat(padLen);
  return `${paddedLabel} ${b} ${current}/${max}`;
}

// Dice animation (Unicode die faces)
const D20_FACES = ['⚀','⚁','⚂','⚃','⚄','⚅'];
const sleep = ms => new Promise(r => setTimeout(r, ms));

export async function animateDiceRoll(rolls, notation, total, modifier = 0) {
  const frames = 8;
  process.stdout.write('\n  ');
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
  console.log(`  ${C.bold}🎲 ${notation}${C.reset}  ${rollStr}${modStr} = ${C.bold}${C.white}${total}${C.reset}\n`);
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
  console.log('\n' + line + '\n');
}

// Dungeon Master speech
export function dm(text) {
  console.log(`${C.bold}${C.white}Dungeon Master:${C.reset} ${text}\n`);
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

// ---------- Rest Animation ----------
export async function restAnimation(seconds) {
  const total = seconds;
  const start = Date.now();
  const width = 30;
  const heart = '❤️';
  const flame = '🔥';
  const barFull = '█';
  const barEmpty = '░';

  return new Promise((resolve) => {
    const interval = setInterval(() => {
      const elapsed = (Date.now() - start) / 1000;
      const remaining = Math.max(0, total - elapsed);
      const pct = elapsed / total;
      const fill = Math.floor(pct * width);
      const empty = width - fill;

      // Build the progress bar
      const bar = `${C.green}${barFull.repeat(fill)}${C.gray}${barEmpty.repeat(empty)}${C.reset}`;
      const timer = `${Math.ceil(remaining)}s`;
      const spaces = ' '.repeat(Math.max(0, 6 - timer.length));
      const line = `${C.yellow}${heart.repeat(5)} ${C.bold}RESTORING HEALTH${C.reset} ${flame.repeat(5)}`;

      // Move cursor to top of the animation area
      process.stdout.write('\n\x1b[?25l'); // hide cursor
      process.stdout.write('\x1b[2A'); // move up two lines (adjust as needed)
      // Clear lines
      for (let i = 0; i < 3; i++) {
        process.stdout.write('\x1b[2K'); // clear line
        process.stdout.write('\x1b[1A'); // move up
      }
      process.stdout.write('\x1b[2K'); // clear current line
      console.log(line);
      console.log(`  ${bar}  ${timer} remaining`);
      console.log(C.gray + "  Breathe deeply... the dungeon quiets." + C.reset);

      if (remaining <= 0) {
        clearInterval(interval);
        process.stdout.write('\x1b[?25h'); // show cursor
        resolve();
      }
    }, 1000);
  });
}
