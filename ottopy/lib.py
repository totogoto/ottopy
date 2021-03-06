from .maze import Maze
from .models.world_model import WorldModel
import time
import ipykernel
from string import Template

MAJ_VERSION = int(ipykernel.__version__.split(".")[0])

html_template = Template("""
<!doctype html>
<html>
<head>
  <meta charset="UTF-8">
  <title>OttoPy Output Runner</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/totogoto/ottopy_runner@latest/public/css/style.css">
</head>
<body>
  <div id="runner_body">
    <div class="runner-header">
      <span class="h3">Project: $project_name</span>
      <button class="play-btn" onclick="play()"> Play </button>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/gh/totogoto/ottopy_runner@latest/dist/runner.js"></script>
  <script> 
  let steps = []
  function play(){
    $('#outputArea').remove()
    const instance = new Runner()
    steps.map(s => instance._js_call(s))
  } 
  </script>
""")


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

    def generate_maze(level, floating=False, zoom=None, gen_html=False):
        world = load_world(level, floating=floating)
        maze = Maze(world, floating=floating, zoom=zoom, gen_html=gen_html)
        bot_init(maze, level)
        return maze

    def get_bot(level, floating=False, zoom=None, gen_html=False):
        maze = generate_maze(level, floating=floating, zoom=zoom, gen_html=gen_html)
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

    def create_html_file(project_name):
        with open('last_run.html', 'w') as f:
            f.write(html_template.safe_substitute(project_name=project_name))


    def wait_for_bot(level, floating=False, zoom=None, wait=1, gen_html=False):
        bot = get_bot(level, floating, zoom, gen_html=gen_html)
        maze = bot.world

        wait_for_init(wait)
        if gen_html:
            project_name =  maze.model.project_title if maze.model.project_title else level
            create_html_file(project_name=project_name)
      
        maze.redraw_all()
        bot.set_trace('red')
        return bot

    return wait_for_bot
