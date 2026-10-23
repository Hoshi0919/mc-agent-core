package hoshi.mcagent.multiblock;

import java.util.*;

/**
 * Immutable definition of a multiblock structure in Minecraft (vanilla and tech automation).
 */
public record MultiblockBlueprint(
        String id,
        String name,
        int widthX,
        int heightY,
        int depthZ,
        Map<String, Integer> requiredBlocks,
        List<String[]> layerSchematics,
        String coreActivationCondition,
        String perksAndRange
) {
    public MultiblockBlueprint {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(name, "name");
        requiredBlocks = Collections.unmodifiableMap(new LinkedHashMap<>(requiredBlocks != null ? requiredBlocks : Collections.emptyMap()));
        layerSchematics = Collections.unmodifiableList(new ArrayList<>(layerSchematics != null ? layerSchematics : Collections.emptyList()));
        coreActivationCondition = coreActivationCondition != null ? coreActivationCondition : "";
        perksAndRange = perksAndRange != null ? perksAndRange : "";
    }

    public int totalBlockCount() {
        return requiredBlocks.values().stream().mapToInt(Integer::intValue).sum();
    }
}
