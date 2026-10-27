package hoshi.mcagent.spatial;

/**
 * RGBA color representation for in-world visual highlights and HUD cards.
 */
public record SpatialColor(int red, int green, int blue, int alpha) {

    public static final SpatialColor RED = new SpatialColor(255, 60, 60, 180);
    public static final SpatialColor GREEN = new SpatialColor(60, 255, 60, 180);
    public static final SpatialColor BLUE = new SpatialColor(60, 150, 255, 180);
    public static final SpatialColor YELLOW = new SpatialColor(255, 215, 0, 180);
    public static final SpatialColor ORANGE = new SpatialColor(255, 140, 0, 180);
    public static final SpatialColor CYAN = new SpatialColor(0, 255, 255, 180);
    public static final SpatialColor PURPLE = new SpatialColor(186, 85, 211, 180);
    public static final SpatialColor WHITE = new SpatialColor(255, 255, 255, 200);

    public SpatialColor {
        red = Math.max(0, Math.min(255, red));
        green = Math.max(0, Math.min(255, green));
        blue = Math.max(0, Math.min(255, blue));
        alpha = Math.max(0, Math.min(255, alpha));
    }

    public SpatialColor withAlpha(int newAlpha) {
        return new SpatialColor(red, green, blue, newAlpha);
    }

    public String toHex() {
        return String.format("#%02X%02X%02X%02X", red, green, blue, alpha);
    }

    public String toJson() {
        return "{\"r\":" + red + ",\"g\":" + green + ",\"b\":" + blue + ",\"a\":" + alpha + "}";
    }

    public static SpatialColor fromHex(String hex) {
        if (hex == null || hex.isEmpty()) {
            return WHITE;
        }
        String clean = hex.startsWith("#") ? hex.substring(1) : hex;
        try {
            if (clean.length() == 6) {
                int r = Integer.parseInt(clean.substring(0, 2), 16);
                int g = Integer.parseInt(clean.substring(2, 4), 16);
                int b = Integer.parseInt(clean.substring(4, 6), 16);
                return new SpatialColor(r, g, b, 255);
            } else if (clean.length() == 8) {
                int r = Integer.parseInt(clean.substring(0, 2), 16);
                int g = Integer.parseInt(clean.substring(2, 4), 16);
                int b = Integer.parseInt(clean.substring(4, 6), 16);
                int a = Integer.parseInt(clean.substring(6, 8), 16);
                return new SpatialColor(r, g, b, a);
            }
        } catch (Exception ignored) {
        }
        return WHITE;
    }
}
