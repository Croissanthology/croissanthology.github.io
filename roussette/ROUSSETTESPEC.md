# Roussette — full build specification

A Minecraft mod. Everything decided, everything still open, and why.
Written by Claude with Margot, July 2026, for whoever builds it.

> **Read section 2 first.** Several things in here are counterintuitive and were
> arrived at by throwing away a more obvious version. The reasons matter more than
> the values.

---

## 1. Target

- **Minecraft Java Edition 26.2** ("Chaos Cubed", released 16 June 2026).
  Mojang moved to year-based versioning in 2026 — there is no 1.22; the 1.21.x line
  was followed by 26.1. **26.3 is in snapshot as of late July 2026**, so check whether
  it has released before you pin anything.
- **Fabric.** Verify current Fabric API and Loom versions yourself; any numbers from
  training data for this version line are unreliable.
- Must install into an **existing world** and work immediately. This is a hard
  requirement and it drives the whole structure-placement design in section 7.

## 2. What this is, and the four rules

A small lavender catshark with cat ears — a *roussette*, the French name for the
family — that hunts one specific player relentlessly and forever. She is somebody's
older sister, rendered as a mob. Every design decision below serves these, in order:

1. **She must be cute.** Not cute-menacing. Cute, and *separately* relentless.
2. **Hitting her must be fun.** The knockback is the core loop. It should feel
   enormous and slightly ridiculous every single time, forever.
3. **She must never actually be a threat.** She bites for half a heart and refuses to
   bite below 3.5 hearts. She cannot kill. Escalation would ruin her completely.
4. **She does not speak.** Sounds only. Dialogue makes her a character commenting on
   events; noises make her a thing that is *happening to you*. This was tried the
   other way first and reverted.

### Rules that were tried and rejected

- **Escalating tolerance to repellent.** Each knockout was going to make the next one
  harder. Rejected: it punishes the player who is already being hunted, and makes his
  tools get worse over time. The victim should never be the one absorbing the
  difficulty curve.
- **Guards in the temples.** Rejected: she is the antagonist. Mobs in the shrine split
  the tension and turn the place into a generic dungeon.
- **Killing her with a sword.** She can only be killed by fire and lava. A sword
  launches her. The whole joke is that beating her up is satisfying and accomplishes
  nothing.
- **Invulnerability.** Also rejected, and this is the subtle one. Making her mortal
  made her *more* unnerving, not less — a kill he can actually land gives him a real
  victory, and then thirty ticks later there is a wet noise behind him. An invincible
  mob is a nuisance you walk past. A mortal one that keeps coming back is a
  relationship.

## 3. The creature — geometry

Units are Minecraft pixels, 16 to a block. Origin at body centre, **+X toward the
nose**, +Y up. Rotations are Euler XYZ radians about each box's own centre.
Total length 31.2px = **1.95 blocks**. Model v5, "elegant pass".

