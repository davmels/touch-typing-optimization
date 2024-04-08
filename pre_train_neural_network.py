import os
import numpy as np
import keras
import tensorflow as tf
import json
import argparse
import copy

from helpers import *
from classes.keyboard_structure import KeyboardStructure
from classes.characters_placement import CharactersPlacement
from classes.effort import Effort

if __name__ == '__main__':
    number_of_keyboards = 100
    number_of_characters = 94
    characters_placements = []

    parser = argparse.ArgumentParser()
    parser.add_argument('--genetic-config', required=True)
    args = parser.parse_args()

    info_log('Load genetic config file: %s' % args.genetic_config)
    with open(args.genetic_config, 'r', encoding='utf-8') as file:
        genetic_config = json.load(file)

    info_log('Construct initial characters placement')
    initial_characters_placement = CharactersPlacement(characters_set=genetic_config['characters_set'],
                                                       effort_parameters=genetic_config['effort_parameters'])

    info_log('Construct keyboard structure')
    keyboard_structure = KeyboardStructure(
        name='nothing',
        width=genetic_config['keyboard_structure']['width'],
        height=genetic_config['keyboard_structure']['height'],
        buttons=genetic_config['keyboard_structure']['buttons'],
        hands=genetic_config['hands'],
    )

    effort = Effort(**genetic_config['effort_parameters'])

    # IMPORTANT HERE... I HAVE TO SAVE THESE SOMEWHERE, IN A SEPARATE CONFIG FILE!
    character_to_predefined_key = {}
    for index, character in enumerate(initial_characters_placement.characters_set):
        character_to_predefined_key[character.character] = index

    for _ in range(number_of_keyboards):
        random_characters_placement = copy.deepcopy(initial_characters_placement)
        random_characters_placement.randomize()
        characters_placements.append(random_characters_placement)

    data = np.zeros([number_of_keyboards, number_of_characters, number_of_characters], dtype=int)
    labels = np.zeros([number_of_keyboards], dtype=float)

    for keyboard in range(number_of_keyboards):
        for index, character in enumerate(characters_placements[keyboard].characters_set):
            data[keyboard][index][character_to_predefined_key[character.character]] = 1
        labels[keyboard] = effort.calculate_effort(keyboard_structure, )

    model = keras.Sequential([
        keras.layers.Flatten(input_shape=(number_of_characters, number_of_characters)),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dense(1)
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='mean_absolute_error'
    )
