from jackbox.overdrawn import Overdrawn


class Civicdoodle(Overdrawn):

    def __init__(self, game_id: str = None, api_account: str = 'dev'):
        super().__init__(game_id=game_id, api_account=api_account)
