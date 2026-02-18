import os
import svgwrite
from cairosvg import svg2png
from jackbox import Jackbox


class Drawful(Jackbox):

    def __init__(self, game_id: str = None, api_account: str = 'dev', dry_run: bool = False):
        super().__init__(game_id=game_id, api_account=api_account, dry_run=dry_run)

        self.data_url = self.gallery_url = 'DrawfulGame'

    def create_image(self, _drawing, _name):
        print(f"INFO: Processing image {_name}")
        dwg = svgwrite.Drawing(profile='tiny', viewBox='0 0 240 320')
        dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), rx=None, ry=None, fill="#FFFFFF"))
        for line in _drawing['lines']:
            if len(line['points']) > 1:
                shape = dwg.polyline(
                    [(point['x'], point['y']) for point in line['points']],
                    stroke=line['color'],
                    fill='none',
                    stroke_width=line['thickness']
                )
            else:
                shape = dwg.circle(
                    center=(line['points'][0]['x'], line['points'][0]['y']),
                    r=2,
                    stroke=line['color'],
                    fill=line['color'],
                    stroke_width=line['thickness']
                )
            dwg.add(shape)
        filename = f"./{self.clean_string(_name)}.png"
        svg2png(bytestring=dwg.tostring(), write_to=filename)
        return filename

    def process_game(self):
        data = super().process_game()
        if data:
            try:
                # Queue intro message first
                self.queue_intro_message()

                # Process player portraits
                for player in data['blob']['playerPortraits']:
                    player_name = player['player']['name']
                    filename = self.create_image(player, player_name)
                    self.queue_file_upload(
                        file=filename,
                        title=player_name
                    )

                # Process drawings
                for drawing in data['blob']['drawings']:
                    filename = self.create_image(
                        drawing,
                        f"{drawing['player']['name']}-{drawing['title']['text']}"
                    )

                    text = "Stare at the art..."
                    self.queue_file_upload(
                        file=filename,
                        title=text
                    )

                    title = drawing['title']['text']
                    blocks = [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": self.clean_string(
                                    f"*Actual Title*: `{title}`\n*Artist*: _{drawing['player']['name']}\n",
                                    underscore=False
                                )
                            }
                        }
                    ]
                    if "lies" in drawing and len(drawing['lies']) > 0:
                        lies = []
                        for lie in drawing['lies']:
                            lies.append(self.clean_string(f"*{lie['player']['name']}*:\t`{lie['text']}`", underscore=False))
                        blocks.append(
                            {
                                "type": "context",
                                "elements": [
                                    {
                                        "type": "mrkdwn",
                                        "text": "\n".join(lies)
                                    }
                                ]
                            }
                        )

                    self.queue_chat_message(
                        text=text,
                        blocks=str(blocks)
                    )

                # All messages prepared successfully, send them
                self.send_queued_messages()

            except Exception as ex:
                print(f"ERROR: Failed to process game: {ex}")
                self.clear_queue(cleanup_files=True)
                raise
