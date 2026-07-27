package roussette.core;

/** Can and treated-armour accounting.
 *
 *  Deliberately has NO tolerance mechanic. An earlier design made each knockout
 *  harder than the last; it was cut because it makes the tools of the player who
 *  is already being hunted get progressively worse. Every dose is identical,
 *  forever. All scarcity lives in the supply of cans. */
public final class Repellent {

    public static final int SPRAYS_PER_CAN   = 10;    // Margot's call, up from 4

    /** Applying a whole can at an anvil has to stay worth doing.
     *
     *  At 4 sprays a can, trading it for 6 knockouts was an obvious upgrade. At
     *  10 sprays it would have been a downgrade -- you would be burning ten
     *  escapes to buy six -- which quietly kills the anvil recipe. So the
     *  charges scale with the can and the trade keeps its original 1.5x shape:
     *  hands-free, and more total knockouts than you put in. */
    public static final int ARMOUR_CHARGES   = 15;    // was 6, when a can held 4
    public static final int DOSE_TICKS       = 900;   // 45s of proximity
    public static final double DOSE_RANGE    = 6.0;

    /** A can in the player's inventory. */
    public static final class Can {
        private int sprays = SPRAYS_PER_CAN;
        public int  sprays()  { return sprays; }
        public boolean empty(){ return sprays <= 0; }
        /** @return true if a spray was actually released. */
        public boolean spray() { return sprays > 0 && sprays-- > 0; }
        /** Shrine basins refill empties. */
        public void refill() { sprays = SPRAYS_PER_CAN; }
        /** Mining the wrong block in a temple bursts the can. */
        public void rupture() { sprays = 0; }
    }

    /** An armour piece that has had a whole can applied at an anvil. */
    public static final class TreatedArmour {
        private int charges;
        private int dose;
        public TreatedArmour(int charges) { this.charges = charges; }
        public static TreatedArmour applyCan(Can can) {
            can.rupture();                       // a full can is consumed
            return new TreatedArmour(ARMOUR_CHARGES);
        }
        public int  charges() { return charges; }
        public boolean spent(){ return charges <= 0; }
        /** 0.0 to 1.0 -- drives the lavender wash fading off the armour. */
        public double tint()  { return charges / (double) ARMOUR_CHARGES; }
        /** How close she is to keeling over; drives her stagger animation. */
        public double doseFraction() { return dose / (double) DOSE_TICKS; }

        /** Call once per tick. @return true on the tick she should go down. */
        public boolean tick(double distanceToShark, boolean sharkAlreadyDown) {
            if (spent() || sharkAlreadyDown) { return false; }
            if (distanceToShark <= DOSE_RANGE) {
                if (++dose >= DOSE_TICKS) { dose = 0; charges--; return true; }
            } else if (dose > 0) {
                dose--;                          // exposure decays when she backs off
            }
            return false;
        }
    }
}
