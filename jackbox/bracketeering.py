from jackbox.brk import Brk


class Bracketeering(Brk):

    def __init__(self, game_id: str = None, dev: bool = False):
        super().__init__(game_id=game_id, dev=dev)
