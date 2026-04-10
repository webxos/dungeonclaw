#!/usr/bin/env python3
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
