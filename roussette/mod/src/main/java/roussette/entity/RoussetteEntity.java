package roussette.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.phys.Vec3;

import roussette.RoussetteMod;
import roussette.core.Ports;
import roussette.core.Roussette;
import roussette.save.RoussetteSaveData;

import java.util.Random;

/**
 * The catshark. This class is deliberately thin: it implements
 * {@link Ports.Sensors} and {@link Ports.Actuators} against the real world and
 * ticks {@link Roussette} once per entity tick. Every timing, distance and
 * decision lives in the tested core, not here.
 *
 * <p>She has no AI goals at all. Vanilla pathfinding is not used, because she
 * does not travel -- she re-forms. See {@code RoussetteManager}.
 */
public class RoussetteEntity extends Mob implements Ports.Sensors, Ports.Actuators {

    /** 0 round, 1 slit, 2 X. Synced so the client can draw her face. */
    private static final EntityDataAccessor<Integer> PUPIL =
            SynchedEntityData.defineId(RoussetteEntity.class, EntityDataSerializers.INT);
    /** Drives the stagger animation as a repellent dose builds, 0.0 - 1.0. */
    private static final EntityDataAccessor<Float> DROWSY =
            SynchedEntityData.defineId(RoussetteEntity.class, EntityDataSerializers.FLOAT);

    private final Roussette brain = new Roussette();
    private final Random rng = new Random();
    private Player victim;
    private int reformDelay;

    public RoussetteEntity(EntityType<? extends RoussetteEntity> type, Level level) {
        super(type, level);
        // She is not a fish out of water: no drying damage, ever. Spec §9.
        this.setPathfindingMalus(net.minecraft.world.level.pathfinder.PathType.WATER, 0.0F);
        this.brain.seed(level.getRandom().nextLong() | 1L);
    }

