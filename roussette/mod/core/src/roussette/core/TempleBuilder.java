package roussette.core;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Turning a chosen site into blocks, without hanging the server.
 *
 *  <p>{@code /roussette-temples} has to work in a world that already exists, so
 *  the structure cannot come from worldgen -- it is written block by block into
 *  live chunks. Doing that synchronously for a dozen temples, each 34 blocks
 *  deep, freezes the server for long enough that everyone times out. So the work
 *  is chopped into per-chunk batches and spread across ticks.
 *
 *  <p>This class is the bookkeeping half, and it is pure: coordinate mapping,
 *  chunk grouping, batching, and the run-once flag. The adapter supplies force
 *  loading and the actual block writes. */
public final class TempleBuilder {
    private TempleBuilder() {}

    /** Blocks written per tick. Conservative on purpose -- a temple is a few
     *  thousand blocks, so this finishes one in well under a second of game
     *  time while leaving the tick budget alone. */
    public static final int BLOCKS_PER_TICK = 512;

    /** A block in absolute world coordinates. */
    public record Abs(int x, int y, int z, String block) {
        public int chunkX() { return x >> 4; }
        public int chunkZ() { return z >> 4; }
    }

    /**
     * Map temple-local coordinates onto the world.
     *
     * <p>Grid rows run downward (row 0 is sky) while Minecraft Y runs upward, so
     * Y is mirrored about the cross-section's ground row. That row is pinned to
     * the site's surface height, which is what makes the above-ground lip sit
     * flush with the terrain and the shaft descend into it.
     */
    public static List<Abs> toWorld(List<Blueprint.Placement3> local, SiteFinder.Site site,
                                    int groundRow, int centreColumn, int depth) {
        List<Abs> out = new ArrayList<>(local.size());
        for (Blueprint.Placement3 p : local) {
            out.add(new Abs(
                site.x() + (p.x() - centreColumn),
                site.surfaceY() + (groundRow - p.y()),
                site.z() + (p.z() - depth / 2),
                p.block()));
        }
        return out;
    }

    /** One chunk's worth of writing. The adapter force-loads {@code chunkX/chunkZ},
     *  writes the blocks, and releases it when {@link #last} is true. */
    public record Batch(int chunkX, int chunkZ, List<Abs> blocks, boolean last) {}

    /** Groups placements by chunk, preserving a stable order so a run is
     *  reproducible and can be resumed after a restart. */
    public static Map<Long, List<Abs>> byChunk(List<Abs> blocks) {
        Map<Long, List<Abs>> map = new LinkedHashMap<>();
        for (Abs a : blocks) {
            long key = (((long) a.chunkX()) << 32) ^ (a.chunkZ() & 0xffffffffL);
            map.computeIfAbsent(key, k -> new ArrayList<>()).add(a);
        }
        return map;
    }

    /** Hands out one {@link Batch} per tick, never spanning two chunks, so only
     *  one chunk is force-loaded at a time. */
    public static final class Schedule {
        private final List<List<Abs>> chunks = new ArrayList<>();
        private final int budget;
        private int chunk, offset, written;
        private final int total;

        public Schedule(List<Abs> blocks, int budget) {
            this.budget = Math.max(1, budget);
            this.total = blocks.size();
            chunks.addAll(byChunk(blocks).values());
        }

        public boolean done()     { return chunk >= chunks.size(); }
        public int written()      { return written; }
        public int total()        { return total; }
        public int chunkCount()   { return chunks.size(); }
        public double progress()  { return total == 0 ? 1.0 : written / (double) total; }

        /** @return the next slice of work, or null when finished. */
        public Batch next() {
            if (done()) return null;
            List<Abs> cur = chunks.get(chunk);
            int end = Math.min(cur.size(), offset + budget);
            List<Abs> slice = new ArrayList<>(cur.subList(offset, end));
            boolean lastOfChunk = end >= cur.size();
            Abs any = slice.get(0);
            Batch b = new Batch(any.chunkX(), any.chunkZ(), slice, lastOfChunk);
            written += slice.size();
            if (lastOfChunk) { chunk++; offset = 0; } else { offset = end; }
            return b;
        }
    }

    /** Temples exist in the Overworld only. */
    public static final String HOME_DIMENSION = "minecraft:overworld";

    public static boolean canBuildIn(String dimension) {
        return HOME_DIMENSION.equals(dimension);
    }

    public enum RunState { NEVER_RUN, RUNNING, COMPLETED }

    /**
     * "Runs once, ever" — per <em>world</em>, not per player.
     *
     * <p>The latch flips to RUNNING <em>before</em> the first block is written,
     * not after the last one. That ordering is the whole point: three players
     * typing the command in the same second must produce one set of temples,
     * not three overlapping sets carved through each other. The second and
     * third invocations are refused while the first is still placing.
     *
     * <p>Persisted in world save data, so a restart part-way through a run does
     * not reopen the door either. A run interrupted by a crash stays RUNNING
     * and stays refused — deliberately, because the alternative is letting a
     * half-built temple be built over.
     */
    public static final class OneShot {
        private RunState state = RunState.NEVER_RUN;

        /** @return true if this invocation may proceed. Flips the latch. */
        public boolean tryFire() {
            if (state != RunState.NEVER_RUN) return false;
            state = RunState.RUNNING;
            return true;
        }

        /** Called once the last batch has been written. */
        public void complete() { state = RunState.COMPLETED; }

        public RunState state()  { return state; }
        public boolean fired()   { return state != RunState.NEVER_RUN; }

        /** Restore from save data on server start. */
        public void restore(RunState s) { state = s; }

        /** What the refused player is told. */
        public String refusal() {
            return switch (state) {
                case NEVER_RUN -> "";
                case RUNNING   -> "The temples are being built right now. Wait.";
                case COMPLETED -> "The temples have already been built in this world. "
                                + "They only ever appear once.";
            };
        }
    }
}
