// fuzzy.js – Levenshtein-based command spell checker

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
  'blacksmith','alchemist','recycle','forge','brew','upgrade'
];

function levenshtein(a, b) {
  const m = a.length, n = b.length;
  const dp = Array.from({length: m+1}, (_,i) => Array.from({length: n+1}, (_,j) => i===0?j:j===0?i:0));
  for (let i=1;i<=m;i++) for (let j=1;j<=n;j++)
    dp[i][j] = a[i-1]===b[j-1] ? dp[i-1][j-1] : 1+Math.min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1]);
  return dp[m][n];
}

export function spellCorrectTokens(input) {
  const tokens = input.trim().toLowerCase().split(/\s+/);
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