    public static AttributeSupplier.Builder attributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, Roussette.MAX_HEALTH)   // 16 = 8 hearts
                .add(Attributes.MOVEMENT_SPEED, 0.25D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.0D)
                .add(Attributes.FOLLOW_RANGE, 128.0D);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(PUPIL, 0);
        builder.define(DROWSY, 0.0F);
    }

    /** She never fights mobs and mobs never fight her. Margot's correction. */
    @Override
    protected void registerGoals() { /* intentionally empty */ }

    @Override
    public boolean canBeLeashed() { return false; }

    @Override
    public boolean removeWhenFarAway(double distance) { return false; }

    public int pupilState()  { return this.entityData.get(PUPIL); }
    public float drowsy()    { return this.entityData.get(DROWSY); }
    public void setDrowsy(float f) { this.entityData.set(DROWSY, f); }
    public Roussette brain() { return brain; }

    // ------------------------------------------------------------------ tick
    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide) return;

        this.victim = RoussetteSaveData.get((ServerLevel) this.level()).findVictim(this.level());
        if (this.victim != null && this.victim.isSpectator()) this.victim = null;

        brain.tick(this, this);
    }

    /** Fire and lava still work, but so does everything else now. */
    @Override
    public boolean hurt(DamageSource source, float amount) {
        boolean applied = super.hurt(source, amount);
        // VERIFY: getEntity() vs getDirectEntity() -- we want the swinger.
        if (applied && source.getEntity() instanceof Player && this.isAlive()) {
            brain.onHit(this);
        }
        return applied;
    }

    /** Right-click with an empty hand is a headpat. Vanilla datapacks cannot
     *  detect this; a mod can, which is the whole reason for spec §9's note. */
    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (player.getItemInHand(hand).isEmpty()) {
            if (!this.level().isClientSide) brain.onHeadpat(this);
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }

    /** A repellent spray, or a full dose off treated armour. */
    public void knockOut() { brain.onRepellent(this); }

    @Override
    public void die(DamageSource source) {
        brain.onDefeated(this);
        super.die(source);
        if (this.level() instanceof ServerLevel server) {
            RoussetteSaveData.get(server).scheduleReform(Roussette.REFORM_DELAY);
        }
    }

    /** Called by the manager on a freshly spawned replacement. */
    public void announceReform() { brain.onReform(this); }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("Pupil", pupilState());
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.entityData.set(PUPIL, tag.getInt("Pupil"));
    }

    // =================================================================== SENSORS
    @Override public boolean victimPresent()  { return victim != null; }
    @Override public double  victimDistance() { return victim == null ? 1e9 : this.distanceTo(victim); }
    @Override public boolean inWater()        { return this.isInWater(); }
    @Override public boolean onFire()         { return this.isOnFire(); }
    @Override public boolean victimSneaking() { return victim != null && victim.isShiftKeyDown(); }
    @Override public int     victimHealth()   { return victim == null ? 20 : (int) Math.ceil(victim.getHealth()); }

    @Override
    public int lightLevel() {
        return this.level().getMaxLocalRawBrightness(this.blockPosition());
    }

    @Override
    public boolean passable(double up, double forward) {
        Vec3 look = this.getLookAngle().normalize();
        Vec3 p = this.position().add(look.scale(forward)).add(0.0, up, 0.0);
        BlockPos pos = BlockPos.containing(p);
        return this.level().getBlockState(pos).getCollisionShape(this.level(), pos).isEmpty();
    }

    @Override
    public boolean doorAhead() {
        Vec3 look = this.getLookAngle().normalize();
        for (double d = 0.5; d <= 2.0; d += 0.5) {
            Vec3 p = this.position().add(look.scale(d));
            BlockPos pos = BlockPos.containing(p);
            if (this.level().getBlockState(pos).getBlock() instanceof DoorBlock) return true;
        }
        return false;
    }

    // ================================================================= ACTUATORS
    @Override
    public void faceVictim() {
        if (victim == null) return;
        double dx = victim.getX() - this.getX(), dz = victim.getZ() - this.getZ();
        float yaw = (float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0);
        this.setYRot(yaw);
        this.yBodyRot = yaw;
        this.yHeadRot = yaw;
    }

    @Override public void levelPitch() { this.setXRot(0.0F); }

    @Override
    public void moveForward(double blocks) {
        Vec3 look = this.getLookAngle().normalize();
        Vec3 step = new Vec3(look.x, this.isInWater() ? look.y * 0.6 : 0.0, look.z).scale(blocks);
        this.setDeltaMovement(this.getDeltaMovement().add(step));
        if (this.isInWater()) {
            // enough lift to stop her sinking to the floor of a 34-block shaft
            this.setDeltaMovement(this.getDeltaMovement().add(0.0, 0.012, 0.0));
        }
        this.hasImpulse = true;
    }

    @Override
    public void stepUp(double up, double forward) {
        Vec3 look = this.getLookAngle().normalize();
        this.setDeltaMovement(this.getDeltaMovement()
                .add(look.x * forward, up * 0.42, look.z * forward));
        this.hasImpulse = true;
    }

    @Override
    public void spinYaw(double degrees) {
        this.setYRot((float) (this.getYRot() + degrees));
    }

    @Override
    public void launchAwayFromVictim(double horizontal, double vertical) {
        Vec3 away = victim == null
                ? new Vec3(rng.nextDouble() - 0.5, 0, rng.nextDouble() - 0.5)
                : this.position().subtract(victim.position());
        if (away.lengthSqr() < 1.0e-4) away = new Vec3(1, 0, 0);
        away = away.normalize();
        // Enormous and slightly ridiculous, every single time, forever.
        this.setDeltaMovement(away.x * horizontal * 2.6, vertical * 1.35, away.z * horizontal * 2.6);
        this.hurtMarked = true;
        this.hasImpulse = true;
    }

    @Override
    public void bounce(double retain) {
        Vec3 v = this.getDeltaMovement();
        double vx = v.x, vy = v.y, vz = v.z;
        // Reflect off whatever she actually hit. horizontalCollision and
        // verticalCollision are set by the movement code on the tick of impact.
        if (this.horizontalCollision) { vx = -vx; vz = -vz; }
        if (this.verticalCollision)   { vy = -vy; }
        if (!this.horizontalCollision && !this.verticalCollision) { vx = -vx; vz = -vz; }
        this.setDeltaMovement(vx * retain, Math.max(vy * retain, 0.22), vz * retain);
        this.hurtMarked = true;
        this.hasImpulse = true;
    }

    @Override
    public void teleportToVictim() {
        if (victim == null) return;
        Vec3 behind = victim.position().subtract(victim.getLookAngle().normalize().scale(2.0));
        // VERIFY: teleportTo(ServerLevel, x, y, z, ...) exists for cross-dimension
        // moves; the manager handles the dimension case, so this is same-level.
        this.teleportTo(behind.x, behind.y + 0.25, behind.z);
        this.setDeltaMovement(Vec3.ZERO);
    }

    @Override
    public void rideVictimFeet() {
        if (victim == null) return;
        Vec3 feet = victim.position();
        this.setPos(feet.x, feet.y + 0.05, feet.z);
        this.setDeltaMovement(Vec3.ZERO);
        this.fallDistance = 0.0F;
    }

    @Override
    public void sound(String event) {
        SoundEvent se = switch (event) {
            case "cry"     -> RoussetteMod.SND_CRY.get();
            case "wail"    -> RoussetteMod.SND_WAIL.get();
            case "purr"    -> RoussetteMod.SND_PURR.get();
            case "purreow" -> RoussetteMod.SND_PURREOW.get();
            case "chomp"   -> RoussetteMod.SND_CHOMP.get();
            case "gnaw"    -> RoussetteMod.SND_GNAW.get();
            case "eep"     -> RoussetteMod.SND_EEP.get();
            case "huff"    -> RoussetteMod.SND_HUFF.get();
            case "squelch" -> RoussetteMod.SND_SQUELCH.get();
            case "reform"  -> RoussetteMod.SND_REFORM.get();
            default        -> null;
        };
        if (se == null) return;
        float pitch = 0.92F + rng.nextFloat() * 0.16F;
        this.level().playSound(null, this.getX(), this.getY(), this.getZ(),
                se, SoundSource.HOSTILE, 1.0F, pitch);
    }

    @Override
    public void particles(String kind, int count) {
        if (!(this.level() instanceof ServerLevel server)) return;
        ParticleOptions p = switch (kind) {
            case "heart"      -> ParticleTypes.HEART;
            case "crit"       -> ParticleTypes.CRIT;
            case "splash"     -> ParticleTypes.SPLASH;
            case "bubble"     -> ParticleTypes.BUBBLE;
            case "item_slime" -> ParticleTypes.ITEM_SLIME;
            default           -> ParticleTypes.SPLASH;
        };
        server.sendParticles(p, this.getX(), this.getY() + 0.4, this.getZ(),
                count, 0.35, 0.3, 0.35, 0.02);
    }

    @Override
    public void slowVictim(int amplifier, int ticks) {
        if (victim == null) return;
        // VERIFY: MobEffects entries are Holder<MobEffect> in 1.21+, and the
        // constant may be MOVEMENT_SLOWDOWN or SLOWNESS depending on version.
        victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, ticks, amplifier,
                false, false, true));
    }

    @Override
    public void clearVictimSlow() {
        if (victim != null) victim.removeEffect(MobEffects.MOVEMENT_SLOWDOWN);
    }

    /**
     * Half a heart, and never below 3.5 hearts. The floor is enforced in the
     * core, but it is re-checked here: rule 3 is the one rule that must not fail
     * even if somebody edits the brain badly.
     */
    @Override
    public void damageVictim(double halfHearts) {
        if (victim == null || victim.isCreative()) return;
        if (victim.getHealth() < Roussette.BITE_FLOOR) return;
        victim.hurt(this.damageSources().mobAttack(this), (float) halfHearts);
    }

    @Override
    public void setGlowing(boolean on) {
        // VERIFY: setGlowingTag is the entity-level flag the outline reads.
        if (this.hasGlowingTag() != on) this.setGlowingTag(on);
    }

    @Override
    public void setPupil(Ports.Pupil pupil) {
        this.entityData.set(PUPIL, switch (pupil) {
            case ROUND -> 0;
            case SLIT  -> 1;
            case X     -> 2;
        });
    }

    /** Used by the tint/stagger logic so he can read her like someone about to
     *  fall asleep. Not part of the brain. */
    public LivingEntity victimEntity() { return victim; }
}
