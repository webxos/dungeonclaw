// model_tier.js

export function detectTier(modelName) {
  const name = modelName.toLowerCase();
  // Explicit size suffixes take priority
  if (/\b(0\.5b|0\.4b|1b|tiny)\b/.test(name)) return 'tiny';
  if (/\b(1\.5b|2b|3b|4b|nano)\b/.test(name)) return 'small';   // nano → small
  if (/\b(7b|8b)\b/.test(name)) return 'medium';
  if (/\b(13b|14b|20b|30b|70b)\b/.test(name)) return 'large';
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
    questGen: true,   // changed from false
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
