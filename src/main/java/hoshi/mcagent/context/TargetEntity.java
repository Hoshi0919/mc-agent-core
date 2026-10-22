package hoshi.mcagent.context;

import java.util.Collections;
import java.util.Map;

/**
 * Represents the entity targeted by the player's crosshair (Raycast Entity HitResult).
 */
public record TargetEntity(
        String entityId,
        String customName,
        float health,
        float maxHealth,
        boolean isHostile,
        boolean isBaby,
        boolean isTamed,
        String profession,
        Map<String, String> properties
) {
    public TargetEntity {
        if (properties == null) {
            properties = Collections.emptyMap();
        }
    }

    public static TargetEntity of(String entityId, float health, float maxHealth, boolean isHostile) {
        return new TargetEntity(entityId, null, health, maxHealth, isHostile, false, false, null, Collections.emptyMap());
    }

    public boolean isVillager() {
        return entityId != null && entityId.contains("villager") && !entityId.contains("zombie_villager");
    }

    public boolean isZombieVillager() {
        return entityId != null && entityId.contains("zombie_villager");
    }

    public boolean isPiglin() {
        return entityId != null && entityId.contains("piglin") && !entityId.contains("piglin_brute");
    }

    public boolean isPiglinBrute() {
        return entityId != null && entityId.contains("piglin_brute");
    }

    public boolean isWarden() {
        return entityId != null && entityId.contains("warden");
    }

    public boolean isArmadillo() {
        return entityId != null && entityId.contains("armadillo");
    }

    public boolean isIronGolem() {
        return entityId != null && entityId.contains("iron_golem");
    }

    public String toSummary() {
        String name = (customName != null && !customName.isEmpty()) ? customName : entityId;
        String prof = profession != null ? " (" + profession + ")" : "";
        return String.format("%s%s [HP: %.1f/%.1f, Hostile: %b, Baby: %b]", name, prof, health, maxHealth, isHostile, isBaby);
    }
}
