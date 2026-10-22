package hoshi.mcagent.crafting;

import java.util.Collections;
import java.util.Map;

/**
 * Standard recipe specification with material costs and alternative crafting paths.
 */
public record CraftingRecipe(
        String recipeId,
        String displayName,
        String category,
        int outputCount,
        Map<String, Integer> ingredients,
        String craftTip
) {
    public CraftingRecipe {
        if (ingredients == null) {
            ingredients = Collections.emptyMap();
        }
    }
}
