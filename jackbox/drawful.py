import os
import svgwrite
from cairosvg import svg2png
from jackbox import Jackbox


class Drawful(Jackbox):

    def __init__(self, game_id: str = None, dev: bool = False):
        super().__init__(game_id=game_id, dev=dev)

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
        filename = f"./{self.clean_filename(_name)}.png"
        svg2png(bytestring=dwg.tostring(), write_to=filename)
        return filename

    def process_game(self):
        data = super().process_game()
        if data:
            intro_message = self.send_intro_message()

            for player in data['playerPortraits']:
                player_name = player['player']['name']
                filename = self.create_image(player, player_name)

                self.slack_client.files_upload(file=filename, title=player_name, channels=self.slack_channel,
                                               thread_ts=intro_message['ts'])
                if os.path.exists(filename):
                    os.remove(filename)

            for drawing in data['drawings']:
                filename = self.create_image(
                    drawing,
                    f"{drawing['player']['name']}-{drawing['title']['text']}"
                )

                initial_comment = ""
                title = drawing['title']['text']
                if "lies" in drawing:
                    lies = [f"*Actual Title*: `{title}`\n*Artist*: _{drawing['player']['name']}_\n"]
                    for lie in drawing['lies']:
                        lies.append(f"*{lie['player']['name']}*:\t`{lie['text']}`")
                    initial_comment = '\n'.join(lies)
                self.slack_client.files_upload(file=filename, title=title, channels=self.slack_channel,
                                               initial_comment=initial_comment, thread_ts=intro_message['ts'])
                if os.path.exists(filename):
                    os.remove(filename)
