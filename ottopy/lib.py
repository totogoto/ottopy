from .maze import Maze
from .models.world_model import WorldModel
import time
import ipykernel
MAJ_VERSION = int(ipykernel.__version__.split(".")[0])


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

    def wait_for_init(wait=3):
        if MAJ_VERSION >= 6:
            try: 
                granularity = 0.1
                kernel = get_ipython().kernel
                for x in range(int(wait/granularity)):
                    time.sleep(granularity)
                    kernel.shell_stream.flush()
                    if kernel.msg_queue.qsize() > 0 :
                        sess = kernel.session.clone()
                        for (_,_,i) in kernel.msg_queue._queue:
                            idents, msg = sess.feed_identities(i[0], copy=False)
                            t=sess.deserialize(msg, content=True, copy=False)
                            if t.get("msg_type", "") == "comm_msg":
                                return
            except:
                time.sleep(1.2)
                print("timeout - some bot function may not work")

        else: 
            print("ipykernel is outdated . should be >=6.0")


    def wait_for_bot(level, floating=False, zoom=None, wait=1):
        bot = get_bot(level, floating, zoom)
        maze = bot.world
      
        wait_for_init(wait)
      
        maze.redraw_all()
        bot.set_trace('red')
        return bot

    return wait_for_bot
