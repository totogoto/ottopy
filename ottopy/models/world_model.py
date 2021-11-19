from .robot_model import RobotModel
from .world_parser import WorldParser

from IPython.display import HTML as html_print
from IPython.display import display

import json
from enum import Enum, IntFlag
from functools import partial
from .tile_map import DEFAULT_TILE_MAP


from .goal import class_list, Goal, PositionGoal, DropGoal


def cstr(s, color='black'):
    return "<text style=color:{}>{}</text>".format(color, s)


def print_success(msg, color="blue"):
    if msg is not None:
        display(html_print(
            cstr("\N{speech balloon} {}".format(msg), color=color)))


def print_error(error):
    if error is not None:
        display(html_print(cstr("✗ {}".format(error), color="red")))


MAX_ROWS = 20
MAX_COLS = 20


class WallType(IntFlag):
    NORMAL = 1
    REMOVABLE = 2
    GOAL = 4


class Direction(Enum):
    EAST = 0
    NORTH = 1
    WEST = 2
    SOUTH = 3

    @classmethod
    def get_dir(cls, direction):
        if isinstance(direction, Direction):
            return direction
        elif isinstance(direction, str):
            return Direction[direction.upper()]
        elif isinstance(direction, int):
            return Direction(direction)


class Cell:
    def __init__(self, x, y, world, background=None, msg=None):
        self.x = x
        self.y = y
        self.world = world
        self.background = background
        self.msg = msg
        self.editable = {"pick": True, "drop": True}

    def walls_list(self, direction):
        direction = Direction.get_dir(direction)
        if direction == Direction.EAST or direction == Direction.WEST:
            return self.world.vwalls

        if direction == Direction.NORTH or direction == Direction.SOUTH:
            return self.world.hwalls

    def wall_cord(self, direction):
        direction = Direction.get_dir(direction)
        if direction == Direction.EAST or direction == Direction.NORTH:
            return [self.x, self.y]

        if direction == Direction.WEST:
            return [self.x - 1, self.y]

        if direction == Direction.SOUTH:
            return [self.x, self.y - 1]

    def ui_direction(self, direction):
        direction = Direction.get_dir(direction)
        if direction == Direction.EAST or direction == Direction.WEST:
            return "east"

        if direction == Direction.NORTH or direction == Direction.SOUTH:
            return "north"

    def set_wall(self, direction, val):
        direction = Direction.get_dir(direction)
        [x, y, ui_dir] = self.wall_ui_params(direction)
        if isinstance(val, WallType):
            val = val.value

        # if WallType(val) in WallType.GOAL:
        #     self.world._add_goal("wall",  {"x":x, "y": y, "walls": [ui_dir]} )

        if direction == Direction.EAST or direction == Direction.WEST:
            self.world.vwalls[x][y] = val

        if direction == Direction.NORTH or direction == Direction.SOUTH:
            self.world.hwalls[x][y] = val

    def get_wall(self, direction):
        walls = self.walls_list(direction)
        [x, y] = self.wall_cord(direction)
        return walls[x][y]

    def wall_ui_params(self, direction):
        [x, y] = self.wall_cord(direction)
        return [x, y, self.ui_direction(direction)]

    def add_wall(self, direction, call_js=None, wall_type="normal"):

        if wall_type == "removable":
            RN = WallType.REMOVABLE | WallType.NORMAL
            self.set_wall(direction, RN)
        elif wall_type == "goal":
            self.set_wall(direction, WallType.GOAL)
        else:
            self.set_wall(direction, WallType.NORMAL.value)

        if call_js is not None:
            call_js('add_wall', self.wall_ui_params(direction))

    def add_removable_wall(self, direction, call_js=None):
        self.add_wall(self, direction, call_js, "removable")

    def add_goal_wall(self, direction, call_js=None):
        self.add_wall(direction, call_js, "goal")

    def set_as_goal(self, direction):
        val = self.get_wall(direction)
        VW = WallType(val) | WallType.GOAL
        self.set_wall(direction, VW)

    def set_as_removable(self, direction):
        val = self.get_wall(direction)
        VW = WallType(val) | WallType.REMOVABLE
        self.set_wall(direction, VW)

    def remove_wall(self, direction, call_js=None):
        self.set_wall(direction, 0)
        if call_js is not None:
            call_js('remove_wall', self.wall_ui_params(direction))

    def add_msg(self, msg, call_js=None):
        self.msg = msg
        if call_js is not None:
            call_js('add_msg', [self.x, self.y, self.msg])

    def has_wall(self, direction):
        walls = self.walls_list(direction)
        [x, y] = self.wall_cord(direction)
        wall_type = WallType(walls[x][y])
        return WallType.NORMAL in wall_type

    def has_goal_wall(self, direction):
        walls = self.walls_list(direction)
        [x, y] = self.wall_cord(direction)
        wall_type = WallType(walls[x][y])
        return WallType.GOAL in wall_type

    def has_border(self, direction):
        direction = Direction.get_dir(direction)

        if direction == Direction.EAST and self.x == self.world.cols:  # east
            return True
        if direction == Direction.NORTH and self.y == self.world.rows:  # north
            return True
        if direction == Direction.WEST and self.x - 1 == 0:  # west
            return True
        if direction == Direction.SOUTH and self.y - 1 == 0:  # south
            return True
        return False

    def has_block(self, direction):
        return self.has_border(direction) or self.has_wall(direction)


