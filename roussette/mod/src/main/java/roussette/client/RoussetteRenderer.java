package roussette.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.ResourceLocation;

import roussette.RoussetteMod;
import roussette.entity.RoussetteEntity;

/** Draws her. */
public class RoussetteRenderer extends MobRenderer<RoussetteEntity, RoussetteModel> {

    public static final ModelLayerLocation LAYER =
            new ModelLayerLocation(RoussetteMod.id("roussette"), "main");

    private static final ResourceLocation TEXTURE =
            RoussetteMod.id("textures/entity/roussette.png");

    public RoussetteRenderer(EntityRendererProvider.Context ctx) {
        super(ctx, new RoussetteModel(ctx.bakeLayer(LAYER)), 0.45F);
    }

    @Override
    public ResourceLocation getTextureLocation(RoussetteEntity entity) {
        return TEXTURE;
    }

    @Override
    protected void scale(RoussetteEntity entity, PoseStack pose, float partialTicks) {
        // Geometry is in Minecraft pixels; models draw at 1/16 scale.
        pose.scale(1.0F, 1.0F, 1.0F);

        // As a repellent dose builds she visibly sags, so he can read her like
        // someone about to fall asleep. Spec §6.
        float droop = entity.drowsy();
        if (droop > 0.0F) {
            pose.translate(0.0F, droop * 0.10F, 0.0F);
            pose.mulPose(com.mojang.math.Axis.ZP.rotation(droop * 0.28F));
        }
    }
}
