from uuid import uuid4


class Tree:
    def __init__(self):
        self.uuid = uuid4()
        self.name = "tree"
        self.object_type = "generated"
        self.health = 100


class Rock:
    def __init__(self):
        self.uuid = uuid4()
        self.name = "rock"
        self.object_type = "generated"
        self.health = 100


class Spawn:
    def __init__(self):
        self.uuid = uuid4()
        self.name = "spawn"
        self.object_type = "static"
        self.health = 1000


get_gameobject_by_name = {
    "tree": Tree,
    "rock": Rock,
    "spawn": Spawn
}
