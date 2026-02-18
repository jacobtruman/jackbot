import os
from jackbox import Jackbox


class Quiplash3(Jackbox):

    def __init__(self, game_id: str = None, api_account: str = 'dev', dry_run: bool = False):
        super().__init__(game_id=game_id, api_account=api_account, dry_run=dry_run)

        self.data_url = self.gallery_url = self.base_image_url = self.base_gen_image_url = 'quiplash3Game'

    def process_game(self):
        data = super().process_game()
        if data:
            try:
                # Queue intro message first
                self.queue_intro_message()

                for index, matchup in enumerate(data['blob']['matchups']):
                    filename = f"{self.clean_string(matchup['question']['prompt'])}.{self.ext}"
                    if self.generate_images(index, filename):
                        title = matchup['question']['prompt']
                        quips = [f"*{title}*"]
                        quiplash = False
                        for side in ['left', 'right']:
                            quip = matchup[side]
                            quips.append(f"*{quip['player']['name']}*: _{quip['answer']}_ ({quip['percent']}%)")
                            if quip['quiplash'] is True:
                                quiplash = True
                        if quiplash:
                            quips.append("`QUIPLASH!`")
                        initial_comment = '\n'.join(quips)
                        self.queue_file_upload(
                            file=filename,
                            title=title,
                            initial_comment=initial_comment
                        )
                    else:
                        raise Exception(f"Failed to generate image for matchup {index}")

                # All messages prepared successfully, send them
                self.send_queued_messages()

            except Exception as ex:
                print(f"ERROR: Failed to process game: {ex}")
                self.clear_queue(cleanup_files=True)
                raise
