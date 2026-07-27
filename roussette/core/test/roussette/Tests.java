package roussette;

import roussette.core.*;
import roussette.core.Ports.Pupil;
import java.util.*;

/** Every behavioural claim in the spec, asserted. */
public class Tests {
    static int passed = 0;
    static List<String> failures = new ArrayList<>();

    static void check(String what, boolean ok) {
        if (ok) { passed++; System.out.println("  ok   " + what); }
        else    { failures.add(what); System.out.println("  FAIL " + what); }
    }

    // --- test doubles -------------------------------------------------------
    static class Fake implements Ports.Sensors, Ports.Actuators {
        double dist = 10; boolean water=false, door=false, pass=true, sneak=false, fire=false;
        int light = 15, health = 20;
        List<String> sounds = new ArrayList<>();
        List<Double> bounceRetains = new ArrayList<>();
        double moved = 0, spun = 0, launchH = 0, launchV = 0, damage = 0;
        int slowCalls = 0, clears = 0, rides = 0, tps = 0;
        Pupil pupil = Pupil.ROUND; boolean glow = false;

        public boolean victimPresent() { return true; }
        public double victimDistance() { return dist; }
        public boolean inWater() { return water; }
        public boolean passable(double u, double f) { return pass; }
        public boolean doorAhead() { return door; }
        public boolean onFire() { return fire; }
        public int lightLevel() { return light; }
        public boolean victimSneaking() { return sneak; }
        public int victimHealth() { return health; }

        public void faceVictim() {} public void levelPitch() {}
        public void moveForward(double b) { moved += b; }
        public void stepUp(double u, double f) { moved += f; }
        public void spinYaw(double d) { spun += d; }
        public void launchAwayFromVictim(double h, double v) { launchH = h; launchV = v; }
        public void bounce(double retain) { bounceRetains.add(retain); }
        public void teleportToVictim() { tps++; }
        public void rideVictimFeet() { rides++; }
        public void sound(String e) { sounds.add(e); }
        public void particles(String k, int n) {}
        public void slowVictim(int a, int t) { slowCalls++; }
        public void clearVictimSlow() { clears++; }
        public void damageVictim(double d) { damage += d; }
        public void setGlowing(boolean on) { glow = on; }
        public void setPupil(Pupil p) { pupil = p; }
    }

    static void run(Roussette r, Fake f, int ticks) { for (int i=0;i<ticks;i++) r.tick(f, f); }

