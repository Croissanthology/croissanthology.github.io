package roussette;

import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.item.component.CustomData;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import roussette.core.Repellent;
import roussette.core.Roussette;
import roussette.entity.RoussetteEntity;
import roussette.save.RoussetteSaveData;
import roussette.temple.TempleRunner;

import java.util.List;

/**
 * The part that makes her inescapable.
 *
 * <p>Everything here is anchored to the <em>victim</em>, never to the shark.
 * Each tick this asks "is there a roussette near him, in whatever dimension he
 * is currently standing in?" and if not, one appears behind him with a splash.
 * That single question is what makes the Nether, the End, ender pearls,
 * {@code /tp} and dying all behave identically without any of them being
 * special-cased. Replacing it with pathfinding breaks all five at once.
 */
@EventBusSubscriber(modid = RoussetteMod.MOD_ID)
public final class RoussetteManager {

    /** No roussette within this many blocks of him means one re-forms. */
    public static final double REFORM_RADIUS = 90.0;

    private static TempleRunner activeRun;

    public static void setActiveRun(TempleRunner runner) { activeRun = runner; }

    @SubscribeEvent
    public static void onJoin(PlayerEvent.PlayerLoggedIn event) {
        if (!(event.getEntity().level() instanceof ServerLevel level)) return;
        RoussetteSaveData.get(level).onPlayerJoin(event.getEntity().getGameProfile().getName());
    }

    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        ServerLevel overworld = server.overworld();
        RoussetteSaveData data = RoussetteSaveData.get(overworld);

        // 1. keep placing temples, a few hundred blocks a tick
        if (activeRun != null) {
            activeRun.tick(server);
            if (activeRun.isDone()) { data.finishTemples(); activeRun = null; }
        }

        // 2. she re-forms rather than travels
        boolean due = data.tickReform();
        Player victim = null;
        for (ServerLevel level : server.getAllLevels()) {
            Player p = data.findVictim(level);
            if (p != null) { victim = p; break; }
        }
        if (victim == null) return;

        ServerLevel here = (ServerLevel) victim.level();
        List<RoussetteEntity> near = here.getEntitiesOfClass(RoussetteEntity.class,
                new AABB(victim.blockPosition()).inflate(REFORM_RADIUS));

        if (near.isEmpty() && (due || server.getTickCount() % 20 == 0)) {
            reformNear(here, victim);
        }

        // 3. treated armour accumulates a dose while she is close
        if (!near.isEmpty()) tickTreatedArmour(victim, near.get(0));
    }

    /** She appears behind him, wetly. */
    private static void reformNear(ServerLevel level, Player victim) {
        Vec3 behind = victim.position()
                .subtract(victim.getLookAngle().normalize().scale(3.0))
                .add(0.0, 0.4, 0.0);

        // VERIFY: EntityType#create(ServerLevel, EntitySpawnReason) -- the second
        // argument was MobSpawnType before it was renamed EntitySpawnReason.
        RoussetteEntity shark = RoussetteMod.ROUSSETTE.get()
                .create(level, EntitySpawnReason.MOB_SUMMONED);
        if (shark == null) return;

        shark.moveTo(behind.x, behind.y, behind.z, victim.getYRot(), 0.0F);
        level.addFreshEntity(shark);
        shark.announceReform();
    }

    // ---------------------------------------------------------------- repellent
    /** Marker + counters live in the stack's custom data. */
    public static final String TAG_CHARGES = "RoussetteCharges";
    public static final String TAG_DOSE    = "RoussetteDose";

    public static boolean isTreated(ItemStack stack) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        return tag.contains(TAG_CHARGES) && tag.getInt(TAG_CHARGES) > 0;
    }

    public static void treat(ItemStack stack) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        tag.putInt(TAG_CHARGES, Repellent.ARMOUR_CHARGES);
        tag.putInt(TAG_DOSE, 0);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    /**
     * The dose builds only while she is genuinely close, and decays when she is
     * not. The fading lavender tint on the armour is the only readout -- there
     * is deliberately no UI.
     */
    private static void tickTreatedArmour(Player victim, RoussetteEntity shark) {
        if (shark.brain().isDown()) return;
        double dist = shark.distanceTo(victim);

        for (ItemStack stack : victim.getArmorSlots()) {
            if (stack.isEmpty() || !isTreated(stack)) continue;

            CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
            int charges = tag.getInt(TAG_CHARGES);
            int dose    = tag.getInt(TAG_DOSE);

            if (dist <= Repellent.DOSE_RANGE) {
                if (++dose >= Repellent.DOSE_TICKS) {
                    dose = 0;
                    charges--;
                    shark.knockOut();
                }
            } else if (dose > 0) {
                dose--;
            }

            tag.putInt(TAG_CHARGES, charges);
            tag.putInt(TAG_DOSE, dose);
            stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));

            // she visibly staggers as it builds, so he can read her
            shark.setDrowsy(charges > 0 ? (float) dose / Repellent.DOSE_TICKS : 0.0F);
            return;   // one piece at a time; they do not stack
        }
        shark.setDrowsy(0.0F);
    }

    /** How much lavender wash is left, 0.0-1.0. Drives the armour tint. */
    public static float tintOf(ItemStack stack) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        if (!tag.contains(TAG_CHARGES)) return 0.0F;
        return tag.getInt(TAG_CHARGES) / (float) Repellent.ARMOUR_CHARGES;
    }

    private RoussetteManager() {}
}
