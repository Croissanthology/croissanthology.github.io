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
        boolean sleeping=false; int flumps=0;
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
        public boolean victimSleeping() { return sleeping; }
        public int victimHealth() { return health; }

        public void faceVictim() {} public void levelPitch() {}
        public void moveForward(double b) { moved += b; }
        public void stepUp(double u, double f) { moved += f; }
        public void spinYaw(double d) { spun += d; }
        public void launchAwayFromVictim(double h, double v) { launchH = h; launchV = v; }
        public void bounce(double retain) { bounceRetains.add(retain); }
        public void teleportToVictim() { tps++; }
        public void rideVictimFeet() { rides++; }
        public void flumpBeside() { flumps++; }
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
        check("she is killable without being a pushover", Roussette.MAX_HEALTH == 16);
        check("a single hit never kills her, so the fling loop survives",
              Roussette.MAX_HEALTH > 10);
        check("she is back almost immediately", Roussette.REFORM_DELAY <= 40);

        // bystanders (the cousin) reach her through the same entry points
        f = new Fake(); r = new Roussette();
        r.onRepellent(f);
        check("a bystander can drop her with repellent", r.isDown());
        r.onHeadpat(f);
        check("a bystander can pat her while she is down", r.timer() > Roussette.KO_TICKS);

        // bedtime: he gets in a bed, she ports over and flumps
        f = new Fake(); r = new Roussette(); f.dist = 20; f.sleeping = true;
        run(r, f, 1);
        check("he goes to bed and she comes to sleep on him",
              r.state() == Roussette.State.SLEEPING);
        check("she flumps over beside him", f.flumps > 0);
        check("with her eyes shut, not X'd out", f.pupil == Pupil.CLOSED);
        f.sounds.clear();
        run(r, f, Roussette.SNORE_PERIOD * 6);
        long snoozing = f.sounds.stream().filter(x -> x.equals("snore") || x.equals("snort")).count();
        check("she snores on a loop while he sleeps", snoozing >= 4);
        check("and some of them are snorts", f.sounds.contains("snort"));
        check("she does not bite a sleeping person", f.damage == 0);
        check("every sleeping noise is still a recorded one",
              f.sounds.stream().allMatch(Tests::isRecordedNoise));

        // a headpat at bedtime, mirroring the knocked-out rule
        int before2 = f.sounds.size();
        r.onHeadpat(f);
        check("patting her at bedtime purrs without waking her",
              r.state() == Roussette.State.SLEEPING && f.sounds.size() > before2);

        // punting her out of bed works, and she comes straight back
        r.onHit(f);
        check("she can still be punted off the pillow", r.state() == Roussette.State.FLUNG);
        run(r, f, Roussette.FLUNG_TICKS + 2);
        check("and flumps back down again, because he is still asleep",
              r.state() == Roussette.State.SLEEPING);

        // morning
        f.sleeping = false;
        run(r, f, 1);
        check("she is awake and hunting again in the morning",
              r.state() == Roussette.State.HUNT);
        check("with normal eyes", f.pupil == Pupil.ROUND);

        // being knocked out beats bedtime -- she is unconscious, not asleep
        f = new Fake(); r = new Roussette(); f.sleeping = true;
        r.onRepellent(f);
        run(r, f, 1);
        check("repellent outranks bedtime", r.isDown() && f.pupil == Pupil.X);

        // fleeing: the Nether, the End, an ender pearl, /tp -- all one event.
        // She does not travel to him. She re-forms on him, wetly.
        f = new Fake(); r = new Roussette();
        f.dist = 5000;                        // he changed dimension
        run(r, f, 1);
        check("fleeing to another dimension just makes her re-form on him", f.tps == 1);
        check("and the splat announces itself", f.sounds.contains("reform"));
        check("she never tries to pathfind there", f.moved == 0);
        check("any distance past the leash counts as fleeing", 5000 > Roussette.LEASH);
        f = new Fake(); r = new Roussette(); f.dist = Roussette.LEASH - 1; f.pass = true;
        run(r, f, 1);
        check("but normal chasing distance does not teleport her", f.tps == 0 && f.moved > 0);

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
        check("a can holds exactly 10 sprays", n == 10);
        check("and once it is empty it stays empty, forever", can.empty());
        check("one can per temple -- that is the whole supply",
              Repellent.CANS_PER_TEMPLE == 1);
        check("the anvil recipe is a sidegrade, not a multiplier",
              Repellent.ARMOUR_CHARGES < Repellent.SPRAYS_PER_CAN);

        Repellent.Can fresh = new Repellent.Can();
        Repellent.TreatedArmour armour = Repellent.TreatedArmour.applyCan(fresh);
        check("applying a can consumes the whole thing", fresh.empty());
        int knockouts = 0;
        int budget = Repellent.DOSE_TICKS * (Repellent.ARMOUR_CHARGES + 2);
        for (int i = 0; i < budget && !armour.spent(); i++)
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

        System.out.println("\nVICTIM");
        // The stem matches however the word gets spelled -- two Ts, one T,
        // plural, any case. Nobody has to get it right for the mod to work.
        check("the real username taunts her", VictimRegistry.isTaunt("I_eat_roussettes"));
        check("a one-T misspelling still taunts her", VictimRegistry.isTaunt("I_eat_roussetes"));
        check("so does the singular", VictimRegistry.isTaunt("Roussette_Hater"));
        check("and it is case-insensitive", VictimRegistry.isTaunt("ROUSSETTES_R_FOOD"));
        check("an innocent name is not a taunt", !VictimRegistry.isTaunt("Margot"));

        VictimRegistry reg = new VictimRegistry();
        reg.protect("LittleCousin");
        check("a taunting name picks the fight by itself",
              reg.adoptIfTaunting("I_eat_roussettes"));
        check("the brother is prey", reg.isVictim("I_eat_roussettes"));
        check("the cousin is not", !reg.isVictim("LittleCousin"));
        check("she hunts exactly one person at a time",
              !reg.adoptIfTaunting("Another_roussette_enjoyer"));

        // /new-target, for when the current victim goes home
        check("/new-target moves her on", reg.newTarget("SomeoneElse"));
        check("and she forgets the old one entirely", !reg.isVictim("I_eat_roussettes"));
        check("the new target is hunted", reg.isVictim("SomeoneElse"));
        check("/new-target refuses a protected player", !reg.newTarget("LittleCousin"));
        check("and the refusal changes nothing", reg.isVictim("SomeoneElse"));

        VictimRegistry reg2 = new VictimRegistry();
        reg2.newTarget("Someone_roussette");
        reg2.protect("Someone_roussette");
        check("protecting the current victim calls her off immediately",
              !reg2.isVictim("Someone_roussette"));
        check("protection beats the taunt stem, so rule 3 is never one typo away",
              !reg2.adoptIfTaunting("Someone_roussette"));
        check("nobody is hunted by default", !new VictimRegistry().hasTarget());

        System.out.println("\nTEMPLE BUILD");
        try {
            String grid = new String(java.nio.file.Files.readAllBytes(
                java.nio.file.Path.of("src/roussette/core/temple.txt")));
            Blueprint bp = new Blueprint(grid);
            List<Blueprint.Placement3> solid = bp.expand(Blueprint.DEPTH);

            check("extruding gives a real building", solid.size() > 5000);
            check("there is still exactly ONE chest, not thirteen",
                  Blueprint.count3(solid, "minecraft:chest") == 1);
            check("still three doors, not thirty-nine",
                  Blueprint.count3(solid, "minecraft:copper_door") == 6);
            check("still four votive frames",
                  Blueprint.count3(solid, "roussette:votive_frame") == 4);
            check("she hangs on the deepest wall as exactly one painting",
                  Blueprint.count3(solid, Blueprint.PAINTING) == 1);

            // the shaft must not be open to raw terrain at the extruded ends
            boolean capped = true;
            int back = Blueprint.DEPTH - 1;
            for (Blueprint.Placement3 p : solid)
                if ((p.z() == 0 || p.z() == back) && p.block().equals("minecraft:water"))
                    capped = false;
            check("the ends are capped, so the pool cannot drain into the ground", capped);

            SiteFinder.Site site = new SiteFinder.Site(1000, -2000, "plains", 70);
            List<TempleBuilder.Abs> world = TempleBuilder.toWorld(
                solid, site, bp.groundRow(), bp.centreColumn(), Blueprint.DEPTH);
            check("world mapping keeps every block", world.size() == solid.size());

            int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE;
            for (TempleBuilder.Abs a : world) { lo = Math.min(lo, a.y()); hi = Math.max(hi, a.y()); }
            check("the pool really is deep", (site.surfaceY() - lo) >= 30);
            check("the above-ground part is a squat lip, not a tower",
                  (hi - site.surfaceY()) <= 8);
            check("it is built around the site, not off to one side",
                  Math.abs(centreOf(world) - site.x()) <= 2);

            TempleBuilder.Schedule sch = new TempleBuilder.Schedule(
                world, TempleBuilder.BLOCKS_PER_TICK);
            check("the work is split over many chunks", sch.chunkCount() > 1);
            int batches = 0, blocks = 0; boolean oneChunkAtATime = true;
            TempleBuilder.Batch b;
            while ((b = sch.next()) != null) {
                batches++; blocks += b.blocks().size();
                if (b.blocks().size() > TempleBuilder.BLOCKS_PER_TICK) oneChunkAtATime = false;
                for (TempleBuilder.Abs a : b.blocks())
                    if (a.chunkX() != b.chunkX() || a.chunkZ() != b.chunkZ()) oneChunkAtATime = false;
            }
            check("no tick ever writes more than its budget", oneChunkAtATime);
            check("a batch never spans two chunks, so only one is force-loaded", oneChunkAtATime);
            check("every block gets written exactly once", blocks == world.size());
            check("and it takes several ticks instead of hanging the server", batches > 1);
            check("progress reaches 100%", sch.done() && sch.progress() == 1.0);
        } catch (Exception e) { check("temple build: " + e, false); }

        TempleBuilder.OneShot once = new TempleBuilder.OneShot();
        check("/roussette-temples runs the first time", once.tryFire());
        check("a second player typing it mid-run is refused", !once.tryFire());
        check("and told why", once.refusal().contains("being built"));
        once.complete();
        check("and it is still refused after it finishes", !once.tryFire());
        check("with a different message", once.refusal().contains("already"));

        TempleBuilder.OneShot restored = new TempleBuilder.OneShot();
        restored.restore(TempleBuilder.RunState.COMPLETED);
        check("the refusal survives a server restart", !restored.tryFire());
        TempleBuilder.OneShot crashed = new TempleBuilder.OneShot();
        crashed.restore(TempleBuilder.RunState.RUNNING);
        check("a run interrupted by a crash does not reopen the door",
              !crashed.tryFire());

        check("temples are an Overworld thing",
              TempleBuilder.canBuildIn("minecraft:overworld"));
        check("...not a Nether thing", !TempleBuilder.canBuildIn("minecraft:the_nether"));
        check("...nor an End thing", !TempleBuilder.canBuildIn("minecraft:the_end"));

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
        "huff",     // the settling noise: "Ok. Ok. anyway."
        "snore", "snort");   // bedtime
    static boolean isRecordedNoise(String s) { return VOICE.contains(s); }

    /** Mid-X of a placed temple, for checking it straddles its site. */
    static double centreOf(List<TempleBuilder.Abs> world) {
        int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE;
        for (TempleBuilder.Abs a : world) { lo = Math.min(lo, a.x()); hi = Math.max(hi, a.x()); }
        return (lo + hi) / 2.0;
    }

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
