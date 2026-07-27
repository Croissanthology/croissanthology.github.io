package roussette.item;

import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.AnvilUpdateEvent;

import roussette.RoussetteManager;
import roussette.RoussetteMod;
import roussette.core.Repellent;
import roussette.entity.RoussetteEntity;

import java.util.List;

/**
 * Shark repellent.
 *
 * <p>Ten sprays, each dropping her for a flat ten seconds — the same every time,
 * forever. There is deliberately no tolerance mechanic: an earlier design made
 * each knockout harder than the last, which meant the player already being
 * hunted was the one absorbing the difficulty curve. All the scarcity lives in
 * the supply of cans instead, and cans do not refill.
 *
 * <p>The sprays are the item's durability, so the vanilla damage bar is the
 * meter and no custom UI is needed.
 */
public class RepellentCanItem extends Item {

    /** How far a spray reaches. */
    public static final double SPRAY_RANGE = 7.0;

    public RepellentCanItem(Properties properties) {
        super(properties.durability(Repellent.SPRAYS_PER_CAN));
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResult.SUCCESS;

        List<RoussetteEntity> hit = level.getEntitiesOfClass(RoussetteEntity.class,
                new AABB(player.blockPosition()).inflate(SPRAY_RANGE));

        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                RoussetteMod.SND_SQUELCH.get(), SoundSource.PLAYERS, 0.7F, 1.6F);

        if (hit.isEmpty()) return InteractionResult.CONSUME;

        for (RoussetteEntity shark : hit) shark.knockOut();

        // VERIFY: hurtAndBreak(int, LivingEntity, EquipmentSlot) signature has
        // moved around; some versions take a ServerLevel first.
        stack.hurtAndBreak(1, player, net.minecraft.world.entity.EquipmentSlot.MAINHAND);
        return InteractionResult.CONSUME;
    }

    /**
     * A whole can plus an armour piece at an anvil gives treated armour: six
     * automatic knockouts, each costing 45 seconds of her being close. It is a
     * <em>sidegrade</em>, not an upgrade — ten manual escapes traded for six
     * that need no reaction time. With cans this scarce, a recipe that
     * multiplied doses would quietly undo the point of them running out.
     */
    @EventBusSubscriber(modid = RoussetteMod.MOD_ID)
    public static final class Anvil {
        @SubscribeEvent
        public static void onAnvil(AnvilUpdateEvent event) {
            ItemStack left = event.getLeft();
            ItemStack right = event.getRight();
            if (!(right.getItem() instanceof RepellentCanItem)) return;
            if (left.isEmpty() || !left.isDamageableItem()) return;
            // must be a full can
            if (right.getDamageValue() != 0) return;
            if (RoussetteManager.isTreated(left)) return;

            ItemStack out = left.copy();
            RoussetteManager.treat(out);
            event.setOutput(out);
            event.setCost(5);
            event.setMaterialCost(1);
        }

        private Anvil() {}
    }
}
