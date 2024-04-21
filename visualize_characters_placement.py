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

    characters_placement = CharactersPlacement(characters_set=genetic_config['characters_set'],
                                               effort_parameters=genetic_config['effort_parameters'])

    from classes.effort import Effort

    info_log('Visualize the characters placement')
    if not os.path.exists(os.path.join(os.path.dirname(args.genetic_config), "layout_images")):
        os.makedirs(os.path.join(os.path.dirname(args.genetic_config), "layout_images"))
    # characters_placement.randomize()
    effort = Effort({'weight': 1, "finger_weights": {}}, 1, 1, 1, 1, 1, 1)
    for index, character in enumerate(characters_placement.characters_set):
        print(index, character.character, effort.find_index(index),
              keyboard_structure.smallest_distance_from_button_to_finger(index if index < 47 else index - 47))

    searching_corpus, testing_corpus, searching_corpus_dict, searching_corpus_digraph_dict, testing_corpus_dict, testing_corpus_digraph_dict = process_corpus(
        corpus_path=genetic_config['corpus_path'], characters_placement=characters_placement,
        random_seed=genetic_config['random_seed'],
        maximum_line_length=genetic_config['maximum_line_length'],
        searching_corpus_size=genetic_config['searching_corpus_size'],
        testing_corpus_size=genetic_config['testing_corpus_size'])

    table_text = []
    cool = True
    if cool:
        each_effort = characters_placement.effort.calculate_effort_detailed(keyboard_structure, searching_corpus_dict,
                                                                            characters_placement.characters_set,
                                                                            searching_corpus_digraph_dict)
        for index, (key, value) in enumerate(each_effort.items()):
            table_text.append(f"{key} : {value:.3f}")

    keyboard_structure.visualize(
        dirpath=os.path.join(os.path.dirname(args.genetic_config), "layout_images"),
        characters_placement=characters_placement,
        save=True,
        table_text=table_text
    )
