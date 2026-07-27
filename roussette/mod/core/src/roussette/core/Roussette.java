package roussette.core;

import roussette.core.Ports.Actuators;
import roussette.core.Ports.Pupil;
import roussette.core.Ports.Sensors;

/** The brain. Ported verbatim from the tuned datapack -- every constant below
 *  was arrived at by playing with it, so change them reluctantly. */
public final class Roussette {

    public enum State { HUNT, LATCHED, FLUNG, WEDGED, PATTED, KO, SLEEPING }

    // --- movement -----------------------------------------------------------
    /** Load-bearing: descending doubles her speed and halves his. This single
     *  pair of numbers is the entire reason the temples are underwater. */
    public static final double SPEED_LAND  = 0.15;
    public static final double SPEED_WATER = 0.32;
    public static final double STEP_UP     = 0.95;
    public static final double CLOSE_ENOUGH = 1.4;
    public static final double LEASH        = 64.0;

    // --- timings, in ticks --------------------------------------------------
    public static final int KO_TICKS       = 200;   // 10s, one repellent spray
    public static final int KO_PAT_BONUS   = 60;    // patting her while down
    public static final int PAT_TICKS      = 30;
    public static final int FLUNG_TICKS    = 26;
    public static final int LATCH_TICKS    = 220;
    public static final int LATCH_COOLDOWN = 100;
    public static final int WEDGE_COOLDOWN = 200;
    public static final int ANGRY_TICKS    = 80;    // then her eyes go round again
    public static final int WAKE_RAGE      = 100;   // hit her while down -> faster
    public static final double RAGE_BONUS  = 1.6;
    public static final int NIBBLE_PERIOD  = 24;
    public static final int GLOW_LIGHT     = 6;
    public static final int BITE_FLOOR     = 7;     // never bite below 3.5 hearts
    public static final double BITE        = 1.0;

    // --- mortality ----------------------------------------------------------
    /** She can be defeated by any damage, and she simply comes back.
     *
     *  Eight hearts: enough that a casual whack launches her rather than kills
     *  her, so rule 2's core loop survives, but low enough that killing her is a
     *  normal thing to do rather than a project. That works because the return
     *  is so fast -- she is back in a second and a half, so a kill was never
     *  going to be worth much anyway. Being killed is just a very long fling. */
    public static final int MAX_HEALTH   = 16;      // half-hearts, i.e. 8 hearts
    public static final int REFORM_DELAY = 30;      // ticks between defeat and return

    // --- ricochet -----------------------------------------------------------
    /** Hitting a wall has to *bounce* her, not stop her. Fraction of speed kept
     *  per impact, decaying so she eventually settles instead of pinballing
     *  forever, plus the airtime a good carom earns her. */
    public static final double BOUNCE_RETAIN = 0.82;
    public static final double BOUNCE_DECAY  = 0.13;
    public static final double BOUNCE_FLOOR  = 0.30;
    public static final int BOUNCE_DEBOUNCE  = 7;
    public static final int BOUNCE_EXTENSION = 8;
    public static final int MAX_BOUNCES      = 4;

    // --- bedtime --------------------------------------------------------------
    /** When he gets into a bed she stops hunting, ports to his side, and flumps
     *  over like something shot — except her eyes are shut and she is snoring.
     *
     *  This is the only state she enters voluntarily and the only one where she
     *  is harmless on purpose rather than by accident. It does not soften her:
     *  she is on his pillow, and she is awake again at dawn. */
    public static final int SNORE_PERIOD = 70;   // ~3.5s between noises
    public static final int SNORT_ONE_IN = 4;    // some of them are snorts

    private State state = State.HUNT;
    private int timer, latchCooldown, wedgeCooldown, angry, rage, clock;
    private int wallDebounce, bounces;

    public int bounces() { return bounces; }

    public State state()      { return state; }
    public boolean isDown()   { return state == State.KO; }
    public int  timer()       { return timer; }

