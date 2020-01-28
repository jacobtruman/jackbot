import os
import requests
from jackbox import Jackbox


class Quiplash2(Jackbox):

    def __init__(self, game_id: str = None, dev: bool = False):
        super().__init__(game_id=game_id, dev=dev)

        self.data_url = 'https://fishery.jackboxgames.com/artifact/Quiplash2Game'
        self.gallery_url = 'http://games.jackbox.tv/artifact/Quiplash2Game'

    def generate_images(self, index):
        url = f"https://fishery.jackboxgames.com/artifact/gif/Quiplash2Game/{self.game_id}/{index}"
        r = requests.get(url)

        if r.status_code != 200:
            print(f"ERROR: There was a problem generating image:\n{r.status_code}\t{r.text}")
            return False
        return True

    def process_game(self):
        data = super().process_game()
        if data:
            self.send_intro_message()

            image_base_url = "https://s3.amazonaws.com/jbg-blobcast-artifacts/Quiplash2Game"
            for index, matchup in enumerate(data['matchups']):
                ext = "gif"
                image_urls = {
                    "gif": f"{image_base_url}/{self.game_id}/anim_{index}.gif",
                    "png": f"{image_base_url}/{self.game_id}/image-{matchup['question']['id']}-null.png"
                }

                if self.generate_images(index):
                    filename = f"{self.clean_filename(matchup['question']['prompt'])}.{ext}"
                    print(f"INFO: Getting image {image_urls[ext]}")
                    r = requests.get(image_urls[ext])

                    if r.status_code == 200:
                        with open(filename, 'wb') as f:
                            f.write(r.content)

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
                        self.slack_client.files_upload(file=filename, title=title, channels=self.slack_channel,
                                                       initial_comment=initial_comment)
                        if os.path.exists(filename):
                            os.remove(filename)
                    else:
                        print(f"ERROR: There was a problem getting the image {image_urls[ext]}")
