# Shared brief: why does growth + plurality empower people more than raw necessity?

## Who is asking and why

Margot writes croissanthology.com and is finishing a long essay (MATS program, mentors wrote
*The Intelligence Curse*) on a tension: we want humans to stay **necessary** after advanced AI,
because necessity seems to be what keeps people empowered, but we don't want humans
**instrumentalized** so hard they lose something. Margot says plainly they do not know math,
game theory or economics, and wants models built and run on their behalf.

Their relevant posts (read if useful; text is in the repo as JSON with a `body_html` field):
- `_substack/are-u-necessary.json` ("What does it mean to be necessary to something?")
- `_substack/how-empowering-is-civilization.json`
- `_substack/does-individual-empowerment-trade.json`

## The puzzle, in Margot's words (lightly condensed)

- "Necessity is really not a saving grace in all situations. Serfs were always necessary, yet
  not particularly empowered at all." Current LLMs are another candidate counterexample:
  necessary and instrumentalized, yet hardly empowered.
- Meanwhile "Sally the Netflix exec" is barely necessary to anyone (she cannot threaten the
  government by withholding season 4 of *Is It Cake*), yet she is relatively empowered to do
  as she wishes with her life. "It's a soft wind of incentives that keeps everything in place,
  and no one individual has much bargaining power."
- "When you don't begin from complete autocracy, the sheer wind of 2% year-on-year GDP growth
  really is sufficient to incentivize civilization not to slouch towards tyranny." "Perhaps
  it's the very idea of regular return on your investment that keeps us up and running, that
  there really IS growth to be had. Whereas if you're in a zero-sum system you genuinely are
  going to find yourself disempowered by a big baddie. Why is this? Can you prove this with
  math? Can you run game theory simulations on whether people being incentivized to grow in
  small ways have some kind of power that doesn't exist in a zero-sum system?"
- "Simulate a world in which there's consistent growth that people can participate in if they
  combine into particular chains of organisation, then simulate the same world in which 2% GDP
  growth is not possible. What would one notice? Is this already part of economics? Are there
  disempowerment curves in economics? What would happen if I pressed all the way here?"
- "It's clear that one reason humans are empowered in the US is because we can vote. But what
  about the Chinese? Why are they empowered?" (Margot's claim: existing autocracies such as
  China stay "broadly aligned with their citizens' well-being", while Kim Jong Un is content
  to keep North Korea far below potential.)
- "Part of what makes necessity empowering is presumably that many depend on us... something
  about the empowerment being in the plurality itself. Is this a mathematically defensible
  model? What does mathematically defensible even mean?"

## What every agent should do

You own ONE angle (given in your prompt). Other agents own the others; do not do their work.

1. Build the model(s), run them, and sweep parameters. Use Python 3 (numpy, scipy,
   matplotlib, pandas, networkx are installed). Fix random seeds. Keep total runtime of your
   full pipeline under about 10 minutes on 4 cores.
2. Be an honest scientist, not an advocate. Margot's hunch may be wrong, partly right, or
   right for a different reason. Do not tune parameters until the hoped-for picture appears.
   If growth by itself does NOT produce empowerment in your model, that is a finding: say what
   extra ingredient is needed. Always report which assumption drives each result, and run at
   least one ablation that removes it. Report results that surprised you.
3. Keep "necessity" (how much the system loses without you) and "empowerment" (how much
   control you have over your own outcomes / what share you keep / how many futures you can
   reach) as separately measured quantities. Never define one as the other.
4. Write everything into your own folder `research/growth-empowerment/<your-folder>/`:
   - the code (runnable with `python3 <file>.py` from that folder, regenerates everything),
   - `results.json`: the key numeric series behind each main chart, small (under 200 KB),
     with self-explanatory keys, so someone else can redraw the charts,
   - PNG figures (matplotlib, dpi 150, readable labels, no jargon in titles),
   - `FINDINGS.md`: at most 700 words, written for a smart reader with no math background.
     Structure: the question in one sentence; what the model is, as a little story with
     named characters; what happened when it ran (with the actual numbers); what drives it;
     what it does NOT show / where it could be wrong; the closest existing work in economics
     or political science (name author + year only if you are confident it exists; never
     invent a citation).
5. Do not touch files outside your folder. Do not commit or push. Do not spawn subagents.
6. Your final message back should be the findings in under 400 words: headline result, the
   three most important numbers, the driving assumption, and the biggest caveat. Say plainly
   if something failed or was not run.
