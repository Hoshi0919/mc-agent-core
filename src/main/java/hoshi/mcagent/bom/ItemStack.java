package hoshi.mcagent.bom;

import java.util.Objects;

/**
 * Immutable representation of a required Minecraft item quantity and stack breakdown.
 */
public class ItemStack {
    private final String itemId;
    private final String displayName;
    private final int count;

    public ItemStack(String itemId, String displayName, int count) {
        if (count < 0) {
            throw new IllegalArgumentException("Item count cannot be negative: " + count);
        }
        this.itemId = Objects.requireNonNull(itemId, "itemId");
        this.displayName = Objects.requireNonNull(displayName, "displayName");
        this.count = count;
    }

    public String getItemId() {
        return itemId;
    }

    public String getDisplayName() {
        return displayName;
    }

    public int getCount() {
        return count;
    }

    public int getStacks() {
        return count / 64;
    }

    public int getRemainder() {
        return count % 64;
    }

    /**
     * Formats count into Minecraft survival stack representation (e.g. "164 (2 组 + 36 个)").
     */
    public String formatStacks() {
        int stacks = getStacks();
        int rem = getRemainder();
        if (stacks > 0 && rem > 0) {
            return String.format("%d (%d 组 + %d 个)", count, stacks, rem);
        } else if (stacks > 0) {
            return String.format("%d (%d 组整)", count, stacks);
        } else {
            return String.format("%d 个", count);
        }
    }

    @Override
    public String toString() {
        return displayName + " x" + formatStacks();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof ItemStack)) return false;
        ItemStack itemStack = (ItemStack) o;
        return count == itemStack.count &&
                itemId.equals(itemStack.itemId) &&
                displayName.equals(itemStack.displayName);
    }

    @Override
    public int hashCode() {
        return Objects.hash(itemId, displayName, count);
    }
}
