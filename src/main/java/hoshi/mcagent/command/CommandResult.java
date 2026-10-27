package hoshi.mcagent.command;

import hoshi.mcagent.format.ChatPaginator;
import hoshi.mcagent.spatial.SpatialDirectivePacket;

/**
 * Result of routing and executing a player slash command or chat trigger.
 */
public class CommandResult {

    public enum Status {
        SUCCESS,
        THROTTLED,
        ERROR,
        UNKNOWN_SUBCOMMAND
    }

    private final Status status;
    private final String action;
    private final String message;
    private final String commandSuggestion;
    private final String tellrawJson;
    private final ChatPaginator.PagedResult pagedResult;
    private final SpatialDirectivePacket spatialDirective;

    public CommandResult(Status status, String action, String message, String commandSuggestion, String tellrawJson, ChatPaginator.PagedResult pagedResult, SpatialDirectivePacket spatialDirective) {
        this.status = status;
        this.action = action;
        this.message = message;
        this.commandSuggestion = commandSuggestion;
        this.tellrawJson = tellrawJson;
        this.pagedResult = pagedResult;
        this.spatialDirective = spatialDirective;
    }

    public CommandResult(Status status, String action, String message, String commandSuggestion, String tellrawJson, ChatPaginator.PagedResult pagedResult) {
        this(status, action, message, commandSuggestion, tellrawJson, pagedResult, null);
    }

    public static CommandResult success(String action, String message, String commandSuggestion, String tellrawJson, ChatPaginator.PagedResult pagedResult, SpatialDirectivePacket spatialDirective) {
        return new CommandResult(Status.SUCCESS, action, message, commandSuggestion, tellrawJson, pagedResult, spatialDirective);
    }

    public static CommandResult success(String action, String message, String commandSuggestion, String tellrawJson, ChatPaginator.PagedResult pagedResult) {
        return new CommandResult(Status.SUCCESS, action, message, commandSuggestion, tellrawJson, pagedResult, null);
    }

    public static CommandResult throttled(String message) {
        return new CommandResult(Status.THROTTLED, "THROTTLED", message, null, null, null, null);
    }

    public static CommandResult error(String action, String message) {
        return new CommandResult(Status.ERROR, action, message, null, null, null, null);
    }

    public static CommandResult unknown(String message) {
        return new CommandResult(Status.UNKNOWN_SUBCOMMAND, "UNKNOWN", message, null, null, null, null);
    }

    public Status getStatus() { return status; }
    public String getAction() { return action; }
    public String getMessage() { return message; }
    public String getCommandSuggestion() { return commandSuggestion; }
    public String getTellrawJson() { return tellrawJson; }
    public ChatPaginator.PagedResult getPagedResult() { return pagedResult; }
    public SpatialDirectivePacket getSpatialDirective() { return spatialDirective; }

    public boolean hasSpatialDirective() {
        return spatialDirective != null && !spatialDirective.isEmpty();
    }

    public boolean isSuccess() {
        return status == Status.SUCCESS;
    }
}
