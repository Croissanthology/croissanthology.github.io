package roussette.core;

/** Model v5, "elegant pass". Units are Minecraft pixels, 16 to a block.
 *  Origin at body centre, +X toward the nose, +Y up. Rotations are Euler XYZ
 *  radians about each box's own centre.
 *
 *  Proportion bands that must hold after any edit (neoteny ratios, tuned over
 *  four passes): head/total 0.32-0.42, eye/head 0.30-0.50, height/total
 *  0.42-0.55, width/total 0.34-0.50. LENGTHENING HER IS THE DANGEROUS EDIT --
 *  a long body reads as predatory no matter what colour it is. */
public final class Geometry {
    private Geometry() {}

    public record Box(String name, double sx, double sy, double sz,
                      double px, double py, double pz,
                      double rx, double ry, double rz, int colour) {}

    public static final int LAV = 0xC3ADEB, LAV_DEEP = 0x8E6FC4, BELLY = 0xF3ECFC,
                            BLUSH = 0xF2A8CE, DARK = 0x5B4383,
                            GOLD = 0xF0C64B, INK = 0x241832;

    public static final Box[] PARTS = {
        new Box("snout",    3.4,4.6,6.0,  10.4,-0.6, 0,    0,0,0,        LAV),
        new Box("head",     8.8,8.8,9.2,   5.4, 0.2, 0,    0,0,0,        LAV),
        new Box("cheekL",   2.2,2.0,0.6,   8.2,-1.9, 4.6,  0,0,0,        BLUSH),
        new Box("cheekR",   2.2,2.0,0.6,   8.2,-1.9,-4.6,  0,0,0,        BLUSH),
        new Box("earL",     2.6,3.0,2.6,   4.6, 5.3, 3.1,  0.30,0,0.16,  LAV),
        new Box("earR",     2.6,3.0,2.6,   4.6, 5.3,-3.1, -0.30,0,0.16,  LAV),
        new Box("earInL",   1.3,1.7,0.6,   4.6, 5.5, 4.5,  0.30,0,0.16,  BLUSH),
        new Box("earInR",   1.3,1.7,0.6,   4.6, 5.5,-4.5, -0.30,0,0.16,  BLUSH),
        new Box("trunk",    8.4,8.8,8.2,  -2.4,-0.2, 0,    0,0,0,        LAV),
        new Box("belly",    8.0,4.0,7.8,  -2.4,-4.3, 0,    0,0,0,        BELLY),
        new Box("rear",     4.6,6.0,5.2,  -7.8, 0.2, 0,    0,0,0,        LAV),
        new Box("peduncle", 3.0,3.6,2.8, -10.8, 0.5, 0,    0,0,0,        LAV),
        new Box("dorsal",   4.2,3.6,1.0,  -3.2, 5.6, 0,    0,0,0,        LAV_DEEP),
        new Box("tailUp",   4.6,3.0,1.0, -13.4, 3.0, 0,    0,0,0.52,     LAV_DEEP),
        new Box("tailLo",   4.2,2.6,1.0, -13.2,-1.6, 0,    0,0,-0.48,    LAV_DEEP),
        new Box("tailMid",  2.2,2.0,1.0, -12.2, 0.7, 0,    0,0,0,        LAV_DEEP),
        new Box("pectL",    3.6,0.9,4.0,   1.6,-3.0, 4.6,  0.46,0,0.14,  LAV_DEEP),
        new Box("pectR",    3.6,0.9,4.0,   1.6,-3.0,-4.6, -0.46,0,0.14,  LAV_DEEP),
        new Box("whiskL",   5.0,0.3,0.3,  13.0,-1.6, 2.0,  0,0.30,0.14,  DARK),
        new Box("whiskR",   5.0,0.3,0.3,  13.0,-1.6,-2.0,  0,-0.30,0.14, DARK),
    };

    /** Eyes, mirrored on plus/minus Z, built as flat quads so the expression
     *  stays legible at distance. Pupil geometry depends on her state. */
    public static final double EYE_X = 8.0, EYE_Y = -0.3, EYE_Z = 4.70;
    public static final double RIM = 4.6, IRIS = 3.9;
    public static final double[] PUPIL_ROUND = { 2.5, 2.5 };
    public static final double[] PUPIL_SLIT  = { 1.0, 3.1 };
    public static final double[] PUPIL_X_BAR = { 0.95, 4.0 };   // two, at plus/minus 45 degrees

    public static double lengthPixels() {
        double lo = Double.MAX_VALUE, hi = -Double.MAX_VALUE;
        for (Box b : PARTS) { lo = Math.min(lo, b.px() - b.sx()/2); hi = Math.max(hi, b.px() + b.sx()/2); }
        return hi - lo;
    }
    public static double headRatio() {
        double lo = Double.MAX_VALUE, hi = -Double.MAX_VALUE;
        for (Box b : PARTS) if (b.name().equals("head") || b.name().equals("snout")) {
            lo = Math.min(lo, b.px() - b.sx()/2); hi = Math.max(hi, b.px() + b.sx()/2);
        }
        return (hi - lo) / lengthPixels();
    }
}
