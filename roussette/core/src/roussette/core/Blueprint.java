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

    public Blueprint(String grid) {
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
}
