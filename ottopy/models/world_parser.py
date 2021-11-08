import random
from .goal import Goal


class WorldParser:
    def __init__(self, world, config):
        self.world = world
        self.config = config

    @staticmethod
    def parse(world, config):
        parser = WorldParser(world, config)
        parser.parse_world()
        return parser

    def parse_world(self):
        self.parse_dimensions()
        self.parse_scene_config()
        self.parse_tilemaps()
        self.parse_walls()
        self.parse_tiles()
        self.parse_messages()
        self.parse_robots()
        self.parse_objects()
        self.parse_flags()
        self.parse_goals()
        self.parse_description()

    def parse_scene_config(self):
        self.world.border_color = self.config.get('border_color', 'darkred'),
        self.world.grid_line_color = self.config.get('grid_line_color', 'gray')

    def parse_tilemaps(self):
        tilemaps = self.config.get('tileMaps', None)
        self.world.add_tile_map(tilemaps)

    def parse_dimensions(self):
        rows = self.parse_val(self.config["rows"])
        cols = self.parse_val(self.config["cols"])
        self.world.set_dimensions(rows, cols)

    def parse_tiles(self):
        tiles = self.config.get("tiles", {})
        for pos, tile in tiles.items():
            [x, y] = map(int, pos.split(","))
            if isinstance(tile, str):
                self.world.add_tile(x, y, [tile])
            if isinstance(tile, list):
                self.world.add_tile(x, y, tile)

    def parse_walls(self):
        walls = self.config.get("walls", {})
        for pos, wall in walls.items():
            [x, y] = map(int, pos.split(","))
            for direction in wall:
                self.world.add_wall(x, y, direction)

    def parse_objects(self):
        objects = self.config.get('objects', {})
        for pos, obj in objects.items():
            for obj_name, val in obj.items():
                parsed_val = self.parse_val(val)
                [x, y] = map(int, pos.split(","))
                self.world.add_object(x, y, obj_name, parsed_val)

    def parse_flags(self):
        flags = self.config.get('flags', [])
        for pos in flags:
            [x, y] = map(int, pos)
            self.world.add_flag(x, y)

    def parse_messages(self):
        messages = self.config.get('messages', {})
        for pos, msg in messages.items():
            [x, y] = map(int, pos.split(","))
            self.world.add_msg(x, y, msg)

    def parse_val(self, value):
        if isinstance(value, list):
            #eg [1,3,5]
            return random.choice(value)
        elif isinstance(value, str) and "-" in value:
            # eg "1-10"
            min_val, max_val = map(int, value.split("-"))
            return random.randint(min_val, max_val)
        else:
            return int(value)

    def parse_robots(self):
        robots = self.config.get('robots', [])
        for robot in robots:
            x = robot.get('x')
            y = robot.get('y')
            positions = robot.get('possible_initial_positions', None)
            if positions is not None and isinstance(positions, list) and len(positions) > 0:
                x, y = random.choice(positions)

            self.world.add_robot(x, y, robot.get(
                '_orientation', 0), robot.get('_traceColor', 'red'))

    def parse_goals(self):
        goals = self.config.get('goal', {})

        self.add_position_goal(goals)
        self.add_wall_goals(goals.get('walls', {}))
        self.add_object_goals(goals.get('objects', {}))

    def add_position_goal(self, goals):
        position_goal = goals.get('possible_final_positions', [])
        if len(position_goal) > 0:
            x, y = random.choice(position_goal)
            self.world._add_goal('position', {"x": x, "y": y})
        elif goals.get('position', None) is not None:
            pos = goals.get('position', None)
            self.world._add_goal('position', pos)
            image = pos.get("image", None)
            if image is not None:
                x = self.parse_val(pos["x"])
                y = self.parse_val(pos["y"])
                self.world.add_tile(x, y, image)

    def add_wall_goals(self, walls={}):
        for xy, wall in walls.items():
            [x, y] = map(int, xy.split(","))
            self.world._add_goal('wall', {"x": x, "y": y, "walls": wall})

    def add_object_goals(self, objects={}):
        for xy, obj in objects.items():
            [x, y] = map(int, xy.split(","))
            for obj_name, val in obj.items():
                self.world._add_goal(
                    'object', {"x": x, "y": y, "val": val, "obj_name": obj_name})

    def parse_description(self):
        self.world.add_description(self.config.get("description"))
