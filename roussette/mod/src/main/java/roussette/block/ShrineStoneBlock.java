package roussette.block;

import net.minecraft.world.level.block.Block;

/**
 * The shaft lining. Bedrock-grade on purpose.
 *
 * <p>Spec §9: reinforced deepslate is <em>not</em> unbreakable — 55 hardness, no
 * associated tool, breaks in about a minute, drops nothing, and cannot be
 * obtained in survival at all. Doubling it up would not have helped either. So
 * the mod registers its own block with bedrock's actual numbers
 * ({@code strength(-1.0F, 3600000.0F)}, set in {@code RoussetteMod}).
 *
 * <p>It matters because the pool is 34 blocks deep with three air pockets in the
 * walls. If he can mine through the shaft, he can drain it, and draining it
 * removes the one place where she is faster than him — which is the entire
 * reason the shrines are underwater.
 */
public class ShrineStoneBlock extends Block {
    public ShrineStoneBlock(Properties properties) {
        super(properties);
    }
}