    // ------------------------------------------------------------------ tick
    public void tick(Sensors s, Actuators a) {
        clock++;
        if (latchCooldown > 0) latchCooldown--;
        if (wedgeCooldown > 0) wedgeCooldown--;
        if (wallDebounce  > 0) wallDebounce--;
        if (rage > 0) rage--;
        if (angry > 0 && --angry == 0 && state != State.KO) a.setPupil(Pupil.ROUND);

        a.setGlowing(s.lightLevel() <= GLOW_LIGHT);

        // He got into a bed. Whatever she was doing, she is going to come and
        // sleep on him -- unless she is already out cold, or still in the air,
        // in which case she finishes that first.
        if (s.victimSleeping() && s.victimPresent()
                && state != State.KO && state != State.FLUNG && state != State.SLEEPING) {
            enterSleep(a);
        }

        switch (state) {
            case KO       -> koTick(a);
            case SLEEPING -> sleepTick(s, a);
            case PATTED   -> patTick(a);
            case FLUNG    -> flungTick(s, a);
            case WEDGED   -> wedgeTick(s, a);
            case LATCHED  -> latchTick(s, a);
            case HUNT     -> huntTick(s, a);
        }
    }

    // ---------------------------------------------------------------- events
    /** Any player melee, from the victim or from a bystander.
     *
     *  Always a fling -- that is the core loop and it stays fun forever. Damage
     *  still lands on top: enough of it defeats her (see MAX_HEALTH) and she
     *  re-forms a moment later, which is the same thing as a very long fling. */
    public void onHit(Actuators a) {
        boolean wasDown = state == State.KO;
        endLatch(a);
        state = State.FLUNG;
        bounces = 0;
        timer = FLUNG_TICKS;
        angry = ANGRY_TICKS;
        latchCooldown = 80;
        a.setPupil(Pupil.SLIT);
        a.launchAwayFromVictim(1.0, 0.78);
        a.sound("cry");
        a.particles("crit", 18);
        // Kicking a helpless thing wakes her up furious. This is deliberate.
        if (wasDown) { rage = WAKE_RAGE; a.sound("wail"); }
    }

    /** Right-click, or crouching nearby. */
    public void onHeadpat(Actuators a) {
        if (state == State.KO) {          // comfortable. stays down longer.
            timer += KO_PAT_BONUS;
            a.sound("purr");
            a.particles("heart", 2);
            return;
        }
        if (state == State.SLEEPING) {    // purrs in her sleep, does not wake
            a.sound("purr");
            a.particles("heart", 3);
            return;
        }
        endLatch(a);
        state = State.PATTED;
        timer = PAT_TICKS;
        a.setPupil(Pupil.ROUND);
        angry = 0;
        a.sound("purr");
    }

    /** A spray from a can, or a full dose from treated armour. */
    public void onRepellent(Actuators a) {
        endLatch(a);
        state = State.KO;
        timer = KO_TICKS;
        rage = 0;
        a.setPupil(Pupil.X);
        a.sound("squelch");
        a.particles("splash", 20);
    }

    /** Her health reached zero. Cosmetically enormous, mechanically just a
     *  detour: the adapter removes her and brings her back REFORM_DELAY ticks
     *  later through onReform. She cannot be gotten rid of, only postponed. */
    public void onDefeated(Actuators a) {
        endLatch(a);
        state = State.FLUNG;
        timer = 0;
        a.sound("wail");
        a.particles("item_slime", 40);
    }

    /** She re-forms near him. Being defeated, changing dimension, teleporting
     *  and burning alive are all the same event to this method. */
    public void onReform(Actuators a) {
        state = State.HUNT;
        timer = latchCooldown = wedgeCooldown = angry = rage = bounces = 0;
        a.setPupil(Pupil.ROUND);
        a.sound("reform");
        a.particles("splash", 26);
    }

    // ---------------------------------------------------------------- states
    private void koTick(Actuators a) {
        if (--timer <= 0) { state = State.HUNT; a.setPupil(Pupil.ROUND); return; }
        a.spinYaw(2);
        if (timer % 20 == 0) a.particles("bubble", 3);
    }

    /** She ports to his side and goes down like a dropped bag of sand. */
    private void enterSleep(Actuators a) {
        endLatch(a);
        state = State.SLEEPING;
        timer = 0;
        angry = 0;
        rage = 0;
        bounces = 0;
        a.setPupil(Pupil.CLOSED);
        a.flumpBeside();
        a.sound("huff");            // the settling-down noise, reused
        a.particles("heart", 2);
    }

    private void sleepTick(Sensors s, Actuators a) {
        if (!s.victimSleeping()) {  // morning
            state = State.HUNT;
            a.setPupil(Pupil.ROUND);
            a.sound("huff");
            a.particles("splash", 4);
            return;
        }
        a.flumpBeside();            // stay put even if the bed is jostled
        if (clock % SNORE_PERIOD == 0) {
            a.sound(roll(SNORT_ONE_IN) ? "snort" : "snore");
            a.particles("bubble", 1);
        }
    }

