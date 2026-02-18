import os
from jackbox import Jackbox


class Brk(Jackbox):

    def __init__(self, game_id: str = None, api_account: str = 'dev', dry_run: bool = False):
        super().__init__(game_id=game_id, api_account=api_account, dry_run=dry_run)
        self.ext = 'png'

        self.data_url = self.gallery_url = self.base_image_url = self.base_gen_image_url = 'BRKGame'

        self.game_name = 'Bracketeering'

    def process_game(self):
        data = super().process_game()
        if data:
            try:
                # Queue intro message first
                self.queue_intro_message()

                for bracket_num in data['bracketData']:
                    bracket = data['bracketData'][bracket_num]
                    for index, _ in enumerate(bracket['matchups']):
                        title = f"{bracket['content']['prompt']['text']} {index}"
                        filename = f"{self.clean_string(title)}.{self.ext}"
                        if self.generate_images(f"{bracket_num}_{index}", filename):
                            initial_comment = f"*{title}*"
                            self.queue_file_upload(
                                file=filename,
                                title=title,
                                initial_comment=initial_comment
                            )
                        else:
                            raise Exception(f"Failed to generate image for bracket {bracket_num} matchup {index}")

                # All messages prepared successfully, send them
                self.send_queued_messages()

            except Exception as ex:
                print(f"ERROR: Failed to process game: {ex}")
                self.clear_queue(cleanup_files=True)
                raise
