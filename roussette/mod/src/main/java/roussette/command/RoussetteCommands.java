package roussette.command;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

import roussette.RoussetteManager;
import roussette.RoussetteMod;
import roussette.core.TempleBuilder;
import roussette.save.RoussetteSaveData;
import roussette.temple.TempleRunner;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** {@code /roussette-temples} and {@code /new-target}. */
@EventBusSubscriber(modid = RoussetteMod.MOD_ID)
public final class RoussetteCommands {

    @SubscribeEvent
    public static void register(RegisterCommandsEvent event) {
        event.getDispatcher().register(temples());
        event.getDispatcher().register(newTarget());
        event.getDispatcher().register(spare());
    }

    /**
     * Builds every temple in the world. Runs <em>once, ever</em>, per world and
     * not per player: the latch flips before the first block is written, so
     * three people typing this in the same second get one set of shrines rather
     * than three carved through each other.
     */
    private static LiteralArgumentBuilder<CommandSourceStack> temples() {
        return Commands.literal("roussette-temples")
                .requires(s -> s.hasPermission(2))
                .executes(ctx -> {
                    CommandSourceStack src = ctx.getSource();
                    ServerLevel level = src.getLevel();
                    RoussetteSaveData data = RoussetteSaveData.get(level);

                    if (!TempleBuilder.canBuildIn(level.dimension().location().toString())) {
                        src.sendFailure(Component.literal(
                                "The shrines are an Overworld thing. Run this there."));
                        return 0;
                    }
                    if (!data.tryStartTemples()) {
                        src.sendFailure(Component.literal(data.temples().refusal()));
                        return 0;
                    }

                    String grid = loadGrid();
                    if (grid == null) {
                        src.sendFailure(Component.literal("Could not read the temple blueprint."));
                        return 0;
                    }

                    TempleRunner runner = new TempleRunner(level, grid, 6000, 12);
                    RoussetteManager.setActiveRun(runner);
                    src.sendSuccess(() -> Component.literal(
                            "Building " + runner.sites().size() + " shrines ("
                            + runner.total() + " blocks). This takes a moment."), true);
                    src.sendSuccess(runner::report, true);
                    return 1;
                });
    }

    /** She outlives her victims. */
    private static LiteralArgumentBuilder<CommandSourceStack> newTarget() {
        return Commands.literal("new-target")
                .requires(s -> s.hasPermission(2))
                .then(Commands.argument("name", StringArgumentType.word())
                        .executes(ctx -> {
                            String name = StringArgumentType.getString(ctx, "name");
                            RoussetteSaveData data = RoussetteSaveData.get(ctx.getSource().getLevel());
                            if (!data.newTarget(name)) {
                                ctx.getSource().sendFailure(Component.literal(
                                        name + " is protected and cannot be hunted."));
                                return 0;
                            }
                            ctx.getSource().sendSuccess(() -> Component.literal(
                                    "She is now hunting " + name + "."), true);
                            return 1;
                        }));
    }

    /** Marks somebody permanently safe. Overrides the taunt rule and /new-target. */
    private static LiteralArgumentBuilder<CommandSourceStack> spare() {
        return Commands.literal("roussette-spare")
                .requires(s -> s.hasPermission(2))
                .then(Commands.argument("name", StringArgumentType.word())
                        .executes(ctx -> {
                            String name = StringArgumentType.getString(ctx, "name");
                            RoussetteSaveData.get(ctx.getSource().getLevel()).protect(name);
                            ctx.getSource().sendSuccess(() -> Component.literal(
                                    name + " is now permanently safe from her."), true);
                            return 1;
                        }));
    }

    private static String loadGrid() {
        try (InputStream in = RoussetteCommands.class.getClassLoader()
                .getResourceAsStream("assets/roussette/temple.txt")) {
            if (in == null) return null;
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return null;
        }
    }

    private RoussetteCommands() {}
}
