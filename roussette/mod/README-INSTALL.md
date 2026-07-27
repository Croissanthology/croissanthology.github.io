# Roussette — install

**Read the honesty note at the bottom before you start.** It matters.

## Quick version

```sh
./install.sh          # macOS / Linux
install.bat           # Windows
```

That builds the mod and copies the jar into your `mods` folder. First build
downloads NeoForge and takes a few minutes; after that it is offline and fast.

Then:

1. Launch the **NeoForge 26.2** profile, not vanilla.
2. **Everyone on the LAN world needs the same jar** in their `mods` folder —
   custom entities do not work if only the host has them.
3. In the world, once ever: `/roussette-temples`

## Requirements

- **Java 21 or newer.**
- **Gradle**, either as `./gradlew` or on your PATH. If you have neither, copy
  `gradlew`, `gradlew.bat` and the `gradle/` folder out of any NeoForge MDK zip
  into this directory — the install script will then use them. It will also
  generate a wrapper for you automatically if plain `gradle` is installed.
- An internet connection for the first build only.

## Commands

| Command | What it does |
|---|---|
| `/roussette-temples` | Builds every shrine. **Once per world, ever.** Overworld only. |
| `/new-target <name>` | Points her at somebody new. |
| `/roussette-spare <name>` | Makes somebody permanently safe. Beats everything else. |

She automatically hunts anyone whose username contains `rousset`, so
`I_eat_roussettes` picks his own fight the moment he logs in. Spare your cousin
explicitly with `/roussette-spare` and he can still pat, punt and spray her —
he just cannot be prey.

## Swapping in your own voice

The mod ships fully audible using **vanilla cat and slime sounds as
placeholders**, so nothing is silent on day one. To replace them with your
recordings:

1. Save each take as **mono OGG Vorbis** in
   `src/main/resources/assets/roussette/sounds/`.
2. Edit `src/main/resources/assets/roussette/sounds.json` and swap the
   placeholder entry for your file. For example, replace

   ```json
   "cry": { "category": "hostile", "subtitle": "subtitles.roussette.cry",
            "sounds": [{ "name": "entity.cat.hurt", "type": "event" }] }
   ```

   with

   ```json
   "cry": { "category": "hostile", "subtitle": "subtitles.roussette.cry",
            "sounds": ["roussette:cry1", "roussette:cry2", "roussette:cry3"] }
   ```

   (three files → she picks one at random each time).
3. Re-run `./install.sh`.

The eight vocal events are `cry`, `wail`, `purr`, `purreow`, `chomp`, `gnaw`,
`eep`, `huff`. Leave `squelch` and `reform` pointing at the vanilla slime and
splash sounds — nobody can perform a wet impact against a wall.

## Textures

The shipped textures are generated placeholders: real palette, correct layout,
but plainly programmer art. `src/main/resources/assets/roussette/textures/` has
her body sheet, the repellent can, the shrine stone, and her painting. All are
straightforward to redraw; the body sheet's layout is documented in the header
comment of `RoussetteModel.java`.

---

## The honesty note

**The Minecraft-facing half of this mod has never been compiled.**

The environment it was written in blocked `maven.neoforged.net`, so NeoForge
could not be downloaded, and blocked `docs.neoforged.net`, so the API could not
be read directly. That half was written from a mix of search results and prior
knowledge of the NeoForge API, against **Minecraft 26.2, which is newer than the
author's training data.**

What that means in practice: **expect the first build to fail with compile
errors**, and expect them to be concentrated in a few predictable places. This
is normal for this situation and not a sign the design is wrong.

Every line the author could not verify is tagged `// VERIFY:`. Find them all:

```sh
grep -rn "VERIFY:" src/main/java
```

Ranked by how likely they are to need fixing:

1. **`client/RoussetteModel.java`** — Minecraft moved entity rendering to a
   render-state pipeline. If 26.2 uses it, this file and `RoussetteRenderer`
   need a `RoussetteRenderState` and different method signatures. The geometry
   itself is fine either way.
2. **`save/RoussetteSaveData.java`** — `SavedData` moved to a Codec +
   `SavedDataType` model. If 26.2 predates that, this reverts to a
   `CompoundTag` save/load pair.
3. **`RoussetteMod.java`** — registry helper names, `EntityType.Builder#build`,
   and whether `Item.Properties` now needs an explicit id.
4. **`entity/RoussetteEntity.java`** — `hurt` vs `hurtServer`, the `MobEffects`
   holder constants, and `hurtAndBreak`'s argument list.
5. **`gradle.properties`** — `neo_version` is a guess. Look up the real current
   26.2 build at <https://projects.neoforged.net/neoforged/neoforge>. If
   Parchment mappings are not published for 26.2, delete the `parchment` block
   in `build.gradle`.

**What is solid:** everything in `src/main/java/roussette/core/`. That is the
brain, the repellent maths, the victim rules, the temple planner and the
geometry — **107 passing tests, no Minecraft required**. You can run them
yourself:

```sh
cd ../core && javac -d out $(find src test -name '*.java') && java -cp out roussette.Tests
```

So the behaviour is verified and the plumbing is not. Fix the plumbing and the
mod works, because none of the decisions that make her *her* live in the
plumbing.