    public static void main(String[] args) {
        System.out.println("\nBEHAVIOUR");
        // rule 3: she can never kill
        Fake f = new Fake(); Roussette r = new Roussette();
        f.dist = 1.0; f.health = 6;              // below the 3.5-heart floor
        run(r, f, 200);
        check("refuses to bite below 3.5 hearts", f.damage == 0);

        f = new Fake(); r = new Roussette(); f.dist = 2.4; f.health = 20;
        run(r, f, 200);
        check("bites when he is healthy", f.damage > 0);

        // rule 2: hitting her is always a fling, never a kill
        f = new Fake(); r = new Roussette();
        r.onHit(f);
        check("a hit flings her", r.state() == Roussette.State.FLUNG && f.launchV > 0.7);
        check("a hit makes her eyes go slitty", f.pupil == Pupil.SLIT);
        run(r, f, Roussette.FLUNG_TICKS + 1);
        check("she returns to hunting after being flung", r.state() == Roussette.State.HUNT);
        run(r, f, Roussette.ANGRY_TICKS + 2);
        check("she forgets the hit and her eyes go round again", f.pupil == Pupil.ROUND);
        check("she wails while airborne", Collections.frequency(f.sounds, "wail") == 3);

        // the ricochet -- "EEEP!" ... "Ok. Ok. anyway."
        f = new Fake(); r = new Roussette(); f.pass = false;   // walls on every side
        r.onHit(f);
        run(r, f, 3);
        check("she ricochets off walls instead of stopping dead", !f.bounceRetains.isEmpty());
        check("the first carom goes EEEP", f.sounds.contains("eep"));
        run(r, f, 80);
        check("she bounces more than once", f.bounceRetains.size() > 1);
        boolean decaying = true;
        for (int i = 1; i < f.bounceRetains.size(); i++)
            if (f.bounceRetains.get(i) > f.bounceRetains.get(i-1)) decaying = false;
        check("each carom keeps less speed than the last", decaying);
        check("she runs out of bounce instead of pinballing forever",
              r.state() == Roussette.State.HUNT);
        check("and huffs when she lands -- 'Ok. Ok. anyway.'", f.sounds.contains("huff"));
        check("she never says a word of it out loud",
              f.sounds.stream().allMatch(Tests::isRecordedNoise));

        // Margot's correction: she CAN be defeated. It just doesn't last.
        f = new Fake(); r = new Roussette();
        r.onDefeated(f);
        check("being defeated is a whole production", f.sounds.contains("wail"));
        r.onReform(f);
        check("and she comes straight back, hunting", r.state() == Roussette.State.HUNT);
        check("with round eyes and no grudge", f.pupil == Pupil.ROUND);
        check("killing her is a project, not an accident", Roussette.MAX_HEALTH >= 30);

        // bystanders (the cousin) reach her through the same entry points
        f = new Fake(); r = new Roussette();
        r.onRepellent(f);
        check("a bystander can drop her with repellent", r.isDown());
        r.onHeadpat(f);
        check("a bystander can pat her while she is down", r.timer() > Roussette.KO_TICKS);

        // the two ways to treat a knocked-out shark
        f = new Fake(); r = new Roussette();
        r.onRepellent(f);
        check("repellent knocks her out with X eyes", r.isDown() && f.pupil == Pupil.X);
        int before = r.timer(); r.onHeadpat(f);
        check("patting her while down keeps her down LONGER", r.timer() > before);
        check("patting her while down does not wake her", r.isDown());

        f = new Fake(); r = new Roussette(); r.onRepellent(f);
        r.onHit(f);
        check("hitting her while down wakes her instantly", !r.isDown());
        f.dist = 10; f.pass = true;
        double calm = measureSpeed(new Roussette(), false);
        double raging = measureSpeedAfterWake();
        check("and she is faster afterwards, out of spite", raging > calm);

        // the number the whole temple design rests on
        check("water doubles her speed", Roussette.SPEED_WATER / Roussette.SPEED_LAND > 2.0);
        double land = measureSpeed(new Roussette(), false), swim = measureSpeed(new Roussette(), true);
        check("...and it actually shows up in movement", swim > land * 2);

        // doorways
        f = new Fake(); r = new Roussette(); f.dist = 5; f.door = true;
        run(r, f, 3);
        check("a doorway traps her", r.state() == Roussette.State.WEDGED);
        f.dist = 9;
        run(r, f, 2);
        check("she pops free once he is 7 blocks away", r.state() == Roussette.State.HUNT);

        // latching
        f = new Fake(); r = new Roussette(); r.seed(4); f.dist = 1.5;
        run(r, f, 60);
        boolean latched = r.state() == Roussette.State.LATCHED;
        check("she latches on when close", latched);
        if (latched) { r.onHeadpat(f); check("a headpat frees your leg", f.clears > 0); }

        // glow
        f = new Fake(); r = new Roussette(); f.light = 3; run(r, f, 1);
        check("she glows in the dark", f.glow);
        f.light = 12; run(r, f, 1);
        check("and not in the light", !f.glow);

        System.out.println("\nREPELLENT");
        Repellent.Can can = new Repellent.Can();
        int n = 0; while (can.spray()) n++;
        check("a can holds exactly 4 sprays", n == 4);
        can.refill();
        check("a shrine basin refills it", can.sprays() == 4);

        Repellent.TreatedArmour armour = Repellent.TreatedArmour.applyCan(can);
        check("applying a can consumes the whole thing", can.empty());
        int knockouts = 0;
        for (int i = 0; i < Repellent.DOSE_TICKS * 10 && !armour.spent(); i++)
            if (armour.tick(3.0, false)) knockouts++;
        check("treated armour gives exactly 6 knockouts", knockouts == 6);
        check("and then the treatment is spent", armour.spent());
        check("the tint fades to nothing as it goes", armour.tint() == 0.0);

        Repellent.TreatedArmour a2 = new Repellent.TreatedArmour(6);
        for (int i = 0; i < Repellent.DOSE_TICKS - 1; i++) a2.tick(3.0, false);
        double near = a2.doseFraction();
        for (int i = 0; i < 200; i++) a2.tick(40.0, false);
        check("backing off lets the dose decay", a2.doseFraction() < near);

        int first = countTicksToKnockout(new Repellent.TreatedArmour(6));
        Repellent.TreatedArmour a3 = new Repellent.TreatedArmour(6);
        countTicksToKnockout(a3);
        int second = countTicksToKnockout(a3);
        check("NO tolerance buildup -- every dose costs the same", first == second);

        System.out.println("\nTEMPLE SITES");
        SiteFinder sf = new SiteFinder();
        List<SiteFinder.Site> sites = sf.find(new FlatWorld(), 0, 0, 6000, 12);
        check("it finds sites", !sites.isEmpty());
        boolean spaced = true, unique = true;
        Set<String> seen = new HashSet<>();
        for (int i = 0; i < sites.size(); i++) {
            if (!seen.add(sites.get(i).biome())) unique = false;
            for (int j = i+1; j < sites.size(); j++) {
                double dx = sites.get(i).x()-sites.get(j).x(), dz = sites.get(i).z()-sites.get(j).z();
                if (Math.sqrt(dx*dx+dz*dz) < SiteFinder.MIN_SPACING) spaced = false;
            }
        }
        check("at most one temple per biome", unique);
        check("all temples at least 1500 blocks apart", spaced);
        check("no temples on lumpy ground", sf.find(new LumpyWorld(), 0, 0, 4000, 12).isEmpty());

        System.out.println("\nBLUEPRINT");
        try {
            String grid = new String(java.nio.file.Files.readAllBytes(
                java.nio.file.Path.of("src/roussette/core/temple.txt")));
            Blueprint bp = new Blueprint(grid);
            check("the cross-section parses", bp.placements().size() > 300);
            check("there is exactly one chest", bp.count("minecraft:chest") == 1);
            check("the shaft is lined with unbreakable stone", bp.count("roussette:shrine_stone") > 90);
            check("there are three alcove doors (six door halves)", bp.count("minecraft:copper_door") == 6);
            check("amethyst lights the descent", bp.count("minecraft:amethyst_cluster") > 10);
            check("votive frames are present", bp.count("roussette:votive_frame") == 4);
        } catch (Exception e) { check("blueprint loads: " + e, false); }

        System.out.println("\nGEOMETRY");
        check("she is about 2 blocks long", Math.abs(Geometry.lengthPixels()/16.0 - 1.95) < 0.1);
        check("head/total ratio is inside the cute band",
              Geometry.headRatio() > 0.32 && Geometry.headRatio() < 0.42);
        check("20 boxes", Geometry.PARTS.length == 20);
        boolean sym = true;
        for (Geometry.Box b : Geometry.PARTS) if (b.name().endsWith("L")) {
            String rn = b.name().substring(0, b.name().length()-1) + "R";
            boolean found = false;
            for (Geometry.Box o : Geometry.PARTS)
                if (o.name().equals(rn) && Math.abs(o.pz() + b.pz()) < 1e-9) found = true;
            if (!found) sym = false;
        }
        check("left and right parts are mirrored exactly", sym);

        System.out.println("\n" + passed + " passed, " + failures.size() + " failed");
        if (!failures.isEmpty()) { failures.forEach(x -> System.out.println("   - " + x)); System.exit(1); }
    }

