# roussette-core

The half of the mod that has no Minecraft in it — and is therefore **tested**.

```sh
cd roussette/core
javac -d out $(find src test -name '*.java') && java -cp out roussette.Tests
```
→ **55 passed, 0 failed.** (Run it from `roussette/core`; the blueprint test
reads `src/roussette/core/temple.txt` by relative path.)

## Why this is split off

Minecraft 26.2 shipped in June 2026, after the training data of the model that
wrote this. Java written against a half-remembered API surface would be
confident-looking guesswork, and a large non-compiling codebase is harder to fix
than to write. So this module contains only what can be verified *without the
game*, and every behavioural claim in the spec is asserted in `Tests.java`.

That decision also made the loader question cheap: because nothing here imports
Minecraft, targeting NeoForge instead of Fabric changes only the adapter.

## What's here

| File | What it is |
|---|---|
| `Ports.java` | The seam. Two interfaces: `Sensors` (what she perceives) and `Actuators` (what she does). |
| `Roussette.java` | The brain. Full state machine, every tuned constant, no Minecraft imports. |
| `Repellent.java` | Can and treated-armour accounting. Deliberately has **no** tolerance mechanic. |
| `SiteFinder.java` | Temple placement: spiral search, flatness test, one per biome, 1500-block spacing. |
| `Blueprint.java` | Parses `temple.txt` into block placements. |
| `Geometry.java` | The 20 boxes, the palette, the three pupil states. |
| `temple.txt` | The temple cross-section as a readable block grid. |

## What the adapter still has to do

Target is **Minecraft Java 26.2 + NeoForge** (see `../DECISIONS.md`).

1. **Implement `Ports.Sensors` and `Ports.Actuators`** against the real entity.
   Tick the brain once per entity tick. That's the whole integration.
   `Actuators.bounce(retain)` must reflect her velocity off the surface she hit —
   the ricochet is a feature, not a collision response.
2. **Entity + renderer + model** from `Geometry.PARTS`. Custom hitbox.
   `MAX_HEALTH = 30` half-hearts. No attack goals and no mob aggro in either
   direction: she does not fight mobs and does not attract them.
3. **Victim registry.** She hunts exactly one registered player, persisted in
   world save data. Every other player is a bystander who can still hit, pat and
   spray her. Bystanders must never be selectable as the victim by accident.
4. **Death and return.** On zero health call `onDefeated`, remove her, and bring
   her back `REFORM_DELAY` ticks later through `onReform`. Same path as a
   dimension change, a teleport, or burning alive.
5. **Register `roussette:shrine_stone`** — bedrock-like hardness. Do *not* use
   reinforced deepslate; it breaks in about a minute and drops nothing.
6. **The `/roussette-temples` command.** The genuinely hard part — see §8 of the
   spec. Force-load chunks, place incrementally across ticks, persist a
   one-shot flag in world save data.
7. **Items:** the can, the anvil recipe, the treated-armour tint.
8. **Sounds:** ten events, Margot's own recordings, mono OGG Vorbis.

## Three things not to redesign

- **`SPEED_LAND = 0.15`, `SPEED_WATER = 0.32`.** Descending doubles her speed and
  halves his. It is the entire reason the temples are underwater.
- **She re-forms, she does not travel.** Anchor everything to the victim and
  dimension changes, teleports and death collapse into one mechanism. Replacing
  this with pathfinding breaks the Nether, the End, and every `/tp`.
- **She never speaks.** `eep` and `huff` are recordings, not text. `Tests.java`
  asserts that every sound she can emit is one of the ten takes, specifically so
  a line of dialogue cannot creep in later.
