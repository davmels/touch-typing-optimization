import os
import json
import argparse

from helpers import *
from classes.keyboard_structure import KeyboardStructure
from classes.characters_placement import CharactersPlacement

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--genetic-config', required=True)
    args = parser.parse_args()

    info_log('Load genetic config file: %s' % args.genetic_config)
    with open(args.genetic_config, 'r', encoding='utf-8') as file:
        genetic_config = json.load(file)

    info_log('Construct keyboard structure')
    keyboard_structure = KeyboardStructure(
        name=genetic_config['keyboard_structure']['name'],
        width=genetic_config['keyboard_structure']['width'],
        height=genetic_config['keyboard_structure']['height'],
        buttons=genetic_config['keyboard_structure']['buttons'],
        hands=genetic_config['hands']
    )

    info_log('Construct initial characters placement')

    characters_placement = CharactersPlacement(characters_set=genetic_config['characters_set'])

    from classes.effort import Effort
    effort = Effort({'weight':1, "finger_weights":{}}, 1, 1, 1, 1, 1, 1)
    for index, character in enumerate(characters_placement.characters_set):
        print(index, character.character, effort.find_index(index),
              keyboard_structure.smallest_distance_from_button_to_finger(index if index < 47 else index - 47))

    info_log('Visualize the characters placement')
    if not os.path.exists(os.path.join(os.path.dirname(args.genetic_config), "layout_images")):
        os.makedirs(os.path.join(os.path.dirname(args.genetic_config), "layout_images"))
    keyboard_structure.visualize(
        dirpath=os.path.join(os.path.dirname(args.genetic_config), "layout_images"),
        characters_placement=characters_placement,
        save=True
    )
