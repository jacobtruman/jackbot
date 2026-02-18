import os
from jackbox import Jackbox

class Range(Jackbox):

    def __init__(self, game_id: str = None, api_account: str = 'dev', dry_run: bool = False):
        super().__init__(game_id=game_id, api_account=api_account, dry_run=dry_run)

        self.data_url = self.gallery_url = self.base_image_url = self.base_gen_image_url = "RangeGameGame"
        self.ext = 'png'
        self.game_name = 'Nonsensory'


    def process_game(self):
        data = super().process_game()
        if data:
            try:
                # Queue intro message first
                self.queue_intro_message()

                players = {player.get("sessionId"): player for player in data.get("blob").get("players")}

                for round_data in data.get("blob").get("roundData"):
                    prompts = {prompt.get('id'): prompt for prompt in round_data.get("prompts")}
                    for index, response in enumerate(round_data.get("responses")):
                        player = players.get(response.get("authorSessionId")).get("name")
                        prompt = prompts.get(response.get('promptId'))
                        round_name = f"round_{round_data.get('index')}_{index}"
                        text = prompt.get("rangeType").get("values")[response.get("targetValueIndex")].get("guessingText")
                        image_urls = {
                            self.ext: f"{self.base_image_url}/round_{round_data.get('index')}_{index}.{self.ext}"
                        }
                        filename = f"{round_name}.{self.ext}"
                        if self.generate_images(round_name, filename, image_urls=image_urls):
                            self.queue_file_upload(
                                file=filename,
                                title=f"Brought to to you by: {player}",
                                initial_comment=f"Prompt text: {text}"
                            )
                        else:
                            raise Exception(f"Failed to generate image for {round_name}")

                # All messages prepared successfully, send them
                self.send_queued_messages()

            except Exception as ex:
                print(f"ERROR: Failed to process game: {ex}")
                self.clear_queue(cleanup_files=True)
                raise