    /** Rule 4: she does not speak. Every noise she is capable of making must be
     *  one of Margot's recordings -- if a line of dialogue ever leaks into the
     *  sound channel, this catches it. */
    static final Set<String> VOICE = Set.of(
        "cry", "wail", "purr", "purreow", "chomp", "gnaw", "squelch", "reform",
        "eep",      // the ricochet yelp
        "huff");    // the settling noise: "Ok. Ok. anyway."
    static boolean isRecordedNoise(String s) { return VOICE.contains(s); }

    static double measureSpeed(Roussette r, boolean water) {
        Fake f = new Fake(); f.dist = 10; f.water = water;
        r.tick(f, f);
        return f.moved;
    }
    static double measureSpeedAfterWake() {
        Fake f = new Fake(); Roussette r = new Roussette();
        r.onRepellent(f); r.onHit(f);
        for (int i = 0; i < Roussette.FLUNG_TICKS + 1; i++) r.tick(f, f);
        f.moved = 0; f.dist = 10;
        r.tick(f, f);
        return f.moved;
    }
    static int countTicksToKnockout(Repellent.TreatedArmour a) {
        int t = 0; while (!a.tick(3.0, false) && t < 100000) t++;
        return t;
    }

    static class FlatWorld implements SiteFinder.Terrain {
        public int surfaceY(int x, int z) { return 70; }
        public String biome(int x, int z) {
            String[] b = {"plains","forest","desert","savanna","taiga","swamp","jungle","badlands"};
            return b[Math.floorMod((x/1500)*7 + (z/1500)*13, b.length)];
        }
        public boolean isLand(int x, int z) { return true; }
    }
    static class LumpyWorld implements SiteFinder.Terrain {
        public int surfaceY(int x, int z) { return 70 + Math.floorMod(x*31+z*17, 9); }
        public String biome(int x, int z) { return "hills"; }
        public boolean isLand(int x, int z) { return true; }
    }
}
