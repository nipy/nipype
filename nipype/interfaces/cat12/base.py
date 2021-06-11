class Cell:
    def __init__(self, arg):
        self.arg = arg

    def to_string(self):
        if isinstance(self.arg, list):
            v = "\n".join([f"'{el}'" for el in self.arg])
        else:
            v = self.arg
        return v


class NestedCell(Cell):
    def __str__(self):
        return "{{%s}}" % self.to_string()
