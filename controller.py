import json
from classes.genetic import Genetic
from helpers import *
import os
import keras
from classes.characters_placement import CharactersPlacement
from classes.keyboard_structure import KeyboardStructure


class Controller:
    def __init__(self):
        pass

    def search(self, config, socket, sid):

        model_name = generate_name_from_config(config, date=False, generations=False)
        model_name = "saved_models/" + model_name + " # 10000 - 2000.keras"

        if os.path.exists(model_name):
            # Model file exists, load the model
            info_log("Loading the neural network model")
            model = keras.models.load_model(model_name)
        else:
            info_log("Couldn't find the neural network model specified, optimizing with default neural network")
            model = None

        # naming each picture according to the effort parameters and date.
        picture_name = generate_name_from_config(config)

        info_log('Construct keyboard structure')
        keyboard_structure = KeyboardStructure(
            name=picture_name,
            width=config['keyboard_structure']['width'],
            height=config['keyboard_structure']['height'],
            buttons=config['keyboard_structure']['buttons'],
            hands=config['hands'],
        )

        info_log('Construct initial characters placement')
        initial_characters_placement = CharactersPlacement(characters_set=config['characters_set'],
                                                           effort_parameters=config['effort_parameters'],
                                                           punctuation_placement=sorted(
                                                               config['punctuation_placement']))

        with open("saved_models/character_to_predefined_key.json", 'r', encoding='utf-8') as json_file_read:
            character_to_predefined_key = json.load(json_file_read)

        info_log('Start genetic algorithm')
        info_log(f"number of generations: {config['number_of_generations']}")
        genetic = Genetic(
            number_of_generations=config['number_of_generations'],
            number_of_characters_placements=config['number_of_characters_placements'],
            number_of_accepted_characters_placements=config['number_of_accepted_characters_placements'],
            number_of_parent_placements=config['number_of_parent_placements'],
            number_of_randomly_injected_characters_placements=
            config['number_of_randomly_injected_characters_placements'],
            maximum_number_of_mutation_operations=config['maximum_number_of_mutation_operations'],
            corpus_path=config['corpus_path'],
            searching_corpus_size=config['searching_corpus_size'],
            testing_corpus_size=config['testing_corpus_size'],
            maximum_line_length=config['maximum_line_length'],
            random_seed=config['random_seed'],
            number_of_cores=config['number_of_cores'],
            keyboard_structure=keyboard_structure,
            initial_characters_placement=initial_characters_placement,
            model=model,
            character_to_predefined_key=character_to_predefined_key
        )

        table_text = []
        each_effort = genetic.initial_characters_placement.effort.calculate_effort_detailed(keyboard_structure,
                                                                                            genetic.searching_corpus_dict,
                                                                                            genetic.initial_characters_placement.characters_set,
                                                                                            genetic.searching_corpus_digraph_dict)

        for index, (key, value) in enumerate(each_effort.items()):
            table_text.append(f"{key} : {value:.3f} / ")

        table_text.append(f"Time taken: {genetic.start()} minutes")

        socket.emit('result', {
            'characters_set': [character.character for character in genetic.best_characters_placement.characters_set]},
                    to=sid)
        # return genetic.best_characters_placement