| Part | Size (x,y,z) | Position | Rotation | Colour |
|---|---|---|---|---|
| `snout` | 3.4 x 4.6 x 6 | 10.4, -0.6, 0 |  | #C3ADEB |
| `head` | 8.8 x 8.8 x 9.2 | 5.4, 0.2, 0 |  | #C3ADEB |
| `cheekL` | 2.2 x 2 x 0.6 | 8.2, -1.9, 4.6 |  | #F2A8CE |
| `cheekR` | 2.2 x 2 x 0.6 | 8.2, -1.9, -4.6 |  | #F2A8CE |
| `earL` | 2.6 x 3 x 2.6 | 4.6, 5.3, 3.1 | 0.3, 0, 0.16 | #C3ADEB |
| `earR` | 2.6 x 3 x 2.6 | 4.6, 5.3, -3.1 | -0.3, 0, 0.16 | #C3ADEB |
| `earInL` | 1.3 x 1.7 x 0.6 | 4.6, 5.5, 4.5 | 0.3, 0, 0.16 | #F2A8CE |
| `earInR` | 1.3 x 1.7 x 0.6 | 4.6, 5.5, -4.5 | -0.3, 0, 0.16 | #F2A8CE |
| `trunk` | 8.4 x 8.8 x 8.2 | -2.4, -0.2, 0 |  | #C3ADEB |
| `belly` | 8 x 4 x 7.8 | -2.4, -4.3, 0 |  | #F3ECFC |
| `rear` | 4.6 x 6 x 5.2 | -7.8, 0.2, 0 |  | #C3ADEB |
| `peduncle` | 3 x 3.6 x 2.8 | -10.8, 0.5, 0 |  | #C3ADEB |
| `dorsal` | 4.2 x 3.6 x 1 | -3.2, 5.6, 0 |  | #8E6FC4 |
| `tailUp` | 4.6 x 3 x 1 | -13.4, 3, 0 | 0, 0, 0.52 | #8E6FC4 |
| `tailLo` | 4.2 x 2.6 x 1 | -13.2, -1.6, 0 | 0, 0, -0.48 | #8E6FC4 |
| `tailMid` | 2.2 x 2 x 1 | -12.2, 0.7, 0 |  | #8E6FC4 |
| `pectL` | 3.6 x 0.9 x 4 | 1.6, -3, 4.6 | 0.46, 0, 0.14 | #8E6FC4 |
| `pectR` | 3.6 x 0.9 x 4 | 1.6, -3, -4.6 | -0.46, 0, 0.14 | #8E6FC4 |
| `whiskL` | 5 x 0.3 x 0.3 | 13, -1.6, 2 | 0, 0.3, 0.14 | #5B4383 |
| `whiskR` | 5 x 0.3 x 0.3 | 13, -1.6, -2 | 0, -0.3, 0.14 | #5B4383 |

**Face** — flat quads, deliberately untextured so the expression stays legible at
distance. Eyes at `[8.0, -0.3, 4.7]`, mirrored on ±Z. Rim 4.6px
`#6A4FA0`, iris 3.9px `#F0C64B`, pupil
`#241832`, plus a 1.2px white highlight offset up-and-forward.

**Three pupil states.** They are a *state readout*, not decoration — "she is currently
annoyed at you" must be readable across a room.

| State | Pupil | When |
|---|---|---|
| Default | round, `[2.5, 2.5]` | normal |
| Angry | slit, `[1.0, 3.1]` | on being hit; reverts after ~4s |
| Knocked out | X — two #241832 bars 4.6px across a pale `#F3ECFC` disc, ±45° | repellent, plus a pink tongue box `[1.8, 0.5, 2.4]` at `[10.2, -4.5, 0]` |

### Proportions — check these after any edit

| Ratio | Value | Valid band |
|---|---|---|
| head length / total | 0.352 | 0.32 – 0.42 |
| eye height / head height | 0.443 | 0.30 – 0.50 |
| body height / total | 0.434 | 0.42 – 0.55 |
| width / total | 0.418 | 0.34 – 0.50 |

**Lengthening her is the single most dangerous edit.** A long body reads as predatory
no matter what colour it is. These bands are neoteny ratios from character design and
the model was tuned against them numerically over four passes.

### Palette

| Role | Hex |
|---|---|
| Hide | `#C3ADEB` |
| Fins, rosettes | `#8E6FC4` |
| Belly | `#F3ECFC` |
| Cheeks, inner ear | `#F2A8CE` |
| Whiskers | `#5B4383` |
| Iris | `#F0C64B` |
| Pupil | `#241832` |

Hide texture is 32×32, **11 large rosettes, not fine speckle** — an earlier version had
~150 marks and read as static from more than a few blocks away.

Ears are not a real catshark feature. They are non-negotiable.

## 4. Behaviour — state machine

One roussette per victim. Priority order each tick, **first match wins**:

