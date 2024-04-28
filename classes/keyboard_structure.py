import os
import copy

import cv2
import cv2 as cv
import numpy as np

from helpers import *
from classes.button import Button
from classes.hand import Hand


class KeyboardStructure:
    def __init__(self, name, width, height, buttons, hands):
        self.name = name
        self.width = width
        self.height = height

        self.buttons = list()
        for button in buttons:
            self.buttons.append(Button(
                id=button['id'],
                location=button['location'],
                size=button['size']
            ))

        self.buttons = sorted(self.buttons, key=lambda button: button.id)

        self._check_buttons_overlapping()

        self.hands = list()
        for hand in hands:
            self.hands.append(Hand(fingers=hand['fingers']))

    def smallest_distance_from_button_to_finger(self, button_id):
        minimum_distance_value = float('inf')

        for i, hand in enumerate(self.hands):
            for j, finger in enumerate(hand.fingers):
                temp_minimum_distance = finger.location.euclidean_distance(self.buttons[button_id].center)
                minimum_distance_value = min(minimum_distance_value, temp_minimum_distance)

        return minimum_distance_value

    def visualize(
            self,
            dirpath,
            characters_placement=None,
            show_hands=True,
            save=False,
            table_text=None
    ):
        if characters_placement is None:
            characters_placement = [''] * len(self.buttons)

        img = np.ones((cm2px(self.height) + cm2px(4.5), cm2px(self.width), 3), np.uint8)
        for i in range(cm2px(self.height)):
            for j in range(cm2px(self.width)):
                img[i][j] = [141, 140, 127]
        for i in range(cm2px(4.5)):
            for j in range(cm2px(self.width)):
                img[i + cm2px(self.height)][j] = [141, 140, 127]

        for button in self.buttons:
            cv.rectangle(
                img=img,
                pt1=cm2px((button.top_left.x, button.top_left.y)),
                pt2=cm2px((button.bottom_right.x, button.bottom_right.y)),
                color=(80, 62, 44),
                thickness=-1
            )
            # cv.circle(
            #     img=img,
            #     center=cm2px((button.center.x, button.center.y)),
            #     radius=cm2px(0.15),
            #     color=random_color(),
            #     thickness=-1
            # )

        if show_hands:
            for hand in self.hands:
                hand_color = random_color()
                for finger in hand.fingers:
                    cv.circle(
                        img=img,
                        center=cm2px((finger.location.x, finger.location.y)),
                        radius=cm2px(0.35),
                        color=hand_color,
                        thickness=-1
                    )

        from PIL import ImageFont, ImageDraw, Image

        georgian_string = "აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ"

        for i in range(len(characters_placement.characters_set)):
            button = self.buttons[i] if i < 47 else self.buttons[i - 47]
            character = characters_placement.characters_set[i].character
            if "dummy_character" in character:
                continue
            if i < 47:
                font_scale = 33
            else:
                font_scale = 21

            if character == '-':
                font_scale = 18
            elif character == '_':
                font_scale = 33

            font = ImageFont.truetype('data_dir/bpg_glaho_sylfaen.ttf', font_scale)
            if character in georgian_string:
                img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
                pil_image = Image.fromarray(img)
                draw = ImageDraw.Draw(pil_image)
                draw.text(cm2px(
                    (button.location.x + 0.08 if i < 47 else button.location.x + 2 * button.size.width / 3,
                     button.location.y + button.size.height / 3.2 if i < 47 else button.location.y)
                ), character,
                    font=font)
                img = np.asarray(pil_image)
                img = cv.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                cv.putText(
                    img=img,
                    text=character,
                    org=cm2px((button.text_origin.x if i < 47 else button.location.x + 4 * button.size.width / 6.7,
                               button.text_origin.y if i < 47 else button.location.y + button.size.height / 2)),
                    fontFace=cv.FONT_HERSHEY_SIMPLEX,
                    fontScale=font_scale / 30,
                    color=(241, 240, 236),
                    thickness=2
                )

        if table_text:
            table_font_scale = 0.5  # Adjust font scale for table
            table_font = cv.FONT_HERSHEY_SIMPLEX
            table_color = (0, 0, 0)  # Black color for table text
            table_thickness = 2
            table_spacing = cm2px(0.5)  # Vertical spacing between rows
            table_row_count = 5  # Number of rows
            table_col_count = 2  # Number of columns

            # Write table text
            for row_idx in range(table_row_count):
                y = int(cm2px(0.4) + row_idx * (table_font_scale * 30 + table_spacing))  # Convert to integer
                for col_idx in range(table_col_count):
                    x = int(cm2px(0.5) + col_idx * cm2px(self.width/2))  # Convert to integer
                    text_idx = row_idx * table_col_count + col_idx
                    if text_idx < len(table_text):
                        text = table_text[text_idx]
                    else:
                        text = ""
                    cv.putText(
                        img=img,
                        text=text,
                        org=(x, y + cm2px(self.height)),
                        fontFace=table_font,
                        fontScale=table_font_scale,
                        color=table_color,
                        thickness=table_thickness
                    )

        cv.imshow(self.name, img)
        cv.waitKey(0)

        if save:
            print(self.name)
            cv.imwrite(os.path.join(dirpath, self.name + '.png'), img)

    def _check_buttons_overlapping(self):
        for i in range(len(self.buttons)):
            for j in range(i + 1, len(self.buttons)):
                if self.buttons[i].is_overlapping(self.buttons[j]):
                    warning_log('buttons %s and %s are overlapped' % (i + 1, j + 1))

    def __str__(self):
        text = '%s Configurations\n' % self.name
        text += '- Width: %scm\n' % self.width
        text += '- Height: %scm\n' % self.height
        text += '- Number of Buttons: %s\n' % len(self.buttons)
        text += '- Number of Hands: %s' % len(self.hands)
        return text
