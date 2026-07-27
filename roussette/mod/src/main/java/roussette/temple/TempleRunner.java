package roussette.temple;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

import roussette.core.Blueprint;
import roussette.core.SiteFinder;
import roussette.core.TempleBuilder;

import java.util.ArrayList;
import java.util.List;

/**
 * Places every temple, a few hundred blocks per tick.
 *
 * <p>This is the hard part of the whole mod and the reason it exists: structures
 * normally only generate in brand-new chunks, and this has to work in a world
 * that already exists. So nothing is asked of worldgen -- blocks are written
 * directly into live chunks, which means the chunks have to be force-loaded, and
 * doing that for a dozen 34-block-deep shafts in one tick freezes the server
 * long enough for everyone to time out.
 *
 * <p>All the bookkeeping (site choice, coordinate mapping, chunk grouping,
 * batching) is in the tested core. This class supplies only the three things
 * that need a real world: reading terrain, force-loading, and writing blocks.
 */
public class TempleRunner {

    private final List<TempleBuilder.Abs> pending = new ArrayList<>();
    private final List<SiteFinder.Site> sites;
    private final ServerLevel level;
    private TempleBuilder.Schedule schedule;
    private ChunkPos held;
    private boolean done;

    public TempleRunner(ServerLevel level, String grid, int searchRadius, int maxSites) {
        this.level = level;
        Blueprint bp = new Blueprint(grid);
        List<Blueprint.Placement3> solid = bp.expand(Blueprint.DEPTH);

        BlockPos spawn = level.getSharedSpawnPos();
        this.sites = new SiteFinder().find(new LevelTerrain(level),
                spawn.getX(), spawn.getZ(), searchRadius, maxSites);

        for (SiteFinder.Site site : sites) {
            pending.addAll(TempleBuilder.toWorld(
                    solid, site, bp.groundRow(), bp.centreColumn(), Blueprint.DEPTH));
        }
        this.schedule = new TempleBuilder.Schedule(pending, TempleBuilder.BLOCKS_PER_TICK);
        this.done = pending.isEmpty();
    }

    public List<SiteFinder.Site> sites() { return sites; }
    public boolean isDone() { return done; }
    public int total() { return pending.size(); }

    public void tick(MinecraftServer server) {
        if (done) return;
        TempleBuilder.Batch batch = schedule.next();
        if (batch == null) { release(); done = true; return; }

        ChunkPos want = new ChunkPos(batch.chunkX(), batch.chunkZ());
        if (!want.equals(held)) { release(); hold(want); }

        for (TempleBuilder.Abs a : batch.blocks()) {
            BlockState state = stateOf(a.block());
            if (state == null) continue;
            BlockPos pos = new BlockPos(a.x(), a.y(), a.z());
            if (level.isInWorldBounds(pos)) {
                // flag 2 = send to clients, skip neighbour updates. Neighbour
                // updates here would cascade water physics through a 34-block
                // shaft mid-build and cost far more than the placement itself.
                level.setBlock(pos, state, 2);
            }
        }

        if (batch.last()) { release(); }
    }

    private void hold(ChunkPos pos) {
        // VERIFY: setChunkForced(x, z, true) is the long-lived force-load; the
        // alternative is level.getChunkSource().addRegionTicket(...).
        level.setChunkForced(pos.x, pos.z, true);
        held = pos;
    }

    private void release() {
        if (held != null) { level.setChunkForced(held.x, held.z, false); held = null; }
    }

    private BlockState stateOf(String id) {
        if (id.equals("minecraft:air")) return Blocks.AIR.defaultBlockState();
        ResourceLocation rl = ResourceLocation.parse(id);
        // VERIFY: BuiltInRegistries.BLOCK.getOptional / .get returning Optional
        // vs Holder in this version.
        var block = BuiltInRegistries.BLOCK.getOptional(rl).orElse(null);
        return block == null ? null : block.defaultBlockState();
    }

    public Component report() {
        StringBuilder sb = new StringBuilder("Roussette shrines placed:");
        for (SiteFinder.Site s : sites) {
            sb.append("\n  ").append(s.biome())
              .append(" @ ").append(s.x()).append(", ").append(s.z());
        }
        return Component.literal(sb.toString());
    }

    /** The adapter's half of SiteFinder.Terrain. */
    private record LevelTerrain(ServerLevel level) implements SiteFinder.Terrain {
        @Override public int surfaceY(int x, int z) {
            return level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, x, z);
        }
        @Override public String biome(int x, int z) {
            var holder = level.getBiome(new BlockPos(x, surfaceY(x, z), z));
            return holder.getRegisteredName();   // VERIFY: unwrapKey().get().location() if absent
        }
        @Override public boolean isLand(int x, int z) {
            int y = surfaceY(x, z);
            return !level.getBlockState(new BlockPos(x, y - 1, z)).getFluidState().isSource();
        }
    }
}