| State | Duration | Behaviour | Exits on |
|---|---|---|---|
| **Knocked out** | 200t | Belly-up, X eyes, tongue out, drifting, bubbles rising | timer |
| **Headpat** | 30t | Spins 16°/tick, heart particles, purrs twice | timer |
| **Flung** | 26t | Real velocity. Cartwheels 47°/tick. Wails at t=24/16/8. Squelches off any solid block, 7t debounce | timer |
| **Wedged** | — | Stuck in a doorframe, rotating 9°/tick, wailing once a second, completely helpless | victim >7 blocks away |
| **Latched** | 220t | Rides his feet. Slowness II. Gnaws every 24t | timer, hit, or headpat |
| **Hunt** | — | Faces him. **0.15 blocks/tick on land, 0.32 in water.** Steps over 1-block rises | — |

**That water speed is load-bearing** — it is why the temples are underwater. Descending
doubles her speed and halves his.

**Triggers**

- **Hit** — any player melee. Fling only; never lethal.
- **Headpat** — currently crouch-within-3.5-blocks, because vanilla datapacks cannot
  detect an empty-handed right-click. **In the mod, make this a real right-click, and
  keep crouch as a second path.**
- **Latch** — 1-in-3 roll within 1.9 blocks, 100t cooldown after release.
- **Wedge** — any door within ~2 blocks ahead, 200t cooldown.
- **Glow** — light level ≤6. Outline tinted **lavender**, not white.

**Reform, and do not replace this with pathfinding.** She does not travel — she
re-forms. The entire system runs anchored to the victim, so every lookup resolves in
*his* dimension. No roussette within 90 blocks means one appears behind him with a
splash and a wet squelch. **Dimension change, teleport, and death are all the same
event.** Nether, End, ender pearl, `/tp`, burning alive — one mechanism covers all of it.

**Knocked out, and the two ways to treat her.** This is the best interaction in the mod:

- **Hit her while she's down** → wakes instantly, slit eyes, +speed for 5 seconds.
- **Headpat her while she's down** → purrs without waking, and **stays down longer**.

Being cruel to a helpless thing costs you. Being kind to it buys you more of exactly
what you wanted. He will find the second one by accident.

## 5. Sound

**All recordings are Margot's own voice.** Mono OGG Vorbis. Eight events, several with
multiple takes chosen at random:

`cry` ×3 · `wail` ×2 · `purr` · `purreow` · `chomp` ×2 · `gnaw` · `squelch` ×2 · `reform`

`cry` is a short yelp on being hit. `wail` is longer and fires three times while she is
airborne. `squelch` is the wet impact against walls and the respawn noise.

## 6. Shark repellent

**The can.** 4 sprays. Each drops her for a flat **10 seconds** — long enough for
roughly 30 blocks of head start. Same every time, forever, no adaptation.

**Anvil application.** A full can + an armour piece = treated armour with **6
knockouts**. She must be within 6 blocks for a constant **45 seconds** to accumulate a
dose. When charges run out the treatment is gone and the lavender wash fades off the
armour — **the fading tint is the meter, there is no UI**. As the dose builds she
should visibly stagger and go half-lidded, so he can read her like someone about to
fall asleep.

All scarcity lives in the *supply of cans*. Never in a stat quietly degrading.

## 7. Temples

**Fiction, and it decides everything else.** These are not defences. They are
**fisher-shrines** built by people who lived alongside the roussettes and needed,
occasionally, to be left alone for ten seconds. Humble, not fortified. There is a basin
that still refills empty cans. The mosaic of her on the deepest wall is **not a ward —
it is a thank-you.** They were fond of her too.

### Placement

- **On land**, anywhere flat-ish. Not coastal — that was an earlier version.
- **Very low to the ground and hard to see from a distance.** The above-ground portion
  is a squat lip, ~2–3 blocks tall, mostly sunk, easy to walk past.
- **Roughly one per biome**, well spaced (suggest ≥1500 blocks minimum separation).
- Randomly placed and randomly seeded, not identical copies.

