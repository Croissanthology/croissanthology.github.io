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
   giving her a real health pool — **`MAX_HEALTH = 16` half-hearts (8 hearts)**,
   revised down from 15 hearts once it was clear how fast she returns. Casual whacking just
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

**How tough? — 8 hearts.** Originally 15; revised down by Margot, because she
respawns a second and a half later and a long fight for a one-second reward is
just tedious. See correction 1.

**The cousin gets full bystander powers.** He cannot be hunted, but he can
headpat, spray repellent to rescue the victim, and punt the shark for fun. The
brain needed no change for this: `onHit`, `onHeadpat` and `onRepellent` never
knew who was calling them, so bystander interaction works through the same
entry points. Only the adapter has to not care who swung.

## Sound list — split by who makes it

The spec said "all recordings are Margot's own voice", which is right for the
*vocal* half and impossible for the rest. Nobody can perform a wet impact against
a wall. So the twelve events split in two.

**Margot records these — her voice, mono OGG Vorbis.** This is the half that
cannot be substituted; it is the whole reason the mob is her and not a fish.

| Event | Takes | When |
|---|---|---|
| `cry` | ×3 | short yelp on being hit |
| `wail` | ×2 | longer; three times while airborne, and on being defeated |
| `purr` | ×1 | headpat, and patted while knocked out |
| `purreow` | ×1 | mid-headpat |
| `chomp` | ×2 | a bite lands |
| `gnaw` | ×1 | latched, every 24 ticks |
| `eep` | ×1 | **new** — the first ricochet |
| `huff` | ×1 | **new** — "Ok. Ok. anyway.", on landing |
| `snore` | ×2 | **new** — loops all night while he sleeps |
| `snort` | ×2 | **new** — punctuates the snoring, ~1 in 4 |

**Sourced, not performed.** Vanilla sound events referenced by ID need no files
at all, which is the cheapest possible answer:

| Event | When | Candidate |
|---|---|---|
| `squelch` | wall impacts, wedging free | `entity.slime.squish` / `entity.slime.jump` |
| `reform` | she rematerialises behind him | `entity.generic.splash` layered with a slime squish |

Exact vanilla IDs must be verified against the 26.2 sound registry rather than
trusted from memory. If the vanilla slime noises turn out too comedic-soft, these
two are also the easiest to swap for free library recordings later — they are the
only events in the mod with no attachment to a specific performance.

---

## Round two

### The victim rule

Margot's rule: *"any username with the string roussette, that's the enemy."* Her
brother's username is **`I_eat_roussettes`**.

The trigger is the stem **`rousset`** rather than the full word, case-insensitive.
This came out of a false alarm — the username was briefly transcribed here with
one T, which the literal rule would not have matched — and the stem was kept
afterwards deliberately. Spelling `roussette` correctly is evidently not
something to rely on, including from the people writing the mod, and the stem
costs nothing.

**Protection outranks the stem.** A protected player can never become the target,
by taunt or by command, so rule 3 ("she is never actually a threat") is never one
typo or one mistyped command away from failing. The cousin is protected
explicitly rather than by absence, and bystanders keep full hit/pat/spray powers
either way.

### `/new-target <name>` — she outlives her victims

The brother goes home tomorrow night; the shark does not retire. She hunts
**exactly one player at a time**, per spec §4's "one roussette per victim":

- A taunting username adopts itself as the target, but **only if she has none** —
  an existing victim is never silently swapped out from under her.
- `/new-target <name>` moves her on deliberately, and she forgets the old victim.
- It **refuses protected players**, and changes nothing on refusal.
- Protecting the current victim calls her off immediately and retroactively.

### Scarcity: one can per temple, no refills, Overworld only

- `SPRAYS_PER_CAN` 4 → **10**.
- **One can per temple**, in the chest at the bottom. That is it.
- **The basin is gone.** Cans do not refill, ever. `Can.refill()` is deleted
  rather than deprecated, so nothing can call it by accident.
- **Temples are Overworld-only.**

The world therefore contains a fixed, small, permanently shrinking supply of
escapes, which is the point: he is meant to run out.

