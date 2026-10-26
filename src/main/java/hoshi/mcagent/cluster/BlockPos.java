package hoshi.mcagent.cluster;

import java.util.ArrayList;
import java.util.List;

/**
 * Immutable 3D block coordinate for voxel and cluster topological analysis.
 */
public record BlockPos(int x, int y, int z) {

    public BlockPos offset(int dx, int dy, int dz) {
        return new BlockPos(x + dx, y + dy, z + dz);
    }

    public BlockPos offset(String facing) {
        if (facing == null) return this;
        return switch (facing.toLowerCase()) {
            case "down" -> new BlockPos(x, y - 1, z);
            case "up" -> new BlockPos(x, y + 1, z);
            case "north" -> new BlockPos(x, y, z - 1);
            case "south" -> new BlockPos(x, y, z + 1);
            case "west" -> new BlockPos(x - 1, y, z);
            case "east" -> new BlockPos(x + 1, y, z);
            default -> this;
        };
    }

    public int manhattanDistance(BlockPos other) {
        if (other == null) return Integer.MAX_VALUE;
        return Math.abs(x - other.x) + Math.abs(y - other.y) + Math.abs(z - other.z);
    }

    public double euclideanDistance(BlockPos other) {
        if (other == null) return Double.MAX_VALUE;
        double dx = x - other.x;
        double dy = y - other.y;
        double dz = z - other.z;
        return Math.sqrt(dx * dx + dy * dy + dz * dz);
    }

    public List<BlockPos> getDirectNeighbors() {
        List<BlockPos> neighbors = new ArrayList<>(6);
        neighbors.add(new BlockPos(x, y - 1, z));
        neighbors.add(new BlockPos(x, y + 1, z));
        neighbors.add(new BlockPos(x, y, z - 1));
        neighbors.add(new BlockPos(x, y, z + 1));
        neighbors.add(new BlockPos(x - 1, y, z));
        neighbors.add(new BlockPos(x + 1, y, z));
        return neighbors;
    }

    @Override
    public String toString() {
        return String.format("[%d, %d, %d]", x, y, z);
    }
}
