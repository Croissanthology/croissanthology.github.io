package roussette.client;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;

import roussette.core.Geometry;
import roussette.entity.RoussetteEntity;

/**
 * Her body, built straight from {@link Geometry#PARTS} — the same 20 boxes the
 * core's proportion tests check, so the model and the tested geometry cannot
 * drift apart.
 *
 * <p><b>Coordinate flip.</b> {@code Geometry} uses +X toward the nose and +Y up,
 * with the origin at her body centre. Minecraft model space has +Y pointing
 * <em>down</em>. So every pivot's Y is negated, and rotations about X and Z flip
 * sign with it while Y rotations do not.
 *
 * <p><b>Texture layout.</b> The sheet is five large flat-colour regions plus
 * three eye tiles. Each cube points at whichever region matches its palette
 * colour, so every face comes out the right flat colour with the rosettes
 * scattered over the hide region.
 *
 * <p><b>VERIFY — this is the highest-risk file in the mod.</b> Minecraft moved
 * entity rendering to a render-state pipeline
 * ({@code EntityModel<S extends EntityRenderState>}, with {@code setupAnim(S)}
 * instead of taking the entity). If 26.2 uses that pipeline, this class needs a
 * {@code RoussetteRenderState} carrying pupil/drowsy/age and the signatures
 * below change accordingly. The geometry itself does not.
 */
public class RoussetteModel extends EntityModel<RoussetteEntity> {

    /** Model-space UV size. The PNG is 4x this for detail. */
    public static final int TEX_W = 128, TEX_H = 128;

    /** Region origins on the sheet, keyed by palette colour. */
    private static int[] regionFor(int colour) {
        return switch (colour) {
            case Geometry.LAV      -> new int[]{0, 0};
            case Geometry.LAV_DEEP -> new int[]{64, 0};
            case Geometry.BELLY    -> new int[]{64, 32};
            case Geometry.BLUSH    -> new int[]{0, 64};
            case Geometry.DARK     -> new int[]{32, 64};
            default                -> new int[]{0, 0};
        };
    }

    private final ModelPart root;
    private final ModelPart tail, earL, earR, pectL, pectR;
    private final ModelPart eyeRoundL, eyeRoundR, eyeSlitL, eyeSlitR, eyeKoL, eyeKoR, tongue;

    public RoussetteModel(ModelPart root) {
        this.root = root;
        this.tail  = root.getChild("tailMid");
        this.earL  = root.getChild("earL");
        this.earR  = root.getChild("earR");
        this.pectL = root.getChild("pectL");
        this.pectR = root.getChild("pectR");
        this.eyeRoundL = root.getChild("eye_round_l");
        this.eyeRoundR = root.getChild("eye_round_r");
        this.eyeSlitL  = root.getChild("eye_slit_l");
        this.eyeSlitR  = root.getChild("eye_slit_r");
        this.eyeKoL    = root.getChild("eye_ko_l");
        this.eyeKoR    = root.getChild("eye_ko_r");
        this.tongue    = root.getChild("tongue");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();

        for (Geometry.Box b : Geometry.PARTS) {
            int[] r = regionFor(b.colour());
            root.addOrReplaceChild(b.name(),
                    CubeListBuilder.create()
                            .texOffs(r[0], r[1])
                            .addBox((float) (-b.sx() / 2), (float) (-b.sy() / 2), (float) (-b.sz() / 2),
                                    (float) b.sx(), (float) b.sy(), (float) b.sz()),
                    PartPose.offsetAndRotation(
                            (float) b.px(), (float) -b.py(), (float) b.pz(),
                            (float) -b.rx(), (float) b.ry(), (float) -b.rz()));
        }

        // Eyes: flat quads, deliberately untextured hide so the expression stays
        // legible from across a room. Three states, one visible at a time.
        addEye(root, "eye_round_l", 64, 64, 1);
        addEye(root, "eye_round_r", 64, 64, -1);
        addEye(root, "eye_slit_l",  80, 64, 1);
        addEye(root, "eye_slit_r",  80, 64, -1);
        addEye(root, "eye_ko_l",    96, 64, 1);
        addEye(root, "eye_ko_r",    96, 64, -1);

        // Mouth, and the tongue that lolls out when she is knocked out.
        root.addOrReplaceChild("mouth",
                CubeListBuilder.create().texOffs(112, 80)
                        .addBox(-0.3F, -0.4F, -2.1F, 0.6F, 0.8F, 4.2F),
                PartPose.offset(9.9F, 3.6F, 0.0F));
        root.addOrReplaceChild("tongue",
                CubeListBuilder.create().texOffs(112, 88)
                        .addBox(-0.9F, -0.25F, -1.2F, 1.8F, 0.5F, 2.4F),
                PartPose.offsetAndRotation(10.2F, 4.5F, 0.0F, 0.0F, 0.0F, -0.22F));

        return LayerDefinition.create(mesh, TEX_W, TEX_H);
    }

    private static void addEye(PartDefinition root, String name, int u, int v, int side) {
        root.addOrReplaceChild(name,
                CubeListBuilder.create().texOffs(u, v)
                        .addBox(-2.3F, -2.3F, -0.25F, 4.6F, 4.6F, 0.5F),
                PartPose.offset((float) Geometry.EYE_X,
                        (float) -Geometry.EYE_Y,
                        (float) (Geometry.EYE_Z * side)));
    }

    /**
     * @param pupil  0 round, 1 slit, 2 knocked out
     * @param swim   how hard the tail is working, 0..1
     * @param age    ticks, for idle motion
     */
    public void setState(int pupil, float swim, float age) {
        eyeRoundL.visible = eyeRoundR.visible = pupil == 0;
        eyeSlitL.visible  = eyeSlitR.visible  = pupil == 1;
        eyeKoL.visible    = eyeKoR.visible    = pupil == 2;
        tongue.visible    = pupil == 2;

        float beat = 0.5F + swim * 2.6F;
        tail.yRot  = (float) Math.sin(age * 0.35F * beat) * (0.30F + swim * 0.55F);
        pectL.zRot = (float) (0.14 + Math.sin(age * 0.18F) * 0.16F);
        pectR.zRot = (float) (0.14 - Math.sin(age * 0.18F) * 0.16F);
        // ears twitch, because they are the whole point
        earL.zRot = (float) (0.16 + Math.sin(age * 0.11F) * 0.07F);
        earR.zRot = (float) (0.16 - Math.sin(age * 0.13F) * 0.07F);
    }

    @Override
    public void setupAnim(RoussetteEntity entity, float limbSwing, float limbSwingAmount,
                          float ageInTicks, float netHeadYaw, float headPitch) {
        float swim = Math.min(1.0F, (float) entity.getDeltaMovement().horizontalDistance() * 6.0F);
        setState(entity.pupilState(), swim, ageInTicks);
    }

    @Override
    public void renderToBuffer(PoseStack pose, VertexConsumer buffer, int light,
                              int overlay, int colour) {
        root.render(pose, buffer, light, overlay, colour);
    }

    public ModelPart root() { return root; }
}
