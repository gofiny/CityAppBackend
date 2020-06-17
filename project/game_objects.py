from uuid import uuid4


class BaseObject:
    def __init__(self, uuid=None):
        if uuid:
            self.uuid = uuid
        else:
            self.uuid = uuid4()
        

class Tree(BaseObject):
    def __init__(self, *args, **kwargs):
        self.name = "tree"
        self.object_type = "generated"
        self.health = 100
        super().__init__(*args, **kwargs)


class Rock(BaseObject):
    def __init__(self, *args, **kwargs):
        self.name = "rock"
        self.object_type = "generated"
        self.health = 100
        super().__init__(*args, **kwargs)


class Spawn(BaseObject):
    def __init__(self,  *args, **kwargs):
        self.name = "spawn"
        self.object_type = "static"
        self.health = 1000
        super().__init__(*args, **kwargs)

    


get_gameobject_by_name = {
    "tree": Tree,
    "rock": Rock,
    "spawn": Spawn
}
