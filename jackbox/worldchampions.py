import os
import svgwrite
from cairosvg import svg2png
from jackbox import Jackbox


class Worldchampions(Jackbox):

    def __init__(self, game_id: str = None, api_account: str = 'dev', dry_run: bool = False):
        super().__init__(game_id=game_id, api_account=api_account, dry_run=dry_run)

        self.data_url = self.gallery_url = self.base_image_url = self.base_gen_image_url = 'WorldChampionsGame'
        self.game_name = "Champ'd UP"

    @staticmethod
    def _split_point(point):
        _point = point.split(",")
        return _point[0], _point[1]

    def create_image(self, _drawing):
        image_name = f"{_drawing['player']['name']}-{_drawing['name']}"
        print(f"INFO: Processing image {image_name}")
        dwg = svgwrite.Drawing(profile='tiny', viewBox=f"0 0 {_drawing['size']['width']} {_drawing['size']['height']}")
        dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), rx=None, ry=None, fill="#FFFFFF"))
        for line in _drawing['lines']:
            points = line['points'].split("|")
            if len(points) > 1:
                shape = dwg.polyline(
                    [self._split_point(point) for point in points],
                    stroke=line['color'],
                    fill='none',
                    stroke_width=line['thickness'] * 5
                )
            else:
                point = self._split_point(points[0])
                shape = dwg.circle(
                    center=(point[0], point[1]),
                    r=2,
                    stroke=line['color'],
                    fill=line['color'],
                    stroke_width=line['thickness']
                )
            dwg.add(shape)
        filename = f"./{self.clean_string(image_name)}.png"
        svg2png(bytestring=dwg.tostring(), write_to=filename)
        return filename

    def _queue_drawing_message(self, drawing, metadata):
        """Queue messages for a drawing (file upload + chat message)."""
        filename = self.create_image(drawing)

        name = drawing['name']
        title = metadata['title']
        text = f"Stare at the art... {name}"

        self.queue_file_upload(
            file=filename,
            title=text
        )

        text_items = {
            "Name": name,
            "Actual Title": title,
            "Artist": drawing['player']['name'],
            "Score": drawing['player']['score'],
            "Result": "`WINNER`" if drawing['voteData']['isWinner'] else "`LOSER`"
        }
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self.clean_string(
                        "\n".join([f"*{key}*: {val}" for key, val in text_items.items()]),
                        underscore=False
                    )
                }
            }
        ]

        self.queue_chat_message(
            text=text,
            blocks=str(blocks)
        )

    def process_game(self):
        data = super().process_game()

        if data:
            try:
                # Queue intro message first
                self.queue_intro_message()

                for index, matchup in enumerate(data['blob']['matchups']):
                    metadata = {"full_title": matchup['fullTitle'], "title": matchup['title']}
                    self._queue_drawing_message(matchup['challenger'], metadata)
                    self._queue_drawing_message(matchup['champion'], metadata)

                # All messages prepared successfully, send them
                self.send_queued_messages()

            except Exception as ex:
                print(f"ERROR: Failed to process game: {ex}")
                self.clear_queue(cleanup_files=True)
                raise