### Interior

A single main room containing **a very deep pool**: 33 blocks from the water's surface
to the floor. Walls of the shaft are **unbreakable** — see the gotcha in section 9.

- **Three rest alcoves**, alternating sides, each behind a **copper door**. Doors are
  not waterloggable, so they hold the water out with no redstone at all.
- **The alcoves defend themselves.** She wedges in doorframes. He swims in gasping, she
  follows, and gets stuck in the doorway going *bleh* while he catches his breath four
  blocks away. This was not designed — it fell out of two unrelated features and it is
  the best thing in the building. Preserve it.
- **The light turns lavender as you descend.** Sea lanterns at the top; amethyst
  clusters thicken with depth until the bottom is lit almost entirely in her colour.
- **The bottom chamber** holds a copper chest with **1–2 cans**, votive cans in item
  frames on the walls (so a looted shrine stays visibly, sadly empty), and **the 29×13
  block mosaic of her** filling the deepest wall — the last thing he sees before the
  chest, with his air bar nearly out.
- **Exit:** a soul sand bubble column in one corner. Once he has paid for it, the
  shrine lets him leave fast.

### Trap — rupture, not explosion

Mining the wrong block does not hurt him. **The pressurised cans burst.** He loses what
he came for, the chamber fills with lavender fog, and *she* goes down if she is nearby.
A botched raid costs the prize and hands him ten seconds of accidental peace. Do not
make this lethal; he is 33 blocks from air.

### Cross-section

Authored as a block grid. `R` unbreakable shrine stone, `C` copper, `~` water,
`a` air pocket, `D` copper door, `A` amethyst, `S` sea lantern, `M` mosaic,
`F` item frame + can, `H` chest, `B` bedrock. **Note the above-ground portion in this
sketch is still the old tall version — flatten it per the placement rules above.**

```
                                 
                                 
                                 
                                 
                                 
                                 
        CCCCCCCCCCCCCCCCC        
        CS             SC        
        C               C        
        C               C        
                        C        
          F           F C        
        C###~~~~~~~~~###C        
gggggggggggR~~~~~~~~~Rggggggggggg
sssssssssssR~~~~~~~~~Rsssssssssss
sssssssssssR~~~~~~~~~Rsssssssssss
sssssssssssR~~~~~~~~~Rsssssssssss
sssssssssssR~~~~~~~~~Rsssssssssss
sssssssRRRRR~~~~~~~~~Rsssssssssss
ssssssRSaaaDA~~~~~~~~Rsssssssssss
ssssssRaaaaD~~~~~~~~~Rsssssssssss
ssssssRaaaaR~~~~~~~~ARsssssssssss
sssssssRRRRRA~~~~~~~~Rsssssssssss
sssssssssssR~~~~~~~~~Rsssssssssss
sssssssssssR~~~~~~~~~Rsssssssssss
sssssssssssR~~~~~~~~~Rsssssssssss
sssssssssssR~~~~~~~~ARsssssssssss
sssssssssssRA~~~~~~~~RRRRRsssssss
sssssssssssR~~~~~~~~~DaaaSRssssss
sssssssssssR~~~~~~~~ADaaaaRssssss
sssssssssssRA~~~~~~~~RaaaaRssssss
sssssssssssR~~~~~~~~~RRRRRsssssss
sssssssssssRA~~~~~~~~Rsssssssssss
sssssssssssRA~~~~~~~~Rsssssssssss
sssssssssssR~~~~~~~~ARsssssssssss
sssssssssssRA~~~~~~~~Rsssssssssss
sssssssRRRRR~~~~~~~~~Rsssssssssss
ssssssRSaaaD~~~~~~~~ARsssssssssss
ssssssRaaaaDA~~~~~~~~Rsssssssssss
ssssssRaaaaR~~~~~~~~ARsssssssssss
sssssssRRRRRRRRRRRRRRRRRsssssssss
sssssssssR~~~~~~~~~~~~~Rsssssssss
sssssssssRMMMMMMMMMMMMMRsssssssss
sssssssssR~~~~~~~~~~~~~Rsssssssss
sssssssssR~~F~~~H~~~F~~Rsssssssss
sssssssssRS~~~~~~~~~~~SRsssssssss
sssssssssBBBBBBBBBBBBBBBsssssssss
sssssssssssssssssssssssssssssssss
sssssssssssssssssssssssssssssssss
sssssssssssssssssssssssssssssssss
```

