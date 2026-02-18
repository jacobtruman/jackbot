import os
from jackbox import Jackbox


class Overdrawn(Jackbox):

    def __init__(self, game_id: str = None, api_account: str = 'dev', dry_run: bool = False):
        super().__init__(game_id=game_id, api_account=api_account, dry_run=dry_run)

        self.data_url = self.gallery_url = self.base_image_url = self.base_gen_image_url = 'OverdrawnGame'

        self.game_name = 'Civic Doodle'

    def process_game(self):
        data = super().process_game()
        if data:
            try:
                # Queue intro message first
                self.queue_intro_message()

                for index, round_data in enumerate(data['rounds']):
                    if 'titleVotes' in round_data and 'winningTitle' in round_data['titleVotes']:
                        title = round_data['titleVotes']['winningTitle']
                    elif 'artQuestion' in round_data and 'displayText' in round_data['artQuestion']:
                        title = round_data['artQuestion']['displayText']
                    else:
                        title = "UNDEFINED"
                    filename = f"{self.clean_string(title)}.{self.ext}"
                    if self.generate_images(index, filename):
                        initial_comment = f"*{title}*"
                        self.queue_file_upload(
                            file=filename,
                            title=title,
                            initial_comment=initial_comment
                        )
                    else:
                        raise Exception(f"Failed to generate image for round {index}")

                # All messages prepared successfully, send them
                self.send_queued_messages()

            except Exception as ex:
                print(f"ERROR: Failed to process game: {ex}")
                self.clear_queue(cleanup_files=True)
                raise
