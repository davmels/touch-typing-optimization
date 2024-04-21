import os
import numpy as np
import keras
# import tensorflow as tf
import json
import argparse
import copy
from tqdm import tqdm

from helpers import *
from classes.keyboard_structure import KeyboardStructure
from classes.characters_placement import CharactersPlacement
from classes.effort import Effort
#info: Sun Apr 14 21:32:56 2024] Time taken for training neural network is 25.84 minutes
if __name__ == '__main__':
    number_of_keyboards = 10000
    number_of_characters = 94
    characters_placements = []
    number_of_epochs = 2000

    parser = argparse.ArgumentParser()
    parser.add_argument('--genetic-config', required=True)
    args = parser.parse_args()

    info_log('Load genetic config file: %s' % args.genetic_config)
    with open(args.genetic_config, 'r', encoding='utf-8') as file:
        genetic_config = json.load(file)

    info_log('Construct initial characters placement')
    initial_characters_placement = CharactersPlacement(characters_set=genetic_config['characters_set'],
                                                       effort_parameters=genetic_config['effort_parameters'])

    model_name = generate_name_from_config(genetic_config, date=False, generations=False)
    model_name += f" # {number_of_keyboards} - {number_of_epochs}"

    info_log('Construct keyboard structure')
    keyboard_structure = KeyboardStructure(
        name='nothing',
        width=genetic_config['keyboard_structure']['width'],
        height=genetic_config['keyboard_structure']['height'],
        buttons=genetic_config['keyboard_structure']['buttons'],
        hands=genetic_config['hands'],
    )

    effort = Effort(**genetic_config['effort_parameters'])

    with open("saved_models/character_to_predefined_key.json", 'r', encoding='utf-8') as json_file_read:
        character_to_predefined_key = json.load(json_file_read)

    for _ in range(number_of_keyboards):
        random_characters_placement = copy.deepcopy(initial_characters_placement)
        random_characters_placement.randomize()
        characters_placements.append(random_characters_placement)

    data = np.zeros([number_of_keyboards, number_of_characters, number_of_characters], dtype=int)
    labels = np.zeros([number_of_keyboards], dtype=float)

    searching_corpus, testing_corpus, searching_corpus_dict, searching_corpus_digraph_dict, testing_corpus_dict, testing_corpus_digraph_dict = process_corpus(
        corpus_path=genetic_config['corpus_path'], characters_placement=initial_characters_placement,
        random_seed=genetic_config['random_seed'],
        maximum_line_length=genetic_config['maximum_line_length'],
        searching_corpus_size=genetic_config['searching_corpus_size'],
        testing_corpus_size=genetic_config['testing_corpus_size'])

    info_log(f"preparing dataset for training consisting of {number_of_keyboards} keyboards")
    for keyboard in tqdm(range(number_of_keyboards)):
        for index, character in enumerate(characters_placements[keyboard].characters_set):
            data[keyboard][index][character_to_predefined_key[character.character]] = 1
        labels[keyboard] = effort.calculate_effort(keyboard_structure, searching_corpus_dict,
                                                   characters_placements[keyboard].characters_set,
                                                   searching_corpus_digraph_dict)

    split_point = int(0.8 * number_of_keyboards)
    info_log(
        f"training neural network on {math.floor(split_point)} random keyboards for {number_of_epochs} epochs.")

    x_train = data[:split_point]
    x_test = data[split_point:]
    y_train = labels[:split_point]
    y_test = labels[split_point:]

    start_time = time.time()
    input_shape = (number_of_characters, number_of_characters)
    model = keras.Sequential([
        keras.layers.Input(shape=input_shape),
        keras.layers.Flatten(),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dense(1)
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='mean_absolute_error'
    )

    #early_stopping = keras.callbacks.EarlyStopping(monitor='val_loss', patience=250, restore_best_weights=False)

    model.fit(x_train, y_train, epochs=2000, validation_split=0.2)#, callbacks=[early_stopping])

    model.save('saved_models/' + model_name + '.keras')

    model.evaluate(x_test, y_test)

    time = round((time.time() - start_time) / 60, 2)
    info_log('Time taken for training neural network is %s minutes' % (time))
