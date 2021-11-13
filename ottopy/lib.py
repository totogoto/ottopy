from .maze import Maze
from .models.world_model import WorldModel
import asyncio
import ipython_blocking

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

    def generate_maze(level, floating=False, zoom=None):
        world = load_world(level, floating=floating)
        maze = Maze(world, floating=floating, zoom=zoom)
        bot_init(maze, level)
        return maze

    def get_bot(level, floating=False, zoom=None):
        maze = generate_maze(level, floating=floating, zoom=zoom)
        bot = maze.bot()
        return bot
    

    async def wait_for_init(widget, sleep=0.05):
        isInited = False
        def on_inited(button):
            nonlocal isInited
            isInited = True
            widget.unobserve(on_inited, 'is_inited')
        
        widget.observe(on_inited, 'is_inited')
        async def runner():
            ctx = ipython_blocking.CaptureExecution(replay=True)
            with ctx:
                while True:
                    await asyncio.sleep(sleep)
                    if isInited:
                        break
                    ctx.step() # handles all other messages that aren't 'execute_request' including widget value changes
        return await asyncio.create_task(runner())

    async def wait_for_bot(level, floating=False, zoom=None):
        bot = get_bot(level, floating, zoom)
        maze = bot.world
        await wait_for_init(maze)
        return bot

    return wait_for_bot
