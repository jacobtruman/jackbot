import os
from jackbox import Jackbox


class Brk(Jackbox):

    def __init__(self, game_id: str = None, dev: bool = False):
        super().__init__(game_id=game_id, dev=dev)
        self.ext = 'png'

        self.data_url = self.gallery_url = self.base_image_url = self.base_gen_image_url = 'BRKGame'

        self.game_name = 'Bracketeering'

    def process_game(self):
        data = super().process_game()
        if data:
            intro_message = self.send_intro_message()

            for bracket_num in data['bracketData']:
                bracket = data['bracketData'][bracket_num]
                for index, matchup in enumerate(bracket['matchups']):
                    title = f"{bracket['content']['prompt']['text']} {index}"
                    filename = f"{self.clean_filename(title)}.{self.ext}"
                    if self.generate_images(f"{bracket_num}_{index}", filename):
                        initial_comment = f"*{title}*"
                        self.slack_client.files_upload(file=filename, title=title, channels=self.slack_channel,
                                                       initial_comment=initial_comment, thread_ts=intro_message['ts'])
                        if os.path.exists(filename):
                            os.remove(filename)
