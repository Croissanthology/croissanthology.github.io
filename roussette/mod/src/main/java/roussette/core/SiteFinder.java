package roussette.core;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Chooses where the temples go.
 *
 *  This exists because /roussette-temples has to work in a world that ALREADY
 *  EXISTS. Normal structure generation only touches newly generated chunks, so
 *  placement has to be done imperatively: scan outward, judge the terrain, and
 *  write blocks directly. This class is the judging half, and it is pure, so it
 *  can be tested against synthetic terrain without running the game. */
public final class SiteFinder {

    /** Implemented by the adapter over the real world. */
    public interface Terrain {
        int    surfaceY(int x, int z);
        String biome(int x, int z);
        boolean isLand(int x, int z);
    }

    public record Site(int x, int z, String biome, int surfaceY) {}

    public static final int    STEP        = 96;    // sample spacing
    public static final int    FLAT_RADIUS = 7;     // half-width of the flatness test
    public static final int    FLAT_TOL    = 2;     // max surface variance, blocks
    public static final double MIN_SPACING = 1500;  // between any two temples
    public static final int    DEPTH_NEEDED = 40;   // shaft plus floor

    /** Spiral outward from the origin, taking at most one site per biome. */
    public List<Site> find(Terrain t, int originX, int originZ, int searchRadius, int maxSites) {
        List<Site> sites = new ArrayList<>();
        Set<String> biomesUsed = new HashSet<>();
        for (int ring = 1; ring * STEP <= searchRadius && sites.size() < maxSites; ring++) {
            for (int i = -ring; i <= ring && sites.size() < maxSites; i++) {
                for (int j = -ring; j <= ring; j++) {
                    if (Math.max(Math.abs(i), Math.abs(j)) != ring) continue;  // ring edge only
                    int x = originX + i * STEP, z = originZ + j * STEP;
                    if (!t.isLand(x, z)) continue;
                    String biome = t.biome(x, z);
                    if (biomesUsed.contains(biome)) continue;
                    if (!flatEnough(t, x, z)) continue;
                    if (t.surfaceY(x, z) < DEPTH_NEEDED) continue;   // no room for the shaft
                    if (tooClose(sites, x, z)) continue;
                    sites.add(new Site(x, z, biome, t.surfaceY(x, z)));
                    biomesUsed.add(biome);
                    if (sites.size() >= maxSites) break;
                }
            }
        }
        return sites;
    }

    boolean flatEnough(Terrain t, int cx, int cz) {
        int min = Integer.MAX_VALUE, max = Integer.MIN_VALUE;
        for (int dx = -FLAT_RADIUS; dx <= FLAT_RADIUS; dx += 2) {
            for (int dz = -FLAT_RADIUS; dz <= FLAT_RADIUS; dz += 2) {
                if (!t.isLand(cx + dx, cz + dz)) return false;
                int y = t.surfaceY(cx + dx, cz + dz);
                min = Math.min(min, y);
                max = Math.max(max, y);
            }
        }
        return (max - min) <= FLAT_TOL;
    }

    boolean tooClose(List<Site> sites, int x, int z) {
        for (Site s : sites) {
            double dx = s.x() - x, dz = s.z() - z;
            if (Math.sqrt(dx * dx + dz * dz) < MIN_SPACING) return true;
        }
        return false;
    }
}
