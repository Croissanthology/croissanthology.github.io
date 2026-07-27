package roussette.core;

/** The seam between pure behaviour and Minecraft.
 *
 *  Everything in this package is deliberately free of Minecraft imports so it
 *  can be compiled and tested without the game. The adapter layer implements
 *  these two interfaces against whatever the current API actually looks like,
 *  and the brain never needs to know. */
public final class Ports {
    private Ports() {}

    public enum Pupil { ROUND, SLIT, X }

    /** Everything she can perceive. */
    public interface Sensors {
        boolean victimPresent();
        double  victimDistance();
        boolean inWater();
        /** Is the space at local offset (up, forward) enterable? */
        boolean passable(double up, double forward);
        boolean doorAhead();
        boolean onFire();
        int     lightLevel();
        boolean victimSneaking();
        /** Victim health in half-hearts, 20 = full. */
        int     victimHealth();
    }

    /** Everything she can do. */
    public interface Actuators {
        void faceVictim();
        void levelPitch();
        void moveForward(double blocks);
        void stepUp(double up, double forward);
        void spinYaw(double degrees);
        void launchAwayFromVictim(double horizontal, double vertical);
        /** Reflect her current velocity off the surface she just hit, keeping
         *  {@code retain} of the speed. This is the ricochet -- she must come
         *  off walls at a real angle, not just stop against them. */
        void bounce(double retain);
        void teleportToVictim();
        void rideVictimFeet();
        void sound(String event);
        void particles(String kind, int count);
        void slowVictim(int amplifier, int ticks);
        void clearVictimSlow();
        void damageVictim(double halfHearts);
        void setGlowing(boolean on);
        void setPupil(Pupil pupil);
    }
}
