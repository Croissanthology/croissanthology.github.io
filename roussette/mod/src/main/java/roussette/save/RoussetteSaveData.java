package roussette.save;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

import roussette.core.TempleBuilder;
import roussette.core.VictimRegistry;

import java.util.ArrayList;
import java.util.List;

/**
 * Everything the world has to remember: who she is hunting, who is permanently
 * safe, whether the temples have been built, and how long until she re-forms.
 *
 * <p>Stored on the Overworld only and read from there by every dimension, which
 * is what makes "she re-forms, she does not travel" work across the Nether and
 * the End without any special cases.
 *
 * <p>VERIFY: SavedData moved to a Codec + SavedDataType model in recent
 * versions. If 26.2 still wants the older shape, this becomes a
 * {@code save(CompoundTag, HolderLookup.Provider)} override plus a
 * {@code SavedData.Factory}. The fields and logic below do not change either way.
 */
public class RoussetteSaveData extends SavedData {

    public static final String NAME = "roussette";

    private final VictimRegistry registry = new VictimRegistry();
    private final TempleBuilder.OneShot temples = new TempleBuilder.OneShot();
    private int reformIn;

    public RoussetteSaveData() {}

    private RoussetteSaveData(String victim, String runState, int reformIn, List<String> prot) {
        prot.forEach(registry::protect);
        if (!victim.isEmpty()) registry.newTarget(victim);
        this.temples.restore(TempleBuilder.RunState.valueOf(runState));
        this.reformIn = reformIn;
    }

    public static final Codec<RoussetteSaveData> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.STRING.optionalFieldOf("victim", "").forGetter(d -> d.registry.target() == null ? "" : d.registry.target()),
            Codec.STRING.optionalFieldOf("runState", "NEVER_RUN").forGetter(d -> d.temples.state().name()),
            Codec.INT.optionalFieldOf("reformIn", 0).forGetter(d -> d.reformIn),
            Codec.STRING.listOf().optionalFieldOf("protected", List.of())
                    .forGetter(d -> new ArrayList<>(d.registry.protectedPlayers()))
    ).apply(i, RoussetteSaveData::new));

    // VERIFY: SavedDataType(id, constructor, codec).
    public static final SavedDataType<RoussetteSaveData> TYPE =
            new SavedDataType<>(NAME, RoussetteSaveData::new, CODEC);

    /** Always resolves against the Overworld, from any dimension. */
    public static RoussetteSaveData get(ServerLevel anyLevel) {
        ServerLevel overworld = anyLevel.getServer().overworld();
        return overworld.getDataStorage().computeIfAbsent(TYPE);
    }

    // --- victim ---------------------------------------------------------------
    public VictimRegistry registry() { return registry; }

    public boolean newTarget(String name) {
        boolean ok = registry.newTarget(name);
        if (ok) setDirty();
        return ok;
    }

    public void protect(String name) { registry.protect(name); setDirty(); }

    /** Auto-adopt on join, so a taunting username picks its own fight. */
    public void onPlayerJoin(String name) {
        if (registry.adoptIfTaunting(name)) setDirty();
    }

    /** The current victim as a live player, or null if they are offline. */
    public Player findVictim(Level level) {
        String t = registry.target();
        if (t == null) return null;
        for (Player p : level.players()) {
            if (p.getGameProfile().getName().equalsIgnoreCase(t)) return p;
        }
        return null;
    }

    // --- temples --------------------------------------------------------------
    public TempleBuilder.OneShot temples() { return temples; }

    public boolean tryStartTemples() {
        boolean ok = temples.tryFire();
        if (ok) setDirty();
        return ok;
    }

    public void finishTemples() { temples.complete(); setDirty(); }

    // --- reform ---------------------------------------------------------------
    public void scheduleReform(int ticks) { this.reformIn = ticks; setDirty(); }

    /** @return true on the tick she should come back. */
    public boolean tickReform() {
        if (reformIn <= 0) return false;
        if (--reformIn == 0) { setDirty(); return true; }
        return false;
    }
}
