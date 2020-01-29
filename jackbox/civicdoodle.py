import os
from jackbox import Jackbox


class Civicdoodle(Jackbox):

    def __init__(self, game_id: str = None, dev: bool = False):
        super().__init__(game_id=game_id, dev=dev)

        self.data_url = self.gallery_url = self.base_image_url = self.base_gen_image_url = 'OverdrawnGame'

    def process_game(self):
        data = super().process_game()
        if data:
            intro_message = self.send_intro_message()

            for index, round_data in enumerate(data['rounds']):
                if 'titleVotes' in round_data and 'winningTitle' in round_data['titleVotes']:
                    title = round_data['titleVotes']['winningTitle']
                elif 'artQuestion' in round_data and 'displayText' in round_data['artQuestion']:
                    title = round_data['artQuestion']['displayText']
                else:
                    title = "UNDEFINED"
                filename = f"{self.clean_filename(title)}.{self.ext}"
                if self.generate_images(index, filename):
                    initial_comment = f"*{title}*"
                    self.slack_client.files_upload(file=filename, title=title, channels=self.slack_channel,
                                                   initial_comment=initial_comment, thread_ts=intro_message['ts'])
                    if os.path.exists(filename):
                        os.remove(filename)
