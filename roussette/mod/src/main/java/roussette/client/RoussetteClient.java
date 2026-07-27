package roussette.client;

import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

import roussette.RoussetteMod;

/**
 * Client-only wiring: the model layer and the renderer.
 *
 * <p>VERIFY: both of these fire on the <em>mod</em> event bus, client side only.
 * If the bus argument name has changed, this is the annotation to adjust.
 */
@EventBusSubscriber(modid = RoussetteMod.MOD_ID, value = Dist.CLIENT,
                    bus = EventBusSubscriber.Bus.MOD)
public final class RoussetteClient {

    @SubscribeEvent
    public static void registerLayers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(RoussetteRenderer.LAYER, RoussetteModel::createBodyLayer);
    }

    @SubscribeEvent
    public static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(RoussetteMod.ROUSSETTE.get(), RoussetteRenderer::new);
    }

    private RoussetteClient() {}
}
