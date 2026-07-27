# Roussette — what the mod actually does

Concrete and literal. Every number here is the number in the code, not a
paraphrase of the spec. 20 ticks = 1 second. Damage is in half-hearts.

Target: **Minecraft Java 26.2 + NeoForge**.

---

## 1. Her

A lavender catshark with cat ears, **1.95 blocks long**, built from **20 boxes**.
Hide `#C3ADEB`, fins `#8E6FC4`, belly `#F3ECFC`, cheeks and inner ears `#F2A8CE`,
whiskers `#5B4383`, iris `#F0C64B`, pupil `#241832`.

**8 hearts** (`MAX_HEALTH = 16` half-hearts).

Her eyes are a status readout, readable across a room:

| Pupil | Shape | Means |
|---|---|---|
| Round | 2.5 × 2.5 px | normal |
| Slit | 1.0 × 3.1 px | she has just been hit — reverts after **4 seconds** |
| X | two bars at ±45° on a pale disc, tongue out | knocked out |
| Shut | a soft dark arc with a lash tick | asleep beside his bed |

She **glows** — lavender outline — whenever the light level is **6 or below**.

She **does not speak**. Ever. There is a test enforcing it.

She **does not fight mobs and does not attract them.** No attack goals, no
targeting in either direction.

## 2. Who she hunts

**Exactly one player at a time.**

- Any username containing the stem **`rousset`** (case-insensitive) adopts itself
  as her target — but only if she currently has none.
- `/new-target <name>` moves her onto somebody else deliberately. She forgets the
  previous victim completely.
- **Protected players can never be targeted**, by taunt or by command. Protecting
  the current victim calls her off retroactively, that instant.
- Protected players and everyone else keep **full bystander powers**: they can
  hit her, headpat her, and spray her. They simply cannot be prey.

## 3. What she does every tick

First match wins, top to bottom.

### Knocked out — 200 ticks (10 s)
Belly-up, X eyes, tongue out. Rotates 2°/tick, emits 3 bubbles every second.
Wakes on the timer.

### Headpat — 30 ticks (1.5 s)
Spins 16°/tick, hearts every tick, `purreow` at t=20, `purr` at t=8.

### Flung — 26 ticks (1.3 s), extendable
Real velocity. Cartwheels 47°/tick. Wails at t=24, 16, 8.

On hitting a wall (7-tick debounce between impacts):
- **Bounces** — velocity reflected, keeping **82%** of speed on the first carom,
  **13% less** each time after, floor **30%**.
- First carom plays **`eep`**; later ones play `squelch`.
- Each carom **adds 8 ticks of airtime**, up to **4 caroms**, then she runs out
  of bounce and settles instead of pinballing forever.

When it ends she plays **`huff`** — the "Ok. Ok. anyway." — and resumes hunting.

### Asleep beside his bed — no timer
He got into a bed, so she stopped hunting, teleported to his pillow and flumped
over on her side with her eyes shut. **Snores every 3.5 seconds**, and roughly
one in four is a snort instead. She does not bite, does not move, and does not
leave. Ends when he wakes up, with a huff and round eyes — hunting again.

Punting her off the bed works and is encouraged; she flumps straight back down
because he is still asleep. Patting her purrs without waking her, mirroring the
knocked-out rule. Repellent outranks bedtime — she can be unconscious *instead*
of asleep.

She is a `Mob`, not a `Monster`, so vanilla's "you may not rest, there are
monsters nearby" check does not see her. He can get into bed with a shark two
feet away and the game will allow it.

### Wedged in a doorway — no timer
Rotates 9°/tick, wails once a second, completely helpless. Frees herself only
when the victim is **more than 7 blocks away**, then a 200-tick cooldown.

### Latched — 220 ticks (11 s)
Rides his feet. **Slowness II.** Gnaws every 24 ticks, dealing **half a heart** —
but **never below 3.5 hearts**. Below that she still makes the noise and deals
nothing. Ends on the timer, on being hit, or on a headpat.

### Hunting — the default
Faces him, levels her pitch, and closes:

- **0.15 blocks/tick on land**, **0.32 in water.** Water more than doubles her
  speed and halves his. This is why the temples are underwater.
- **×1.6 speed** for 5 seconds if she was woken up angry.
- Steps over 1-block rises.
- Stops closing at **1.4 blocks**.
- Bites every 24 ticks within 2.5 blocks, half a heart, same 3.5-heart floor.
- **1-in-3 chance** to latch within 1.9 blocks, then a 100-tick cooldown.
- Wedges herself in any door within ~2 blocks ahead. She cannot help it.
- **Past 64 blocks she teleports to him** — see below.

## 4. Fleeing does not work

Past the **64-block leash** she does not pathfind. She **re-forms on him**, with
the `reform` splat.

**The Nether, the End, an ender pearl, `/tp`, and dying are all the same code
path.** There is one mechanism, anchored to the victim, so every lookup resolves
in whatever dimension he is currently in. There is no travel to intercept, no
route to block, and no distance that helps.

## 5. Being defeated

Any damage works. At zero health she plays `wail`, throws 40 particles, and
vanishes — then **re-forms 30 ticks (1.5 s) later** with round eyes and no grudge.

Eight hearts: enough that a casual whack launches her rather than killing her,
so the fling stays the core loop, but low enough that killing her is a normal
thing to do rather than a project. That works precisely because the return is so
fast — a kill was never going to buy much peace anyway. Death is a long fling.

