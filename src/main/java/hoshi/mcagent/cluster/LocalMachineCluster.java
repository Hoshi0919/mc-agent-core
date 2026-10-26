package hoshi.mcagent.cluster;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 3D Subgraph of connected blocks in the immediate vicinity of the player's crosshair target.
 */
public record LocalMachineCluster(
        BlockPos origin,
        Map<BlockPos, LocalBlock> blocks
) {
    public LocalMachineCluster {
        if (blocks == null) {
            blocks = Collections.emptyMap();
        }
    }

    public static LocalMachineCluster empty(BlockPos origin) {
        return new LocalMachineCluster(origin, Collections.emptyMap());
    }

    public static Builder builder(int originX, int originY, int originZ) {
        return new Builder(new BlockPos(originX, originY, originZ));
    }

    public static Builder builder(BlockPos origin) {
        return new Builder(origin);
    }

    public LocalBlock getBlock(BlockPos pos) {
        return blocks.get(pos);
    }

    public LocalBlock getBlock(int x, int y, int z) {
        return blocks.get(new BlockPos(x, y, z));
    }

    public Optional<LocalBlock> originBlock() {
        return Optional.ofNullable(blocks.get(origin));
    }

    public int size() {
        return blocks.size();
    }

    public boolean isEmpty() {
        return blocks.isEmpty();
    }

    public List<LocalBlock> getBlocksByType(String keyword) {
        if (keyword == null) return Collections.emptyList();
        String kw = keyword.toLowerCase();
        return blocks.values().stream()
                .filter(b -> b.blockId() != null && b.blockId().toLowerCase().contains(kw))
                .collect(Collectors.toList());
    }

    public List<LocalBlock> getConnectedKinetics() {
        return blocks.values().stream()
                .filter(LocalBlock::isCreateKinetics)
                .collect(Collectors.toList());
    }

    public List<LocalBlock> getConnectedHoppers() {
        return blocks.values().stream()
                .filter(LocalBlock::isHopper)
                .collect(Collectors.toList());
    }

    public String toSummary() {
        if (isEmpty()) {
            return "EmptyCluster (0 blocks)";
        }
        return String.format("Cluster centered at %s with %d blocks (Kinetics: %d, Hoppers: %d, Containers: %d)",
                origin,
                blocks.size(),
                getConnectedKinetics().size(),
                getConnectedHoppers().size(),
                getBlocksByType("chest").size() + getBlocksByType("barrel").size() + getBlocksByType("crafter").size());
    }

    public static class Builder {
        private final BlockPos origin;
        private final Map<BlockPos, LocalBlock> map = new HashMap<>();

        public Builder(BlockPos origin) {
            this.origin = origin;
        }

        public Builder add(LocalBlock block) {
            if (block != null && block.pos() != null) {
                map.put(block.pos(), block);
            }
            return this;
        }

        public Builder add(int x, int y, int z, String blockId, Map<String, String> properties) {
            map.put(new BlockPos(x, y, z), LocalBlock.of(x, y, z, blockId, properties));
            return this;
        }

        public Builder add(int x, int y, int z, String blockId) {
            map.put(new BlockPos(x, y, z), LocalBlock.of(x, y, z, blockId));
            return this;
        }

        public LocalMachineCluster build() {
            return new LocalMachineCluster(origin, Collections.unmodifiableMap(new HashMap<>(map)));
        }
    }
}
