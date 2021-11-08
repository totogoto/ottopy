from .maze import Maze
from .models.world_model import WorldModel


def get_robo_builder(**kwargs):
    levels = kwargs.get("levels", {})
    robo_fn = kwargs.get("robo_fn", {})
    counter = 0

    def blank(world):
        pass

    def load_world(level, floating=False):
        nonlocal counter
        counter += 1
        return WorldModel(f"./worlds/{level}.json", levels.get(level, blank), {'ui_counter': counter, 'floating': floating})

    def bot_init(maze, level):
        bot = maze.bot()
        bot.set_trace('red')
        fn = robo_fn.get(level, blank)
        fn(bot)

    def generate_maze(level, floating=False):
        world = load_world(level, floating=floating)
        maze = Maze(world, floating=floating)
        bot_init(maze, level)
        return maze

    def get_bot(level, floating=False):
        maze = generate_maze(level, floating=floating)
        bot = maze.bot()
        return bot

    return get_bot
