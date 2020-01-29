import json
import slack
import re
import sys
import requests
from pathlib import Path


class Jackbox:

    def __init__(self, game_id: str = None, dev: bool = False):
        self.dev = dev
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

        self._data_url = None
        self._gallery_url = None

        self._game_id = None
        self.game_id = game_id
        self._game_name = None
        self.game_name = self.__class__.__name__

    @property
    def game_id(self):
        return self._game_id

    @game_id.setter
    def game_id(self, value):
        self._game_id = value.strip().strip("/").split("/")[-1]

    @property
    def data_url(self):
        return self._data_url

    @data_url.setter
    def data_url(self, value):
        self._data_url = f"https://fishery.jackboxgames.com/artifact/{value}/{self.game_id}"

    @property
    def gallery_url(self):
        return self._gallery_url

    @gallery_url.setter
    def gallery_url(self, value):
        self._gallery_url = f"http://games.jackbox.tv/artifact/{value}/{self.game_id}"

    @property
    def game_name(self):
        return self._game_name

    @game_name.setter
    def game_name(self, value):
        self._game_name = re.sub(r"([A-Z,0-9])", r" \1", value).strip()

    @staticmethod
    def clean_filename(_filename):
        pattern = re.compile(r'<[^>]+>')
        _filename = pattern.sub('', _filename)
        chars = ["'", '"', ",", "`", "’", '“', '”', ":", ";", "_"]
        for char in chars:
            _filename = _filename.replace(char, "").strip()
        special_chars = [("Ñ", "N"), ("Ï", "I"), ("Æ", "AE")]
        for char, _char in special_chars:
            _filename = _filename.replace(char, _char)
        return _filename.replace(' ', '_')

    def process_game(self):
        r = requests.get(self.data_url)
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            print(f"ERROR: Invalid response from server for url {self.data_url}: ({r.status_code}) {r.text}")
            return False

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