This forced the anvil recipe back down. `ARMOUR_CHARGES` had been raised to 15 to
keep a 10-spray can worth converting, but that only made sense while cans
refilled. With a fixed supply, a recipe that turns 10 sprays into 15 knockouts
manufactures escapes out of nothing and undoes the scarcity. It is back to
**6** — a genuine sidegrade: fewer total uses, bought with not having to react in
time. Flagging it as a derived decision, not one Margot made.

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
- **Overworld only**, and **one can** in the bottom chest.
- **3D:** the cross-section is a schematic, extruded 13 blocks along Z. Two
  things had to be special-cased or the building came out wrong: the extruded
  **ends need capping** (otherwise the pool drains into raw terrain on two
  sides), and **fittings must not repeat** (a naive extrude gives thirteen
  chests and thirty-nine doors).
- **Placement is incremental**, 512 blocks per tick, one chunk per batch so
  exactly one chunk is force-loaded at a time.

### She is a painting, not a mosaic — problem deleted

Spec §7 wanted a **29×13 block mosaic** on the deepest wall. It did not fit: the
bottom chamber's interior is **13 wide × 5 tall**. The options were to grow the
room substantially or shrink her.

Margot's answer was better than either — *it was always meant to be a painting.*
So `M` is now a single painting anchor on the back wall. This deletes the sizing
problem outright, drops ~65 block placements, and removes the §9 complaint that
she reads more saturated in blocks than in her real palette: a painting can use
`#C3ADEB` exactly. The temple no longer needs a `mosaic_marker` block at all.

### The command runs once per *world*, not once per player

- The latch flips to `RUNNING` **before the first block is written**, not after
  the last. Three players typing the command in the same second produce one set
  of temples, not three overlapping sets carved through each other.
- A second invocation mid-run is refused with a different message than one after
  completion, so the player can tell "wait" from "too late".
- A run interrupted by a crash stays `RUNNING` and stays refused. Deliberate: the
  alternative is letting a half-built temple be built over.
- Persisted in world save data, so a restart does not reopen the door.

### Bedtime

When he gets into a bed she stops hunting, teleports to his pillow, flumps over
on her side with her eyes shut, and snores until dawn.

This is the only state she enters **voluntarily**, and the only one where she is
harmless on purpose rather than by accident. It does not soften her and it is not
a truce: she is on his pillow, and she is awake again at first light.

Mechanically it falls out of the existing structure almost for free — a new state
between KO and the rest, a fourth pupil (`CLOSED`), and one new actuator
(`flumpBeside`). Three details worth keeping:

- **Repellent outranks bedtime.** Being knocked out is unconsciousness, not
  sleep; she gets X eyes, not shut ones.
- **She can be punted off the bed**, and flumps straight back down, because the
  sleep check re-fires the moment the fling ends. Nobody wrote that; it fell out
  of the state priority.
- **Patting her purrs without waking her**, exactly like patting her while she is
  knocked out. The two kindness rules now rhyme.

She is registered as a `Mob`, not a `Monster`, so vanilla's "you may not rest,
there are monsters nearby" check ignores her. Without that she would make the bed
unusable and the whole feature would be impossible.

**Two new sounds:** `snore` ×2 and `snort` ×2, bringing Margot's recording list
to 16 takes across 10 events. The snore loops every 3.5 seconds all night, so it
is the sound he will hear more than any other in the mod.

## Still needed from Margot

- **The ten vocal recordings** in the table above (sixteen takes). Her voice is
  the whole point and it is the one part of the mod that cannot be written. The
  wet noises are no longer on her list.
- **The cousin's username**, so he can be protected explicitly. The brother's is
  `I_eat_roussettes`.
- **The painting art**, at some point — now that she is a painting rather than a
  block mosaic it can be drawn at her true palette instead of approximated in
  concrete. Not blocking; a placeholder works.
- **The datapack and resource pack** from spec §10, if they still exist. Not
  blocking — `core/` already ports the brain and the timings — but they are the
  tuned reference for feel.

## Still open, inherited from spec §11

- ~~Whether shrines refill cans over time or are finite forever.~~ **Answered:
  finite forever.** One can per temple, no basin, no refills.
- Whether she is nocturnal, like a real swellshark.
- The befriending arc, now narrowed: since she does not fight mobs, a headpat
  counter could at most change *her* behaviour toward the victim, not turn her
  into a guard.
