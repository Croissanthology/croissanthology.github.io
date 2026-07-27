package roussette.core;

import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;

/** Who she hunts, and -- more importantly -- who she must never hunt.
 *
 *  <h2>The one-T problem</h2>
 *  The rule Margot gave is "any username with the string roussette is the
 *  enemy". Her brother's username is {@code I_eat_roussetes}, which has ONE T.
 *  Matching the literal string {@code "roussette"} does not match him. He
 *  misspelled his own provocation, and a naive implementation of the stated
 *  rule would have hunted nobody at all.
 *
 *  So the trigger is the stem {@link #TAUNT_STEM}, which catches
 *  {@code roussetes}, {@code roussette}, {@code roussettes} and every other way
 *  of getting it slightly wrong.
 *
 *  <h2>Protection wins</h2>
 *  Protected players are never hunted, no matter what they are called. If the
 *  cousin ever renames herself something provocative she is still safe, and
 *  rule 3 (she is never actually a threat) is never one typo away from failing.
 *  Bystanders can still hit, pat and spray her -- they simply cannot be prey. */
public final class VictimRegistry {

    /** The stem, not the full word. See the one-T problem above. */
    public static final String TAUNT_STEM = "rousset";

    private final Set<String> protectedPlayers = new LinkedHashSet<>();
    private final Set<String> designated       = new LinkedHashSet<>();

    private static String key(String name) {
        return name == null ? "" : name.toLowerCase(Locale.ROOT);
    }

    /** Does this name taunt her? Case-insensitive, and tolerant of the
     *  misspelling that started all this. */
    public static boolean isTaunt(String name) {
        return key(name).contains(TAUNT_STEM);
    }

    /** Mark a player as permanently safe. Overrides everything else. */
    public void protect(String name)   { protectedPlayers.add(key(name)); }

    /** Mark a player as prey explicitly, regardless of what they are called. */
    public void designate(String name) { designated.add(key(name)); }

    public void undesignate(String name) { designated.remove(key(name)); }

    public boolean isProtected(String name) { return protectedPlayers.contains(key(name)); }

    /** Protection first, then explicit designation, then the taunt stem. */
    public boolean isVictim(String name) {
        if (name == null || name.isEmpty()) return false;
        if (isProtected(name)) return false;
        return designated.contains(key(name)) || isTaunt(name);
    }

    public Set<String> protectedPlayers() { return Set.copyOf(protectedPlayers); }
    public Set<String> designated()       { return Set.copyOf(designated); }
}