class WorldModel():
    def __init__(self, path=None, initFn=None, options={}):
        self.objects = {}
        self.robots = []
        self.errors = []
        self.goals = []
        self.description = None
        self.project_title = None
        self.set_dimensions(10, 10)
        self.options = {'MAX_INSTRUCTION_COUNT': 1000}
        self.instruction_count = 0
        self.options.update(options)
        self.js_call_counter = 1
        self.messages = {}
        self.flags = {}
        self.border_color = 'darkred'
        self.grid_line_color = 'gray'
        self.is_checked = False
        self.floating = self.options.get('floating', False)
        self.ui_id = f"ttgt_world_{self.options.get('ui_counter', 1)}"

        if path is not None:
            data = self.load_json(path)

            parser = WorldParser.parse(self, data)

        if initFn is not None and callable(initFn):
            initFn(self)

    def load_json(self, path):
        f = open(path, "r")
        data = json.loads(f.read())
        f.close()
        return data

    def max_instruction_count(self):
        return self.options['MAX_INSTRUCTION_COUNT']

    def set_quota(self, val):
        self.options['MAX_INSTRUCTION_COUNT'] = val

    def incr_instruction(self, n=1):
        self.instruction_count += n

    def has_balance(self):
        return self.max_instruction_count() > self.instruction_count

    def js_call(self, call_js_fn=None, method_name=None, params=[]):
        if call_js_fn is not None and callable(call_js_fn):
            call_js_fn(method_name, params)

    def set_dimensions(self, rows=10, cols=10):
        self.rows = min(rows, MAX_ROWS)
        self.cols = min(cols, MAX_COLS)
        self.hwalls = [x[:] for x in [[0] * (self.rows + 1)] * (self.cols + 1)]
        self.vwalls = [x[:] for x in [[0] * (self.rows + 1)] * (self.cols + 1)]
        self.tiles = [x[:] for x in [[None] * (self.rows)] * (self.cols)]
        self.cells = []
        for i in range(self.cols):
            self.cells.append([])
            for j in range(self.rows):
                self.cells[i].append(Cell(i+1, j+1, self))

    def add_tile_map(self, tilemap=None):
        self.tilemap = dict()
        self.tilemap.update(DEFAULT_TILE_MAP)
        if tilemap is not None:
            self.tilemap.update(tilemap)

    def add_tile(self, x, y, background, call_js=None):
        cell = self.cells[x - 1][y - 1]
        cell.background = background
        self.tiles[x - 1][y - 1] = background

    def add_msg(self, x, y, msg, call_js=None):
        pos = "{},{}".format(x, y)
        self.messages[pos] = msg
        cell = self.cells[x - 1][y - 1]
        cell.add_msg(msg, call_js)

    def add_flag(self, x, y, call_js=None):
        pos = "{},{}".format(x, y)
        self.flags[pos] = 1

    def remove_flag(self, x, y, call_js=None):
        pos = "{},{}".format(x, y)
        del self.flags[pos]
        self.js_call(call_js, 'remove_flag', [x, y])

    def add_description(self, desc):
        if isinstance(desc, list):
            self.description = '\n'.join(desc)
        else:
            self.description = desc

    def add_wall(self, x, y, direction, call_js=None, wall_type=WallType.NORMAL):
        cell = self.cells[x - 1][y - 1]
        # js_call
        call_fn = partial(self.js_call, call_js)
        cell.add_wall(direction, call_fn, wall_type)

    def add_goal_wall(self, x, y, direction, call_js=None):
        cell = self.cells[x - 1][y - 1]
        cell.add_goal_wall(direction, call_js)

    def remove_wall(self, x, y, direction, call_js=None):
        cell = self.cells[x - 1][y - 1]
        cell.remove_wall(direction)

    def add_object(self, x, y, obj_name, val, call_js=None):
        obj = {}
        obj[obj_name] = val
        pos = "{},{}".format(x, y)
        self.objects[pos] = obj

        # js_call
        self.js_call(call_js, "add_object", [x, y, obj_name, val])

    def add_robot(self, x, y, orientation, traceColor):
        self.robots.append(RobotModel(x, y, orientation, traceColor))

    def add_goal(self, goal):
        if isinstance(goal, tuple(class_list.values())):
            self.goals.append(goal)
        else:
            raise "Not a valid goal class"

    def add_repoter_goal(self, msg):
        self._add_goal("reporter", msg)

    def add_flag_count_goal(self, count):
        self._add_goal('flag_count', {'count': count})

    def add_drop_obj_goal(self, x, y, obj_name, val):
        self._add_goal(
            'drop', {"x": x, "y": y, "val": val, "obj_name": obj_name})

    def add_pick_obj_goal(self, x, y, obj_name, val):
        self._add_goal('object', {"x": x, "y": y,
                       "val": val, "obj_name": obj_name})

    def add_home_goal(self, x, y, image="house"):
        self._add_goal('position', {"x": x, "y": y})
        self.add_tile(x, y, "house")

    def _add_goal(self, goal_type,  config):
        goal = Goal.load(goal_type, config)
        self.add_goal(goal)

    def position_goal(self):
        return list(filter(lambda goal: isinstance(goal, PositionGoal), self.goals))

    def drop_goals(self):
        return list(filter(lambda goal: isinstance(goal, DropGoal), self.goals))

    def drop_allowed(self, x, y, val=False):
        cell = self.cells[x - 1][y - 1]
        cell.editable["drop"] = val

    def pick_allowed(self, x, y, val=False):
        cell = self.cells[x - 1][y - 1]
        cell.editable["pick"] = val

    def dimensions(self):
        return [self.rows, self.cols]

    def is_clear(self, x, y, dir):
        cell = self.cells[x - 1][y - 1]
        return not cell.has_block(dir)

    def done(self, bot):
        return all(goal.is_completed(bot, self) for goal in self.goals)

    def check(self, bot):
        if self.is_checked == True:
            raise RuntimeError("Already Checked once.")
        sucess = True
        for goal in self.goals:
            if not goal.is_completed(bot, self):
                sucess = False
                print_error(goal.msg())
            else:
                print_success(goal.msg())
        self.is_checked = True
        return sucess

    def world_properties(self):
        return {
            'border_color': self.border_color,
            'grid_line_color': self.grid_line_color,
            'floating': self.floating
        }

    def render_all(self, js_call=None):
        self.js_call(js_call, 'draw_all', [
            self.world_properties(),
            self.ui_id,
            self.rows,
            self.cols,
            self.vwalls,
            self.hwalls,
            [r.toJSON() for r in self.robots],
            self.objects,
            self.tilemap,
            self.tiles,
            self.messages,
            self.flags,
            [x.msg() for x in self.goals],
            [{"obj_name": x.obj_name, "x": x.x, "y": x.y, "val": x.val}
                for x in self.drop_goals()]
        ])
