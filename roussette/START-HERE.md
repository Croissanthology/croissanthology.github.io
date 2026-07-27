# Roussette — start here

You are the second Claude on this project. This file is the entry point; read it
before touching anything else.

**Goal:** produce one working `.jar` for **Minecraft Java 26.2 + NeoForge**, and
get it into three players' `mods` folders.

## What this is

A Minecraft mod. A small lavender catshark with cat ears who hunts one specific
player — Margot's younger brother — relentlessly and forever. She bites for half
a heart, refuses to bite below 3.5 hearts, and cannot kill. Hitting her launches
her across the room, ricocheting off walls, and she comes straight back. When he
gets into a bed she teleports to his pillow, flumps over, and snores until dawn.

She is Margot, rendered as a mob. Her voice is Margot's actual voice.

## The one thing to understand before you start

**This project is in two halves, and they have very different confidence levels.**

| | `core/` | `mod/src/main/java/roussette/` (minus `core/`) |
|---|---|---|
| What | brain, repellent, targeting, temple planning, geometry | the NeoForge adapter |
| Minecraft imports | **none** | everywhere |
| Compiled? | yes | **never** |
| Tests | **120, all passing** | none possible |

The first Claude could not reach `maven.neoforged.net` (blocked by network
policy), so NeoForge could never be downloaded and the adapter has never seen a
compiler. It also could not read `docs.neoforged.net`, so the API was
reconstructed from search results and prior knowledge — against a Minecraft
version newer than its training data.

**Expect the first build to fail.** That is the expected state, not a surprise.
Fixing it is the job.

## Order of work

### 1. Prove the core still passes

```sh
cd core
javac -d out $(find src test -name '*.java') && java -cp out roussette.Tests
```

→ `120 passed, 0 failed`. If this fails, something is wrong with the checkout,
not with the design.

### 2. Fix the build

```sh
cd mod
grep -rn "VERIFY:" src/main/java     # every unverified API call
```

`mod/README-INSTALL.md` ranks where breakage is most likely. Summary, worst first:

1. **`client/RoussetteModel.java` + `RoussetteRenderer.java`** — Minecraft moved
   entity rendering to a render-state pipeline. If 26.2 uses it, these need a
   `RoussetteRenderState` carrying pupil/drowsy/age. The geometry is fine.
2. **`save/RoussetteSaveData.java`** — `SavedData` moved to Codec +
   `SavedDataType`. If 26.2 predates that, revert to a `CompoundTag` pair.
3. **`RoussetteMod.java`** — registry helper names, `EntityType.Builder#build`,
   whether `Item.Properties` needs an explicit id.
4. **`entity/RoussetteEntity.java`** — `hurt` vs `hurtServer`, `MobEffects`
   holder constants, `hurtAndBreak` arguments.
5. **`gradle.properties`** — `neo_version` is a guess. Get the real current 26.2
   build from <https://projects.neoforged.net/neoforged/neoforge>. If Parchment
   mappings are not published for 26.2, delete the `parchment` block in
   `build.gradle`.

### 3. Build and install

```sh
./install.sh          # macOS / Linux
install.bat           # Windows
```

Builds, then copies the jar to the local `mods` folder. Output lands in
`mod/build/libs/`.

### 4. Distribute

Send **the same jar** to the other two players. Custom entities do not work
host-only — all three need it, plus NeoForge 26.2 in their launcher.

### 5. In the world

```
/roussette-spare <cousin's username>    # do this FIRST
/roussette-temples                      # once per world, ever
```

The brother is picked up automatically: any username containing `rousset` becomes
the target, and his is `I_eat_roussettes`.

## Things not to redesign

These look arbitrary and are not:

- **`SPEED_LAND = 0.15`, `SPEED_WATER = 0.32`.** Water doubles her speed and
  halves his. It is the entire reason the shrines are underwater.
- **She re-forms, she does not travel.** Everything is anchored to the victim, so
  dimension changes, ender pearls, `/tp` and death collapse into one mechanism.
  Replacing this with pathfinding breaks the Nether, the End and every teleport
  at once.
- **She is a `Mob`, not a `Monster`.** Vanilla blocks sleep near monsters. Change
  this and bedtime silently stops working.
- **She never speaks.** Sounds only. A test enforces that every noise she can
  emit is one of the recorded takes.
- **No repellent tolerance mechanic.** It was tried and cut: it makes the tools
  of the player already being hunted get worse over time.

## Open item — the sound labels

Margot recorded 13 takes in one file. The first Claude split it (boundaries are
solid — two independent settings agree) but **could not hear the audio**, so the
names are inferred from length and pitch. Two look wrong: clip 5 (`wail2`, 4.54s)
and clip 9 (`chomp2`, 5.26s) are long, low and tonal, which reads far more like
purrs than like a wail and a chomp.

`mod/sounds/review/` has every clip renamed `NN_starttime_guess.ogg` plus a
waveform plot. **Ask Margot to confirm the mapping before distributing the jar**,
or all three players re-download when it turns out to be wrong. Recutting is just
renaming — `mod/sounds/prepare.py` regenerates from the original recording.

No snort was recorded, so `snort` points at the snore take.

## Full documentation

| File | What |
|---|---|
| `WHAT-IT-DOES.md` | every behaviour, concretely, with the real constants |
| `DECISIONS.md` | what was decided and why; **overrules the spec** where they disagree |
| `ROUSSETTESPEC.md` | the original design document |
| `mod/README-INSTALL.md` | install, build, and the ranked list of likely breakage |
| `mod/sounds/RECORDING.md` | the take order, if anything needs re-recording |
| `core/README.md` | what the tested half contains |
| `design/roussette-model-render.png` | what she looks like |

## The four rules, in priority order

Every design decision serves these. If a change would violate one, it is wrong.

1. **She must be cute.** Not cute-menacing. Cute, and *separately* relentless.
2. **Hitting her must be fun.** The knockback is the core loop. Enormous and
   slightly ridiculous, every time, forever.
3. **She must never actually be a threat.** Half a heart, never below 3.5 hearts,
   cannot kill. Escalation would ruin her.
4. **She does not speak.** Sounds only. Dialogue makes her a character commenting
   on events; noises make her a thing that is *happening to you*.
