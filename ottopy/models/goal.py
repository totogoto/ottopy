class PositionGoal():
    def __init__(self, config):
        self.x = config.get("x")
        self.y = config.get("y")
    
    def is_completed(self, bot, world=None):
        return self.x == bot.x and self.y == bot.y

    def msg(self):
        return "Expected: Final Position: {},{}".format(self.x, self.y)
    
    def failed_msg(self, bot, world=None):
        return self.msg + " -> " + "Got: Position {},{}".format(bot.x, bot.y)
            

class ReporterGoal():
    def __init__(self, config):
        self.report = config
    
    def is_completed(self, bot, world=None):
        return self.report in bot.count_report

    def msg(self):
        return "Expected: {}".format(self.report)

    def failed_msg(self, bot, world=None):
        return self.msg + " -> " + "Missing: {}".format(self.report)

class WallGoal():
    def __init__(self, config):
        self.directions = config.get("walls", [])
        self.x  = config.get("x")
        self.y = config.get("y")
    
    def is_completed(self, bot, world=None):
        # return sorted(world.added_walls.get(self.xy, [])) == sorted(self.walls)
        cell = world.cells[self.x - 1][self.y - 1]
        return all(cell.has_block(direction) for direction in self.directions)

    def msg(self):
        return "Expected: Build walls at:  {},{}".format(self.x, self.y)
    
    def failed_msg(self, bot, world=None):
        return self.msg()

class ObjectGoal():
    def __init__(self, config):
        self.obj_name = config.get("obj_name")
        self.x  = config.get("x")
        self.y = config.get("y")
        self.val  = config.get('val')

    def is_completed(self, bot, world=None):
        obj = bot.collections.get("{},{}".format(self.x, self.y), {})
        val = obj.get(self.obj_name, 0)
        return self.val == val

    def msg(self):
        return "Expected: Pick object {} at: {},{}".format(self.obj_name, self.x, self.y)

    def failed_msg(self, bot, world=None):
        return self.msg()

class FlagCountGoal():
    def __init__(self, config):
        self.count = config.get("count")
    
    def is_completed(self, bot, world = None):
        return self.count == bot.flag_count
    
    def msg(self):
        return "Expected: {} Flags".format(self.count)
    
    def failed_msg(self):
        return self.msg()



class DropGoal():
    def __init__(self, config):
        self.obj_name = config.get("obj_name")
        self.x  = config.get("x")
        self.y = config.get("y")
        self.val  = config.get('val')

    def is_completed(self, bot, world=None):
        pos = "{},{}".format(self.x,self.y)
        obj = world.objects.get(pos, {})
        val = obj.get(self.obj_name, None)
        return val == self.val

    def msg(self):
        return "Expected: Drop object {} at: {},{}".format(self.obj_name, self.x, self.y)

    def failed_msg(self, bot, world=None):
        return self.msg()



class_list = {
    "position": PositionGoal,
    "wall": WallGoal,
    "object": ObjectGoal,
    "reporter": ReporterGoal,
    "drop": DropGoal,
    "flag_count": FlagCountGoal
}

class Goal(object):
    @staticmethod
    def load(klassType, config):
        klass = class_list.get(klassType)
        return klass(config)
