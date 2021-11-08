import json
class RobotModel():
    def __init__(self, x, y, orientation = 0, traceColor="red"):
        self.x = x
        self.y = y
        self.orientation = orientation
        self.traceColor = traceColor

    def toJSON(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__,))