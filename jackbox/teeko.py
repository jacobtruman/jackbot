import os
import svgwrite
from cairosvg import svg2png
from jackbox import Jackbox


class Teeko(Jackbox):

    def __init__(self, game_id: str = None, dev: bool = False):
        super().__init__(game_id=game_id, dev=dev)

        self.data_url = 'https://fishery.jackboxgames.com/artifact/TeeKOGame'
        self.gallery_url = 'http://games.jackbox.tv/artifact/TeeKOGame'

    def create_image(self, _drawing, _name):
        print(f"INFO: Processing image {_name}")
        dwg = svgwrite.Drawing(profile='tiny', viewBox='0 0 300 300')
        dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), rx=None, ry=None, fill=_drawing['background']))
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
            self.send_intro_message()

            for shirt in data['shirts']:
                title = shirt['slogan']['slogan']
                drawing = shirt['drawing']
                if drawing['artist'] is not None:
                    artist = drawing['artist']['name']
                else:
                    artist = "None"
                filename = self.create_image(drawing, title)

                comments = [
                    f"*Artist*: _{artist}_",
                    f"*Author*: _{shirt['slogan']['author']['name']}_",
                    f"*Designer*: _{shirt['designer']['name']}_",
                    f"*Wins*: _{shirt['wins']}_",
                    f"\n`{title}`"
                ]
                initial_comment = "\n".join(comments)
                self.slack_client.files_upload(file=filename, title="Stare at the art...", channels=self.slack_channel,
                                               initial_comment=initial_comment)
                if os.path.exists(filename):
                    os.remove(filename)