    private void patTick(Actuators a) {
        if (--timer <= 0) { state = State.HUNT; return; }
        a.spinYaw(16);
        a.particles("heart", 1);
        if (timer == 20) a.sound("purreow");
        if (timer == 8)  a.sound("purr");
    }

    private void flungTick(Sensors s, Actuators a) {
        if (--timer <= 0) {
            state = State.HUNT;
            a.sound("huff");                 // "Ok. Ok. anyway." -- and back to work
            return;
        }
        a.spinYaw(47);                       // cosmetic; travel is real velocity
        a.particles("splash", 2);
        if (timer == 24 || timer == 16 || timer == 8) a.sound("wail");

        // The ricochet. She has to come off the wall at an angle and keep going,
        // and each carom is worth more of the joke than the last -- up to a
        // point, after which she runs out of bounce and settles.
        if (!s.passable(0.2, 0.7) && wallDebounce == 0) {
            wallDebounce = BOUNCE_DEBOUNCE;
            bounces++;
            a.bounce(Math.max(BOUNCE_FLOOR, BOUNCE_RETAIN - (bounces - 1) * BOUNCE_DECAY));
            a.sound(bounces == 1 ? "eep" : "squelch");
            a.particles("item_slime", 10 + bounces * 4);
            if (bounces <= MAX_BOUNCES) timer += BOUNCE_EXTENSION;
        }
    }

    private void wedgeTick(Sensors s, Actuators a) {
        a.spinYaw(9);
        a.particles("splash", 2);
        if (clock % 20 == 0) a.sound("wail");
        if (!s.victimPresent() || s.victimDistance() > 7.0) {
            state = State.HUNT;
            wedgeCooldown = WEDGE_COOLDOWN;
            a.sound("squelch");
            a.particles("item_slime", 22);
        }
    }

    private void latchTick(Sensors s, Actuators a) {
        if (--timer <= 0) { endLatch(a); return; }
        a.rideVictimFeet();
        a.slowVictim(1, 40);
        if (clock % NIBBLE_PERIOD == 0) {
            a.sound("gnaw");
            if (s.victimHealth() >= BITE_FLOOR) a.damageVictim(BITE);
        }
    }

    private void huntTick(Sensors s, Actuators a) {
        if (!s.victimPresent()) return;
        a.faceVictim();
        a.levelPitch();

        if (s.victimDistance() > LEASH) { a.teleportToVictim(); a.sound("reform"); return; }

        if (s.victimDistance() >= CLOSE_ENOUGH) {
            double speed = (s.inWater() ? SPEED_WATER : SPEED_LAND) * (rage > 0 ? RAGE_BONUS : 1.0);
            if (s.passable(0.2, 0.45))        a.moveForward(speed);
            else if (s.passable(1.3, 0.45))   a.stepUp(STEP_UP, 0.3);
        }

        // She cannot help herself. The rest alcoves in the temple exploit this.
        if (wedgeCooldown == 0 && s.doorAhead() && s.victimDistance() <= 7.0) {
            state = State.WEDGED;
            a.sound("squelch");
            a.particles("item_slime", 14);
            return;
        }

        if (latchCooldown == 0 && s.victimDistance() <= 1.9 && roll(3)) {
            state = State.LATCHED;
            timer = LATCH_TICKS;
            a.sound("chomp");
            return;
        }

        if (clock % NIBBLE_PERIOD == 0 && s.victimDistance() <= 2.5) {
            a.sound("chomp");
            a.particles("splash", 6);
            if (s.victimHealth() >= BITE_FLOOR) a.damageVictim(BITE);
        }
    }

    private void endLatch(Actuators a) {
        if (state == State.LATCHED) { latchCooldown = LATCH_COOLDOWN; a.clearVictimSlow(); }
    }

    // Deterministic and seedable, so the tests can pin it.
    private long seed = 0x9E3779B97F4A7C15L;
    private boolean roll(int oneIn) {
        seed ^= seed << 13; seed ^= seed >>> 7; seed ^= seed << 17;
        return Math.floorMod(seed, oneIn) == 0;
    }
    public void seed(long v) { seed = v == 0 ? 1 : v; }
}
