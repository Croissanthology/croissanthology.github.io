package roussette;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.registries.DeferredRegister;

import java.util.function.Supplier;

import roussette.block.ShrineStoneBlock;
import roussette.entity.RoussetteEntity;
import roussette.item.RepellentCanItem;

/**
 * Mod entry point and every registry in one place.
 *
 * <p>Almost all of the actual behaviour lives in {@code roussette.core}, which
 * has no Minecraft imports and is covered by 105 tests. This class and the
 * handful beside it are the adapter: they translate between that tested brain
 * and whatever the current NeoForge API happens to look like.
 *
 * <p><b>Every line tagged {@code // VERIFY:} is an API call written without a
 * compiler.</b> The network policy in the authoring environment blocked
 * maven.neoforged.net, so none of this half of the mod has ever been compiled.
 * Grep for VERIFY to find every spot worth a second pair of eyes.
 */
@Mod(RoussetteMod.MOD_ID)
public class RoussetteMod {

    public static final String MOD_ID = "roussette";

    public static ResourceLocation id(String path) {
        // VERIFY: the ResourceLocation constructor was made private around 1.21;
        // fromNamespaceAndPath is the replacement.
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }

    // --- registries -----------------------------------------------------------
    public static final DeferredRegister.Blocks BLOCKS =
            DeferredRegister.createBlocks(MOD_ID);
    public static final DeferredRegister.Items ITEMS =
            DeferredRegister.createItems(MOD_ID);
    public static final DeferredRegister.Entities ENTITIES =
            DeferredRegister.createEntities(MOD_ID);
    public static final DeferredRegister<SoundEvent> SOUNDS =
            DeferredRegister.create(Registries.SOUND_EVENT, MOD_ID);

    // --- blocks ---------------------------------------------------------------
    /**
     * Bedrock-grade, on purpose. Spec §9: reinforced deepslate is NOT
     * unbreakable -- 55 hardness, breaks in about a minute, drops nothing, and
     * cannot be obtained in survival at all. So the mod brings its own.
     */
    public static final Supplier<Block> SHRINE_STONE = BLOCKS.register("shrine_stone",
            () -> new ShrineStoneBlock(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_PURPLE)
                    .strength(-1.0F, 3600000.0F)   // bedrock's own numbers
                    .noLootTable()));

    public static final Supplier<Item> SHRINE_STONE_ITEM = ITEMS.register("shrine_stone",
            // VERIFY: BlockItem still takes (Block, Item.Properties); in newer
            // versions Properties may need .setId(...) with a ResourceKey.
            () -> new BlockItem(SHRINE_STONE.get(), new Item.Properties()));

    // --- items ----------------------------------------------------------------
    public static final Supplier<Item> REPELLENT_CAN = ITEMS.register("repellent_can",
            () -> new RepellentCanItem(new Item.Properties().stacksTo(1)));

    // --- entity ---------------------------------------------------------------
    public static final Supplier<EntityType<RoussetteEntity>> ROUSSETTE =
            // VERIFY: DeferredRegister.Entities#registerEntityType(name, factory,
            // category, builderCustomiser). If this signature has moved, the
            // fallback is ENTITIES.register(name, () -> EntityType.Builder
            // .of(RoussetteEntity::new, MobCategory.CREATURE)....build(key)).
            ENTITIES.registerEntityType("roussette", RoussetteEntity::new,
                    MobCategory.CREATURE,
                    b -> b.sized(0.9F, 0.7F).clientTrackingRange(12).updateInterval(1));

    // --- sounds ---------------------------------------------------------------
    // Margot's own voice. These are the eight that cannot be substituted.
    public static final Supplier<SoundEvent> SND_CRY     = sound("cry");
    public static final Supplier<SoundEvent> SND_WAIL    = sound("wail");
    public static final Supplier<SoundEvent> SND_PURR    = sound("purr");
    public static final Supplier<SoundEvent> SND_PURREOW = sound("purreow");
    public static final Supplier<SoundEvent> SND_CHOMP   = sound("chomp");
    public static final Supplier<SoundEvent> SND_GNAW    = sound("gnaw");
    public static final Supplier<SoundEvent> SND_EEP     = sound("eep");
    public static final Supplier<SoundEvent> SND_HUFF    = sound("huff");
    // The wet ones. sounds.json points these at vanilla slime/splash samples,
    // so no recording is needed -- see assets/roussette/sounds.json.
    public static final Supplier<SoundEvent> SND_SQUELCH = sound("squelch");
    public static final Supplier<SoundEvent> SND_REFORM  = sound("reform");

    private static Supplier<SoundEvent> sound(String name) {
        // VERIFY: createVariableRangeEvent is the usual factory for mod sounds.
        return SOUNDS.register(name, () -> SoundEvent.createVariableRangeEvent(id(name)));
    }

    // --- wiring ---------------------------------------------------------------
    public RoussetteMod(IEventBus modBus) {
        BLOCKS.register(modBus);
        ITEMS.register(modBus);
        ENTITIES.register(modBus);
        SOUNDS.register(modBus);
        modBus.addListener(this::registerAttributes);
    }

    private void registerAttributes(EntityAttributeCreationEvent event) {
        event.put(ROUSSETTE.get(), RoussetteEntity.attributes().build());
    }
}
