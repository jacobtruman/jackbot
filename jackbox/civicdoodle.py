from jackbox.overdrawn import Overdrawn


class Civicdoodle(Overdrawn):

    def __init__(self, game_id: str = None, dev: bool = False):
        super().__init__(game_id=game_id, dev=dev)
