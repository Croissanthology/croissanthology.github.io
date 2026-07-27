# Roussette — decisions log

Things settled after the spec was written. The spec (`ROUSSETTESPEC.md`) is still
the design document; this file is where it has been overruled or filled in.
Where the two disagree, **this file wins**.

---

## Loader: NeoForge, not Fabric, and not legacy Forge

Margot said "we're using Forge". In 2026 that means **NeoForge** — legacy
Minecraft Forge (LexManos) only maintains old version lines now, and does not
support 26.2 at all, so it was never actually an option for a current LAN world.
NeoForge shipped 26.2 support on 3 July 2026.

**We are not switching to Fabric**, even though the spec was written against it,
because switching loaders means everyone reinstalls their client for no benefit.
The benefit would have been small anyway: `core/` has no Minecraft imports, so
the loader choice only affects the thin adapter layer, not the brain, the
repellent maths, the temple placement, or the model.

Target: **Minecraft Java 26.2 + NeoForge**. 26.3 is still in snapshot (Snapshot 5,
21 July) and is expected around September — do not chase it mid-project.

## Four corrections from Margot

1. **She can be defeated by a player, and she respawns.**
   Overrules spec §2, which had rejected sword-killing and restricted her death
   to fire and lava. Any damage now works.

   This collides with rule 2 (the fling is the core loop and must stay fun
   *forever*) — if she dies in two hits, nobody gets to punt her. Resolved by
   giving her **`MAX_HEALTH = 30` half-hearts (15 hearts)**: casual whacking just
   launches her, and actually killing her is a deliberate project that buys about
   ten seconds of peace. Death is now simply a very long fling, and routes
   through the existing reform mechanism — `onDefeated` then `onReform` after
   `REFORM_DELAY` ticks.

2. **She does not fight mobs and does not attract them.**
   No attack goals, no targeting, and no mob aggro toward her. This also settles
   half of spec §11's open "befriending arc" question: even a befriended
   roussette would not become a bodyguard, because she does not fight.

3. **She hunts the brother only. The cousin is never a target.**
   Already implied by the spec's one-roussette-per-victim design, now explicit.
   Needs a victim registry that survives restarts, and a hard guarantee no other
   player can be selected by accident.

4. **It has to be genuinely funny.**
   The fling was under-built: the old code only played a wet noise on wall
   contact. She now **ricochets** — real velocity reflection, decaying per
   impact, with the carom buying her extra airtime. See below.

## Answers to the three open questions

**Does she speak? — No. Sounds only, rule 4 stands.**
"EEEP! Ok. Ok. anyway." is rendered entirely as audio: `eep` on the first
ricochet, then `huff` when she lands and resumes hunting. No text, no chat
messages, no floating labels. There is a test (`she never says a word of it out
loud`) asserting every sound she emits is one of the recorded takes, so a line of
dialogue cannot leak in later by accident.

**How tough? — 15 hearts.** See correction 1.

**The cousin gets full bystander powers.** She cannot be hunted, but she can
headpat, spray repellent to rescue her cousin, and punt the shark for fun. The
brain needed no change for this: `onHit`, `onHeadpat` and `onRepellent` never
knew who was calling them, so bystander interaction works through the same
entry points. Only the adapter has to not care who swung.

## Sound list — now ten events, up from eight

`cry` ×3 · `wail` ×2 · `purr` · `purreow` · `chomp` ×2 · `gnaw` · `squelch` ×2 ·
`reform` · **`eep`** · **`huff`**

The two new ones are Margot's "EEEP!" and the little composure-regaining noise
after it. All are still her own voice, mono OGG Vorbis.

---

## Round two

### The victim rule, and the one-T problem

Margot's rule: *"any username with the string roussette, that's the enemy."*
Her brother's username is **`I_eat_roussetes`** — **one T**.

`"I_eat_roussetes".contains("roussette")` is **false**. Implemented literally,
the stated rule would have hunted nobody at all, and the mod would have shipped
looking like it worked. He misspelled his own provocation.

The trigger is therefore the stem **`rousset`**, which catches `roussetes`,
`roussette`, `roussettes` and every other near-miss. Case-insensitive.

**Protection outranks the stem.** A protected player is never hunted no matter
what they are called, so rule 3 ("she is never actually a threat") is never one
typo away from failing. The cousin is protected explicitly rather than by
absence, and bystanders keep full hit/pat/spray powers either way.

### A can holds 10 sprays — and that moved the anvil recipe

`SPRAYS_PER_CAN` 4 → **10**, as asked.

This quietly broke the anvil upgrade. At 4 sprays, trading a whole can for 6
armour knockouts was an obvious win; at 10 sprays it becomes a *downgrade* —
burning ten escapes to buy six — so nobody would ever use the recipe again.
`ARMOUR_CHARGES` is therefore 6 → **15**, preserving the original 1.5× shape of
the trade. Flagging it because it is a derived decision, not one Margot made: if
she wants treated armour to be a sidegrade rather than an upgrade, this is the
number to change.

### Fleeing through dimensions — already specced, now tested

Yes, this was in the spec (§4, "Reform, and do not replace this with
pathfinding") and in the ported brain. It is now covered by tests: past the
64-block leash she does not path toward him, she **re-forms on him** with the
`reform` splat. The Nether, the End, an ender pearl, `/tp`, and dying are all
literally the same code path. Confirmed working at the brain level.

### The temple

- **Walls:** the mod's own `roussette:shrine_stone` at bedrock hardness. Not
  reinforced deepslate — spec §9 established it is not unbreakable (55 hardness,
  breaks in about a minute, drops nothing, unobtainable in survival), so
  doubling it up would not have helped.
- **One per biome, ≥1500 blocks apart**, already enforced by `SiteFinder`.
- **Depth:** the shaft bottoms out 34 blocks below the surface, with the item
  chest at the bottom. Confirmed by test.
- **3D:** the cross-section is a schematic, extruded 13 blocks along Z. Three
  things had to be special-cased or the building came out wrong: the extruded
  **ends need capping** (otherwise the pool drains into raw terrain on two
  sides), **fittings must not repeat** (a naive extrude gives thirteen chests
  and thirty-nine doors), and the **mosaic is a wall, not a stripe**.
- **Placement is incremental**, 512 blocks per tick, one chunk per batch so
  exactly one chunk is force-loaded at a time, and the run-once flag survives a
  restart.

### Open: the mosaic does not fit

Spec §7 wants a **29×13** mosaic (377 blocks) filling the deepest wall. The
bottom chamber in the cross-section has an interior of **13 wide × 5 tall** — 65
blocks. A 29-wide mosaic cannot go in a 13-wide room.

Currently built at the largest size that fits (13 × 5). To get the specced
mosaic the bottom chamber has to grow to at least 29 × 13, which is a much
bigger room and changes how the descent feels at the end. **Margot's call.**

## Still needed from Margot

- **The ten sound recordings.** Nothing else can substitute — her voice is the
  whole point, and this is the one part of the mod that cannot be written.
- **Minecraft usernames** for her brother (the victim) and her cousin (protected),
  so the victim registry can be seeded rather than guessed.
- **The datapack and resource pack** from spec §10, if they still exist. Not
  blocking — `core/` already ports the brain and the timings — but they are the
  tuned reference for feel.

## Still open, inherited from spec §11

- Whether shrines refill cans over time or are finite forever.
- Whether she is nocturnal, like a real swellshark.
- The befriending arc, now narrowed: since she does not fight mobs, a headpat
  counter could at most change *her* behaviour toward the victim, not turn her
  into a guard.
