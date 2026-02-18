import os
import svgwrite
from cairosvg import svg2png
from jackbox import Jackbox


class Teeko(Jackbox):

    def __init__(self, game_id: str = None, api_account: str = 'dev', dry_run: bool = False):
        super().__init__(game_id=game_id, api_account=api_account, dry_run=dry_run)

        self.gallery_url = 'TeeKO2Game'
        self.data_url = 'TeeKO2Game'
        # https://jbg-blobcast-artifacts.s3.amazonaws.com/TeeKO2Game/404a73b6ab4b39be8f73d971d24f52a0/data.json.gz

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
        filename = f"./{self.clean_string(_name)}.png"
        svg2png(bytestring=dwg.tostring(), write_to=filename)
        return filename

    def process_game(self):
        data = super().process_game()
        if data:
            try:
                # Queue intro message first
                self.queue_intro_message()

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
                    self.queue_file_upload(
                        file=filename,
                        title="Stare at the art...",
                        initial_comment=initial_comment
                    )

                # All messages prepared successfully, send them
                self.send_queued_messages()

            except Exception as ex:
                print(f"ERROR: Failed to process game: {ex}")
                self.clear_queue(cleanup_files=True)
                raise
