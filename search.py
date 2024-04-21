import os
import json
import argparse

from helpers import *
from classes.keyboard_structure import KeyboardStructure
from classes.characters_placement import CharactersPlacement
from classes.genetic import Genetic

# 0.81

# 5 იტერაცია
# 3.0 წუთი
# 4.323318988
# 0.8 minutes
# 4.359704532

# 25 iterations
# 16.93 minutes
# 3.823404446
# 4.39 minutes
# 3.915055867
# 50 iterations for NN
# 8.45 minutes
# 3.84558431
# 5 iterations with parenthesis
# 0.97 minutes
# 4.303527782
# 100 იტერაცია
# 17.45 minutes
# 3.87752
# 100 iterations
# 15.66 minutes
# 3.847292158
# 200 iterations
# 36.94 minutes
# 3.853543227
# 100
# 59.27 minutes
# 3.82534

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--genetic-config', required=True)
    args = parser.parse_args()

    info_log('Load genetic config file: %s' % args.genetic_config)
    with open(args.genetic_config, 'r', encoding='utf-8') as file:
        genetic_config = json.load(file)

    model_name = generate_name_from_config(genetic_config, date=False, generations=False)
    model_name = "saved_models/" + model_name + " # 10000 - 2000.keras"
    if os.path.exists(model_name):
        # Model file exists, load the model
        info_log("Loading the neural network model")
        import keras

        model = keras.models.load_model(model_name)
    else:
        error_log("Couldn't find the neural network model specified, optimizing slowly without neural network",
                  is_exit=False)
        model = None

    # naming each picture according to the effort parameters and date.
    picture_name = generate_name_from_config(genetic_config)

    info_log('Construct keyboard structure')
    keyboard_structure = KeyboardStructure(
        name=picture_name,
        width=genetic_config['keyboard_structure']['width'],
        height=genetic_config['keyboard_structure']['height'],
        buttons=genetic_config['keyboard_structure']['buttons'],
        hands=genetic_config['hands'],
    )

    info_log('Construct initial characters placement')
    initial_characters_placement = CharactersPlacement(characters_set=genetic_config['characters_set'],
                                                       effort_parameters=genetic_config['effort_parameters'])

    with open("saved_models/character_to_predefined_key.json", 'r', encoding='utf-8') as json_file_read:
        character_to_predefined_key = json.load(json_file_read)

    info_log('Start genetic algorithm')
    info_log(f"number of generations: {genetic_config['number_of_generations']}")
    genetic = Genetic(
        number_of_generations=genetic_config['number_of_generations'],
        number_of_characters_placements=genetic_config['number_of_characters_placements'],
        number_of_accepted_characters_placements=genetic_config['number_of_accepted_characters_placements'],
        number_of_parent_placements=genetic_config['number_of_parent_placements'],
        number_of_randomly_injected_characters_placements=
        genetic_config['number_of_randomly_injected_characters_placements'],
        maximum_number_of_mutation_operations=genetic_config['maximum_number_of_mutation_operations'],
        corpus_path=genetic_config['corpus_path'],
        searching_corpus_size=genetic_config['searching_corpus_size'],
        testing_corpus_size=genetic_config['testing_corpus_size'],
        maximum_line_length=genetic_config['maximum_line_length'],
        random_seed=genetic_config['random_seed'],
        number_of_cores=genetic_config['number_of_cores'],
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
    genetic.save_searching_and_testing_corpus(os.path.dirname(args.genetic_config))

    genetic.best_characters_placement.calculate_fitness(
        genetic.keyboard_structure,
        genetic.testing_corpus_dict,
        genetic.testing_corpus_digraph_dict,
    )
    info_log('Best characters placement fitness value on testing set: %s' % genetic.best_characters_placement.fitness)
    table_text.append(f"fitness value: {genetic.best_characters_placement.fitness}")

    info_log('Visualize best characters placement found by genetic algorithm')
    if not os.path.exists(os.path.join(os.path.dirname(args.genetic_config), "layout_images")):
        os.makedirs(os.path.join(os.path.dirname(args.genetic_config), "layout_images"))

    each_effort = genetic.best_characters_placement.effort.calculate_effort_detailed(keyboard_structure,
                                                                                     genetic.searching_corpus_dict,
                                                                                     genetic.best_characters_placement.characters_set,
                                                                                     genetic.searching_corpus_digraph_dict)

    for index, (key, value) in enumerate(each_effort.items()):
        table_text[index] = table_text[index] + f"{value:.3f}"

    genetic.keyboard_structure.visualize(
        dirpath=os.path.join(os.path.dirname(args.genetic_config), "layout_images"),
        characters_placement=genetic.best_characters_placement,
        save=True,
        table_text=table_text
    )