## 8. The `/roussette-temples` command

**The hard part of this whole mod.** Structures normally only generate in new chunks,
and this must work in a world that already exists.

- Runs **once, ever**. Persist the flag in world save data. Subsequent invocations
  refuse with a message.
- On invocation: search outward from world spawn for candidate sites — surface height
  variance under a threshold, one per biome, minimum separation enforced.
- Chunks must be force-loaded to be written to. **Do this incrementally across ticks**;
  placing dozens of 33-deep structures synchronously will hang the server.
- Report progress in chat, and report where they went, or he will never find them.
- Terrain below the site gets carved for the shaft. That is fine — you are placing
  blocks directly, not asking worldgen for anything.

## 9. Gotchas, corrections, and things that bit us

- **Reinforced deepslate is not unbreakable.** 55 hardness, no associated tool, breaks
  in about a minute and drops nothing, and cannot be obtained in Survival at all.
  I claimed twice that it was unbreakable and craftable; both were wrong.
  **The mod should register its own shrine block with bedrock-like hardness.**
- **Minecraft has no pale lavender block.** The mosaic uses purpur (144), amethyst (42),
  calcite (16), yellow/purple/black/white concrete and pink concrete. She reads slightly
  more saturated in blocks than she does in her real palette. Unavoidable.
- **Fish take drying damage on land.** In the datapack this killed her every 40 seconds
  and was patched by topping her health up unless she is on fire. In a real mod, just
  don't give her the drying behaviour.
- **Doors are not waterloggable**, which is why the alcoves work.
- **Vanilla cannot detect empty-handed right-clicks on an entity.** The mod can. Fix the
  headpat.

## 10. Reference implementation

A working **datapack** (38 functions) and **resource pack** exist and implement
everything in sections 4–6 against a retextured vanilla cod. Treat them as executable
documentation of the behaviour — the timings and feel are already tuned. The mod
replaces the body, not the brain.

Functions:

- `catshark:bonk`
- `catshark:chomp`
- `catshark:deploy`
- `catshark:dismiss`
- `catshark:door_open`
- `catshark:fly_tick`
- `catshark:glow`
- `catshark:gnaw`
- `catshark:headpat`
- `catshark:help`
- `catshark:hunt`
- `catshark:init`
- `catshark:latch_start`
- `catshark:latch_tick`
- `catshark:launch`
- `catshark:load`
- `catshark:on_hit`
- `catshark:pat_start`
- `catshark:pat_tick`
- `catshark:reel_in`
- `catshark:reform`
- `catshark:shark`
- `catshark:tick`
- `catshark:truce`
- `catshark:victim`
- `catshark:voice/chomp`
- `catshark:voice/cry`
- `catshark:voice/gnaw`
- `catshark:voice/purr`
- `catshark:voice/purreow`
- `catshark:voice/reform`
- `catshark:voice/squelch`
- `catshark:voice/wail`
- `catshark:wedge_enter`
- `catshark:wedge_free`
- `catshark:wedge_scan`
- `catshark:wedge_seek`
- `catshark:wedge_tick`

## 11. Still open

- Should there be a **befriending arc** — a headpat counter that eventually flips her
  to guarding him and attacking mobs near him? It would give the repellent a moral
  alternative and make the temples mean something. Undecided, and Margot should decide.
- Whether shrines respawn cans over time, or are finite forever.
- Whether she should be nocturnal, like a real swellshark.
