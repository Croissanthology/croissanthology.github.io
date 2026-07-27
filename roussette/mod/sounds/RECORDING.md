# Recording her voice

**One file. Twelve takes. In this order. Two seconds of silence between each.**

Then send it to me, or run `python3 prepare.py yourfile.wav` yourself — it finds
the gaps, cuts the takes out, names them, and rewires `sounds.json`.

## Before you start

- **Quiet room.** Laptop or phone mic is completely fine. Room tone is fine;
  a fridge hum is fine. What ruins it is a fan or music, because the splitter
  finds takes by looking for gaps, and constant noise means there are no gaps.
- **Stay the same distance from the mic** for all twelve, so the levels match.
- **Don't shout into it.** Clipping cannot be undone. Loud-but-not-blown.
- **Two seconds of silence between takes.** More is fine. Less is risky.
- **Start and end with two seconds of silence** too.
- **Don't count yourself in out loud** — "three, two, one" is a sound, and the
  splitter will faithfully cut it out and name it `cry1`.
- If you fluff one, **stop, wait two seconds, and start the whole file again.**
  Much easier than fixing it later.
- Export **16-bit WAV** if you can. If you can only get m4a or mp3, that's fine
  too — `prepare.py` will convert it, as long as ffmpeg is installed.

## The twelve takes, in order

| # | Name | Length | What it's for | How to do it |
|---|---|---|---|---|
| 1 | **cry** take 1 | ~0.3 s | He hits her | A short, sharp, indignant yelp. Not pain — *offence*. |
| 2 | **cry** take 2 | ~0.3 s | ” | Same again, a bit different. Slightly higher. |
| 3 | **cry** take 3 | ~0.3 s | ” | Once more, grumpier. The game picks one at random each hit. |
| 4 | **wail** take 1 | ~1.0 s | Airborne, and on being defeated | A longer descending "aaaaAAAAaaaa" — the doppler of a small shark sailing across a room. Plays three times per fling, so it wants to be a bit silly. |
| 5 | **wail** take 2 | ~1.0 s | ” | Same idea, different shape. |
| 6 | **purr** | ~1.5 s | Headpats, and being patted while knocked out | A real purr, low and continuous. This is the reward sound — it should be genuinely nice. |
| 7 | **purreow** | ~0.8 s | Mid-headpat, once | A purr that turns into a questioning "mrrrow?" at the end. Rising. |
| 8 | **chomp** take 1 | ~0.25 s | A bite lands | Wet, quick, close to the mic. A gulpy *nom*. |
| 9 | **chomp** take 2 | ~0.25 s | ” | Again, slightly different. |
| 10 | **gnaw** | ~0.5 s | Latched onto his feet, every 1.2 s | The shoulder-chewing noise. Persistent, unbothered, a bit rhythmic. This is the one that plays over and over while she's attached, so make it something you'd tolerate hearing a lot. |
| 11 | **eep** | ~0.3 s | First ricochet off a wall | **"EEEP!"** Startled, high, brief. The single funniest sound in the mod. |
| 12 | **huff** | ~0.6 s | Landing, before she resumes hunting | The "Ok. Ok. anyway." — a sharp exhale through the nose, collecting herself. Dignity reassembling. No words. |

**Total: about 30–40 seconds of recording**, most of which is silence.

## What you are *not* recording

`squelch` (wall impacts, popping free of a doorway) and `reform` (rematerialising
behind him) stay as vanilla Minecraft slime and splash sounds. Nobody can perform
a wet impact against a wall, and the vanilla ones are already good.

## Running it yourself

```sh
cd mod/sounds
python3 prepare.py margot-sounds.wav --dry-run   # check the split first
python3 prepare.py margot-sounds.wav             # then do it for real
```

`--dry-run` prints where it thinks each take starts and how long it is, without
writing anything. **Always run that first** — if the count is not 12, the labels
will be off by one and everything gets misnamed.

If the count is wrong:

| Symptom | Fix |
|---|---|
| Too few clips — two takes ran together | `--min-gap 0.30` |
| Too many clips — one take got cut in half | `--min-gap 0.80` |
| Too many clips — room noise counted as takes | `--floor 6.0` |
| Clips sound clipped at the start | `--pad 120` |

With ffmpeg installed it writes `.ogg` directly and you are done. Without it,
it writes `.wav` and prints the one command to finish the conversion — Minecraft
only plays OGG Vorbis, so that step is not optional.

Then re-run `./install.sh` and she has your voice.