## 6. Shark repellent

**The can — 10 sprays.** Each spray drops her for a flat **10 seconds**, about 30
blocks of head start. Identical every time, forever. **There is no tolerance
mechanic** and there never will be — the victim is not the one who absorbs a
difficulty curve.

**Cans do not refill.** There is no basin. Once empty, empty.

**Anvil recipe.** A full can + an armour piece = treated armour with **6
knockouts**. A deliberate sidegrade: you trade 10 manual escapes for 6 automatic
ones, buying not having to react in time.

To land one automatic knockout she must be within **6 blocks for a continuous 45
seconds**. Back away and the dose decays. As it builds she visibly staggers and
goes half-lidded, so he can read her like someone about to fall asleep.

**The fading lavender tint on the armour is the meter. There is no UI.**

### Knocked out: the two ways to treat her

- **Hit her while she's down** → wakes instantly, slit eyes, **×1.6 speed for 5
  seconds.** Being cruel to a helpless thing costs you.
- **Headpat her while she's down** → purrs, **stays down 3 seconds longer**, does
  not wake. Being kind buys you more of exactly what you wanted.

He will find the second one by accident.

## 7. The temples

**Overworld only. One per biome, at least 1500 blocks apart.**

Sites are chosen by spiralling outward from world spawn on a 96-block grid,
requiring ground flat to within **2 blocks** across a 15×15 patch and at least
**40 blocks** of rock beneath for the shaft.

**Above ground:** a squat lip, no more than 8 blocks tall, mostly sunk. Easy to
walk straight past.

**Below:** a single very deep pool, **34 blocks** from the surface to the floor,
shaft walls of `roussette:shrine_stone` — the mod's own block, at bedrock
hardness. *Not* reinforced deepslate, which is breakable in about a minute and
unobtainable in survival.

**Three rest alcoves** behind **copper doors**, alternating sides. Doors are not
waterloggable, so they hold the water out with no redstone.

**The alcoves defend themselves.** He swims in gasping; she follows and wedges
in the doorway going *bleh* while he catches his breath four blocks away. Nobody
designed this — it falls out of two unrelated features.

**The light turns lavender as you descend.** Sea lanterns at the top, amethyst
thickening with depth until the bottom is lit almost entirely in her colour.

**At the bottom:** a copper chest with **exactly one can**, votive cans in item
frames (so a looted shrine stays visibly, sadly empty), and **a painting of her**
on the deepest wall — the last thing he sees before the chest, with his air bar
nearly gone.

**Exit:** a soul sand bubble column in one corner. Once he has paid for it, the
shrine lets him leave fast.

**The trap is a rupture, not an explosion.** Mining the wrong block bursts the
pressurised cans: he loses what he came for, the chamber fills with lavender fog,
and *she* goes down if she is nearby. A botched raid costs the prize and hands
him ten seconds of accidental peace. It is never lethal — he is 34 blocks from
air.

These are not defences. They are fisher-shrines, built by people who lived
alongside the roussettes and needed, occasionally, to be left alone for ten
seconds. The painting is not a ward. It is a thank-you. They were fond of her too.

## 8. Commands

### `/roussette-temples`
Builds every temple in the world. **Runs once per world, ever.**

- The latch flips **before the first block is written**, so three players typing
  it in the same second produce one set of temples, not three carved through each
  other.
- Refused mid-run with *"The temples are being built right now. Wait."*
- Refused afterwards with *"The temples have already been built in this world."*
- A run interrupted by a crash stays refused — deliberately, so a half-built
  temple can never be built over.
- Survives server restarts.
- Writes **512 blocks per tick**, one chunk force-loaded at a time, reporting
  progress and final locations in chat. It will not hang the server.

### `/new-target <name>`
Moves her onto a new victim. Refuses protected players.

## 9. Sounds

**Margot records these — 10 events, 16 takes, her voice:**
`cry` ×3 · `wail` ×2 · `purr` · `purreow` · `chomp` ×2 · `gnaw` · `eep` · `huff` ·
`snore` ×2 · `snort` ×2

**Sourced, not performed — vanilla sound events, no files needed:**
`squelch` (wall impacts, wedging free) · `reform` (rematerialising)

## 10. Build status

**Written and tested — 120 assertions, no Minecraft required:**

| Module | What it covers |
|---|---|
| `Roussette` | the entire state machine and every tuned constant |
| `Repellent` | cans, doses, treated armour, no-tolerance guarantee |
| `VictimRegistry` | targeting, `/new-target`, protection |
| `SiteFinder` | biome spread, spacing, flatness, depth |
| `Blueprint` | the cross-section, and its extrusion into a real 3D building |
| `TempleBuilder` | world mapping, chunk batching, the run-once latch |
| `Geometry` | the 20 boxes and the neoteny proportion bands |

**Written but never compiled — the Minecraft-facing half, in `mod/`:**

the entity (implementing `Sensors`/`Actuators`) · model, renderer and textures ·
the repellent can and its anvil recipe · `roussette:shrine_stone` · her painting
· sound registration · all three commands · world save data · the temple runner
with force-loading and per-tick block writes

The authoring environment blocked `maven.neoforged.net`, so NeoForge could not be
downloaded and this half has never seen a compiler. Expect the first build to
fail; every unverified API call is tagged `// VERIFY:`. See
[`mod/README-INSTALL.md`](mod/README-INSTALL.md) for the ranked list of where to
look.
