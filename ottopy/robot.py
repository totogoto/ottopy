from .models.world_model import print_success, print_error
_directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]

dir_names = ["east", "north", "west", "south"]


class Stats():
    def __init__(self, bot):
        self.bot = bot

    def report(self):
        return {
            'max_capacity': self.bot.max_capacity,
            'current_load': len(self.bot.last_picked),
            'total_moves': self.bot.move_count,
            'basket': self.bot.basket()
        }


class Robot():
    def __init__(self, index, robot_model, world):
        self.model = robot_model
        self.world_model = world.model
        self.world = world
        self.index = index
        self.collections = {}
        self.speed = 0.5
        self.last_picked = []
        self.count_report = []
        self.max_capacity = None
        self.move_count = 0
        self.stats = Stats(self)
        self.flag_count = 0

    @property
    def x(self):
        return self.model.x

    @property
    def y(self):
        return self.model.y

    @property
    def dir(self):
        return self.model.orientation

    @dir.setter
    def dir(self, value):
        self.model.orientation = value

    @x.setter
    def x(self, value):
        self.model.x = value

    @y.setter
    def y(self, value):
        self.model.y = value

    def check(self):
        self.world.check()

    def move(self, step=1):
        """Move  in the direction that the bot is facing. 
           Robot can not pass through walls, this instruction will error out if robot is facing a wall 
           and is instructed to move 

        Parameters
        ---------
        step : int
        number of steps to move.(default value is 1)

        Examples
        --------
        For moving one step
        >>> bot.move()

        For moving 10 step
        >>> bot.move(10)
        """
        self.world_model.incr_instruction(step)
        for x in range(step):
            self._move()
        self.world.js_call('move_to', [self.index, self.x, self.y])

    def _move(self):
        if self.front_is_clear():
            xx, yy = _directions[self.dir]
            self.x += xx
            self.y += yy
            self._pick_flag()
            self.move_count += 1
        else:
            self.world.js_call('move_to', [self.index, self.x, self.y])
            print_error("Opps You Hit the walls")
            raise RuntimeError('Opps You Hit the walls')

    def front_is_clear(self):
        """Checks if there is no wall in front of the robot (in the direction it is facing).

        Returns
        -------
        bool
            Returns True if there is no wall in front of the robot.
            False otherwise

        Examples
        --------
        >>> bot.front_is_clear()
        True
        """
        return self.world_model.is_clear(self.x, self.y, self.dir)

    def done(self):
        """Checks if all the goals are completed.

        Returns
        -------
        bool
            Returns True if all the goals are completed.

        Examples
        --------
        >>> bot.done()
        True
        """
        self.world_model.incr_instruction()

        return self.world.model.done(self)

    def turn_left(self):
        """Rotate left by 90 degrees.

        Examples
        --------
        >>> bot.turn_left()
        """
        self.world_model.incr_instruction()
        self.dir = (self.dir + 1) % 4
        self.world.js_call('turn_left', [self.index])

    def right_is_clear(self):
        """Checks if there is no wall to the right of the robot.

        Returns
        -------
        bool
            Returns True if there is no wall to the right of the robot.
            False otherwise

        Examples
        --------
        >>> bot.right_is_clear()
        True
        """

        return self.world.model.is_clear(self.x, self.y, (self.dir + 3) % 4)

    def wall_on_right(self):
        """Checks if there is a wall to the right of the robot.

        Returns
        -------
        bool
            Returns True if there is a wall to the right of the robot.

        Examples
        --------
        >>> bot.wall_on_right()
        True
        """

        return not self.right_is_clear()

    def wall_in_front(self):
        """Checks if there is a wall in front of the robot.

        Returns
        -------
        bool
            Returns True if there is a wall in front of the robot.

        Examples
        --------
        >>> bot.wall_in_front()
        True
        """

        return not self.front_is_clear()

    def report(self, msg):
        """ Reports out a message.

        Parameters
        ---------
        msg : str
        message to report

        Examples
        --------
        >>> bot.report("Counted 10 apples")

        """
        self.count_report.append(msg)
        print_success("{}".format(msg))

    def cell(self):
        return self.world_model.cells[self.x - 1][self.y - 1]

    def build_wall(self):
        """Build a wall in front of the robot. The robot can only build a wall in a few places (shown as a dashed line)     
           If there is already a wall in front of the robot this instruction will error out.
           If the robot can not build a wall (because there is no dashed line) this instruction will error out.

        Examples
        --------
        >>> bot.build_wall()
        """
        self.world_model.incr_instruction()
        cell = self.cell()
        if self.front_is_clear():
            if cell.has_goal_wall(self.dir):
                cell.add_wall(self.dir, self.world.js_call)
        else:
            print_error("Wall Already exists")
            raise RuntimeError("Wall Already exists")

    def remove_wall(self):
        """Removes the wall in front of the robot.
           If there is no wall in front of the robot this instruction will error out. 

        Examples
        --------
        >>> bot.remove_wall()
        """

        self.world_model.incr_instruction()
        if not self.front_is_clear():
            self.cell().remove_wall(self.dir, self.world.js_call)
        else:
            print_error("No Wall exists")
            raise RuntimeError("No Wall exists")

    def set_trace(self, color='red'):
        """
            sets a new trace in that color.

        Examples
        --------
        >>> bot.set_trace('red')
        """

        self.world.js_call('set_trace', [self.index, color])

    def set_speed(self, speed=0.1):
        """
            sets the speed for the bot movement in seconds.

        Examples
        --------
        >>> bot.set_speed(1)
        """

        self.speed = speed
        self.world.js_call('set_speed', [self.index, speed])

    def has_object(self, obj_name=None):
        self.world_model.incr_instruction()
        objs = self.collections.values()
        if len(objs) > 0:
            if obj_name is None:
                return 1
            else:
                fobjs = list(filter(lambda x, y: x == obj_name, objs))
                return sum(fobjs.values())
        else:
            return 0

    def read_message(self, wait_For=5):
        """Check and returns the message in the current cell.
           Also, it takes an optional parameter in seconds for waiting before it disappears.


        Returns
        -------
        str
            Returns the message if there is a message in the current cell.
            None otherwise

        Examples
        --------
        >>> bot.read_message()
        "Hi There"
        >>> bot.read_message(3)
        "Hi There"
        """
        cell = self.cell()
        if self.message_here():
            self.world.js_call("show_message", [cell.msg, wait_For])
        return cell.msg

    def message_here(self):
        """Check if the bot is on the envelope cotaining message."

        Returns
        bool
            Returns True if envelope is present in the current cell.
            False otherwise.
        """
        return self.cell().msg is not None

    def object_here(self):
        """Check and return the name of the object in the current cell.

        Returns
        -------
        str
            Returns the object name if there is an object in the current cell.
            None otherwise

        Examples
        --------
        >>> bot.object_here()
        "apple"
        """
        self.world_model.incr_instruction()
        k = "{},{}".format(self.x, self.y)
        obj = self.world_model.objects.get(k, None)
        collection = self.collections.get(k, None)
        if obj is not None:
            obj_name = next(iter(obj))
            if collection is not None:
                cobj = collection.get(obj_name, None)

                if cobj is not None and cobj == obj[obj_name]:
                    return None
            return obj_name
        else:
            return None

    def carries_object(self):
        """Check if the bot has collected any objects.

        Returns
        -------
        bool
            Returns True if the bot has any object collected.
            False otherwise.

        Examples
        --------
        >>> bot.carries_object()
        True
        """

        return len(self.basket()) > 0

    def basket(self):
        """Returns the list of objects picked by the robot.

        Returns
        -------
        array
            Returns the list of objects picked by the robot.

        Examples
        --------
        >>> bot.basket()
        ["apple"]
        """

        if(len(self.last_picked) > 0):
            return [x[0] for x in self.last_picked]
        else:
            return []

    def at_goal(self):
        """Checks if the bot is at its goal position.

        Returns
        -------
        bool
            Returns True if the bot is at its goal position.
            False otherwise.

        Examples
        --------
        >>> bot.at_goal()
        True
        """

        self.world_model.incr_instruction()
        goal = self.world_model.position_goal()

        if len(goal) > 0:
            goal = goal[0]
            return goal.is_completed(self)
        return False

    def on_flag(self):
        k = "{},{}".format(self.x, self.y)
        return self.world_model.flags.get(k, 0) == 1

    def carries_flag(self):
        return self.flag_count > 1

    def _pick_flag(self):
        if self.on_flag():
            self.flag_count += 1
            self.world_model.remove_flag(self.x, self.y, self.world.js_call)

    def put(self):
        cell = self.cell()
        if not cell.editable["drop"]:
            raise RuntimeError("Can't drop to this Cell")

        self.world_model.incr_instruction()
        if len(self.last_picked) > 0:
            [o_name, ck] = self.last_picked.pop()
            collection = self.collections.get(ck, None)
            if collection is not None and o_name in collection:
                obj = collection.get(o_name, 0)
                if obj > 1:
                    collection[o_name] -= 1
                else:
                    del collection[o_name]
                self.collections[ck] = collection
                k = "{},{}".format(self.x, self.y)
                obj_here = self.world_model.objects.get(
                    k, {}).get(o_name, 0) + 1
                self.world_model.add_object(
                    self.x, self.y, o_name, obj_here, self.world.js_call)

    # change very ref of this method and use object here

    def on_object(self, obj_type=None):
        self.world_model.incr_instruction()
        k = "{},{}".format(self.x, self.y)
        obj = self.world_model.objects.get(k, None)
        valid_type = True
        if obj is not None and obj_type is not None:
            obj_name = next(iter(obj))
            valid_type = obj_name == obj_type

        return obj is not None and valid_type and obj != self.collections.get(k, None)

    def take(self, obj_type=None):
        """Collects one object of the specified type from the current cell.
           This instruction errors out if there is no object in the current cell.
           If specified object type is None it will pick objects of any type.


        Examples
        --------
        >>> bot.take()
        """
        if self.max_capacity is not None and self.max_capacity <= len(self.last_picked):
            raise RuntimeError(
                f"Can't Carry more than {self.max_capacity} items")

        self.world_model.incr_instruction()
        cell = self.cell()
        if not cell.editable["pick"]:
            raise RuntimeError("Can't Pick From this Cell")

        if self.on_object(obj_type):
            ck = "{},{}".format(self.x, self.y)

            obj = self.world_model.objects.get(ck, None)
            if obj is not None:
                for k, val in obj.items():
                    collection = self.collections.get(ck, {})
                    picked = collection.get(k, 0)
                    picked = picked + 1
                    collection[k] = picked
                    self.last_picked.append([k, ck])
                    self.collections[ck] = collection
                    if val == picked:
                        del self.world_model.objects[ck]
                        self.world.js_call('remove_object', [self.x, self.y])
                    if val > picked:
                        self.world.js_call('update_object', [
                                           self.x, self.y, val - picked])
        else:
            print_error("No Items to Pick.")
            raise RuntimeError("No Items to Pick.")
            self.world.js_call('error', ["No Items to Pick"])
