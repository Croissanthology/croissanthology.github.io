package roussette.core;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Parses the temple cross-section (a plain text block grid) into placements.
 *
 *  Keeping the structure as text rather than an NBT template means it stays
 *  readable, diffable, and editable by a human who is not running Minecraft. */
public final class Blueprint {

    public record Placement(int x, int y, String block) {}

    /** Legend. SHRINE_STONE must be a custom unbreakable block registered by the
     *  mod -- reinforced deepslate is NOT unbreakable (55 hardness, ~1 minute,
     *  drops nothing) and is not obtainable in survival. */
    public static final Map<Character, String> LEGEND = new LinkedHashMap<>();
    static {
        LEGEND.put('R', "roussette:shrine_stone");
        LEGEND.put('C', "minecraft:oxidized_copper");
        LEGEND.put('#', "minecraft:deepslate_tiles");
        LEGEND.put('~', "minecraft:water");
        LEGEND.put('S', "minecraft:sea_lantern");
        LEGEND.put('A', "minecraft:amethyst_cluster");
        LEGEND.put('D', "minecraft:copper_door");
        LEGEND.put('M', "roussette:mosaic_marker");
        LEGEND.put('F', "roussette:votive_frame");
        LEGEND.put('H', "minecraft:chest");
        LEGEND.put('B', "minecraft:bedrock");
        LEGEND.put('a', "minecraft:air");
        LEGEND.put('g', null);   // leave existing terrain
        LEGEND.put('s', null);
        LEGEND.put(' ', "minecraft:air");
    }

    private final List<Placement> placements = new ArrayList<>();
    private final int width, height;
    private final String grid;

    public Blueprint(String grid) {
        this.grid = grid;
        String[] rows = grid.split("\n");
        int w = 0;
        for (String r : rows) w = Math.max(w, r.length());
        this.width = w;
        this.height = rows.length;
        for (int y = 0; y < rows.length; y++) {
            for (int x = 0; x < rows[y].length(); x++) {
                char c = rows[y].charAt(x);
                if (!LEGEND.containsKey(c)) throw new IllegalArgumentException("unknown glyph '" + c + "'");
                String block = LEGEND.get(c);
                if (block != null) placements.add(new Placement(x, y, block));
            }
        }
    }

    public List<Placement> placements() { return placements; }
    public int width()  { return width; }
    public int height() { return height; }

    public int count(String block) {
        return (int) placements.stream().filter(p -> p.block().equals(block)).count();
    }

    // ---------------------------------------------------------------- 3D
    /** A block in the real world, relative to the temple's own origin. */
    public record Placement3(int x, int y, int z, String block) {}

    /** How far the cross-section is extruded along Z. */
    public static final int DEPTH = 13;
    /** Rows of mosaic hanging below the marker row. Five is what actually fits
     *  in the bottom chamber -- see the note on MOSAIC in the class docs. */
    public static final int MOSAIC_ROWS = 5;

    /** Glyphs that describe the *shape* of the building and are extruded all the
     *  way through. Everything else is a fitting, placed on one slice only. */
    private static boolean structural(char c) {
        return c == 'R' || c == 'C' || c == '#' || c == 'B';
    }
    /** Glyphs that are enclosed space, and therefore need the extruded ends
     *  capping or the shaft would be open to raw terrain on two sides. */
    private static boolean interior(char c) { return c == '~' || c == 'a'; }

    /**
     * Extrude the cross-section into a real 3D structure.
     *
     * <p>The cross-section is a schematic of the X-Y plane; the building is that
     * shape pushed {@code depth} blocks along Z. Three things stop this from
     * being a plain extrusion:
     *
     * <ul>
     *   <li><b>The ends have to be capped.</b> The section only draws walls on
     *       the X sides, so a naive extrude leaves the water shaft open to
     *       terrain at Z=0 and Z=depth-1. Interior glyphs become shrine stone
     *       on those two slices.</li>
     *   <li><b>Fittings must not be repeated.</b> Extruding the chest glyph
     *       through 13 slices gives 13 chests. Chests, doors and votive frames
     *       are placed on the centre slice only.</li>
     *   <li><b>The mosaic is a wall, not a row.</b> The {@code M} glyphs mark
     *       where she goes; the marker expands into a vertical plane on the
     *       back wall, which is what "filling the deepest wall" means.</li>
     * </ul>
     */
    /** The row of the cross-section that sits at the existing world surface.
     *  Everything above it is the squat above-ground lip; everything below is
     *  carved out of the terrain. Identified by the 'g' (ground) glyphs. */
    public int groundRow() {
        String[] rows = grid.split("\n");
        for (int y = 0; y < rows.length; y++) if (rows[y].indexOf('g') >= 0) return y;
        throw new IllegalStateException("cross-section has no ground row");
    }

    /** Horizontal centre of the shaft, so temples are placed around the site. */
    public int centreColumn() { return width / 2; }

    public List<Placement3> expand(int depth) {
        List<Placement3> out = new ArrayList<>();
        String[] rows = grid.split("\n");
        int centre = depth / 2, back = depth - 1;

        for (int y = 0; y < rows.length; y++) {
            for (int x = 0; x < rows[y].length(); x++) {
                char c = rows[y].charAt(x);
                String block = LEGEND.get(c);

                if (structural(c)) {
                    for (int z = 0; z < depth; z++) out.add(new Placement3(x, y, z, block));
                } else if (interior(c)) {
                    // cap both ends, leave the middle hollow
                    out.add(new Placement3(x, y, 0,    LEGEND.get('R')));
                    out.add(new Placement3(x, y, back, LEGEND.get('R')));
                    for (int z = 1; z < back; z++) out.add(new Placement3(x, y, z, block));
                } else if (c == 'H' || c == 'F' || c == 'D') {
                    out.add(new Placement3(x, y, centre, block));
                } else if (c == 'S' || c == 'A') {
                    // lights and crystals live on the two end walls
                    out.add(new Placement3(x, y, 0,    block));
                    out.add(new Placement3(x, y, back, block));
                } else if (c == 'M') {
                    for (int r = 0; r < MOSAIC_ROWS; r++)
                        out.add(new Placement3(x, y + r, back, block));
                }
                // 'g', 's' and ' ' leave the world alone
            }
        }
        return out;
    }

    public static int count3(List<Placement3> ps, String block) {
        return (int) ps.stream().filter(p -> p.block().equals(block)).count();
    }
}
