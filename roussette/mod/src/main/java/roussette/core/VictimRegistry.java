package roussette.core;

import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;

/** Who she hunts, and -- more importantly -- who she must never hunt.
 *
 *  <h2>Exactly one target at a time</h2>
 *  Spec §4 opens with "one roussette per victim", so this holds a single current
 *  target rather than a set. {@code /new-target <name>} moves her onto somebody
 *  else, which is what happens when the current victim goes home.
 *
 *  <h2>Why the trigger is a stem</h2>
 *  The taunt rule is "any username containing roussette". The stem
 *  {@link #TAUNT_STEM} is used instead of the full word so that one-T
 *  misspellings, plurals and case all still match. Nobody has to spell it right
 *  for the mod to work, which given how this project started seems wise.
 *
 *  <h2>Protection wins</h2>
 *  A protected player can never become the target, by taunt or by command. Rule
 *  3 (she is never actually a threat) is therefore never one typo or one
 *  mistyped command away from failing. Protected players keep every other
 *  interaction: they can hit her, pat her, and spray her. */
public final class VictimRegistry {

    /** The stem, not the full word -- tolerant of spelling. */
    public static final String TAUNT_STEM = "rousset";

    private final Set<String> protectedPlayers = new LinkedHashSet<>();
    private String target;   // lowercase, or null for nobody

    private static String key(String name) {
        return name == null ? "" : name.toLowerCase(Locale.ROOT);
    }

    /** Does this name taunt her? Case-insensitive. */
    public static boolean isTaunt(String name) {
        return key(name).contains(TAUNT_STEM);
    }

    /** Mark a player permanently safe. Overrides taunts and commands alike. */
    public void protect(String name) {
        protectedPlayers.add(key(name));
        if (key(name).equals(target)) target = null;   // safety is retroactive
    }

    public boolean isProtected(String name) { return protectedPlayers.contains(key(name)); }

    /**
     * {@code /new-target <name>}. Moves her onto a new victim.
     *
     * @return false if that player is protected, in which case nothing changes
     *         and the command should report the refusal.
     */
    public boolean newTarget(String name) {
        if (name == null || name.isEmpty() || isProtected(name)) return false;
        target = key(name);
        return true;
    }

    /** Auto-adopt on join: a taunting name picks a fight, but only if nobody is
     *  currently being hunted. An existing target is never silently replaced. */
    public boolean adoptIfTaunting(String name) {
        if (target != null || isProtected(name) || !isTaunt(name)) return false;
        target = key(name);
        return true;
    }

    public void clearTarget() { target = null; }

    /** The current victim's name, lowercase, or null if she is between victims. */
    public String target() { return target; }

    public boolean hasTarget() { return target != null; }

    public boolean isVictim(String name) {
        if (name == null || name.isEmpty() || target == null) return false;
        if (isProtected(name)) return false;
        return target.equals(key(name));
    }

    public Set<String> protectedPlayers() { return Set.copyOf(protectedPlayers); }
}
