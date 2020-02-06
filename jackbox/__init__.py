import json
import slack
import re
import sys
import requests
from pathlib import Path


class Jackbox:

    def __init__(self, game_id: str = None, dev: bool = False):
        self.dev = dev
        self.ext = 'gif'
        config_file = f'{str(Path.home())}/.config/jackbot/config.json'
        try:
            with open(config_file) as file:
                config_json = json.loads(file.read())
        except FileNotFoundError as _fe:
            sys.exit(f"ERROR: config file not found {config_file}:\n\t{_fe}")
        except json.decoder.JSONDecodeError as _je:
            sys.exit(f"ERROR: invalid config file format {config_file}:\n\t{_je}")

        if self.dev:
            config = config_json['dev']
        else:
            config = config_json['prod']

        self.slack_channel = config['slack_channel']
        self.slack_client = slack.WebClient(token=config['slack_token'])

        self._fishery_url = "https://fishery.jackboxgames.com/artifact"
        self._data_url = None
        self._gallery_url = None
        self._base_image_url = None
        self._base_gen_image_url = None

        self._game_id = None
        self.game_id = game_id
        self._game_name = None
        self._max_attempts = 5

    @property
    def game_id(self):
        if self._game_name is None:
            self.game_name = self.__class__.__name__
        return self._game_id

    @game_id.setter
    def game_id(self, value):
        self._game_id = value.strip().strip("/").split("/")[-1]

    @property
    def data_url(self):
        return self._data_url

    @data_url.setter
    def data_url(self, value):
        self._data_url = f"{self._fishery_url}/{value}/{self.game_id}"

    @property
    def gallery_url(self):
        return self._gallery_url

    @gallery_url.setter
    def gallery_url(self, value):
        self._gallery_url = f"http://games.jackbox.tv/artifact/{value}/{self.game_id}"

    @property
    def base_image_url(self):
        return self._base_image_url

    @base_image_url.setter
    def base_image_url(self, value):
        self._base_image_url = f"https://s3.amazonaws.com/jbg-blobcast-artifacts/{value}/{self.game_id}"

    @property
    def base_gen_image_url(self):
        return self._base_gen_image_url

    @base_gen_image_url.setter
    def base_gen_image_url(self, value):
        self._base_gen_image_url = f"{self._fishery_url}/{self.ext}/{value}/{self.game_id}"

    @property
    def game_name(self):
        return self._game_name

    @game_name.setter
    def game_name(self, value):
        self._game_name = re.sub(r"([A-Z,0-9])", r" \1", value).strip()

    @staticmethod
    def parse_game_url(url):
        url_parts = url.strip("/").split("/")
        return url_parts[-2].replace("Game", ""), url_parts[-1]

    @staticmethod
    def clean_string(_string, underscore=True):
        pattern = re.compile(r'<[^>]+>')
        _string = pattern.sub('', _string)
        chars = ["'", '"', ",", "`", "’", '“', '”', ":", ";", "_"]
        for char in chars:
            _string = _string.replace(char, "").strip()
        special_chars = [("Ñ", "N"), ("Ï", "I"), ("Æ", "AE")]
        for char, _char in special_chars:
            _string = _string.replace(char, _char)
        if underscore:
            _string = _string.replace(' ', '_')
        return _string

    def process_game(self):
        r = requests.get(self.data_url)
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            print(f"ERROR: Invalid response from server for url {self.data_url}: ({r.status_code}) {r.text}")
            return False

    def generate_images(self, index, filename, attempt=0):
        image_urls = {
            "gif": f"{self.base_image_url}/anim_{index}.gif",
            "png": f"{self.base_image_url}/image_{index}.png"
        }

        if self.ext == 'gif':
            url = f"{self.base_gen_image_url}/{index}"
            r = requests.get(url)

            print(f"INFO: Generating image {url}")
            if r.status_code != 200:
                attempt += 1
                print(f"ERROR: There was a problem generating image:\n{r.status_code}\t{r.text}\n"
                      f"Attempt: {attempt} / {self._max_attempts}")
                if attempt < self._max_attempts:
                    return self.generate_images(index, filename, attempt)
                return False

        print(f"INFO: Getting image {image_urls[self.ext]}")
        r2 = requests.get(image_urls[self.ext])
        if r2.status_code != 200:
            print(f"ERROR: There was a problem getting image:\n{r2.status_code}\t{r2.text}")
            return False
        else:
            with open(filename, 'wb') as f:
                f.write(r2.content)

        return True

    def send_intro_message(self):
        blocks = str([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{self.game_name}*"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": self.gallery_url
                    }
                ]
            }
        ])

        return self.slack_client.chat_postMessage(channel=self.slack_channel, text=self.gallery_url, blocks=blocks)
