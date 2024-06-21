import copy
import json
from classes.characters_placement import CharactersPlacement
from classes.keyboard_structure import KeyboardStructure
from utility.helpers import *

with open('data_dir/config.json', 'r', encoding='utf-8') as jfr:
    config_initial = json.load(jfr)


class Analyser:
    def __init__(self):
        pass

    def analyse(self, optimization_config, res_func):
        config = copy.deepcopy(config_initial)

        config['effort_parameters'] = optimization_config['effort_parameters']
        config['punctuation_placement'] = optimization_config['punctuation_placement']
        config['number_of_generations'] = optimization_config['number_of_generations']
        config['characters_set'] = optimization_config['characters_set']

        self.validate_config(config)

        info_log('Construct keyboard structure')
        keyboard_structure = KeyboardStructure(
            name=config['keyboard_structure']['name'],
            width=config['keyboard_structure']['width'],
            height=config['keyboard_structure']['height'],
            buttons=config['keyboard_structure']['buttons'],
            hands=config['hands']
        )

        info_log('Construct initial characters placement')
        characters_placement = CharactersPlacement(characters_set=config['characters_set'],
                                                   punctuation_placement=config['punctuation_placement'],
                                                   effort_parameters=config['effort_parameters'])

        searching_corpus_dict, searching_corpus_digraph_dict, testing_corpus_dict, testing_corpus_digraph_dict = process_corpus()

        characters_placement.calculate_fitness(keyboard_structure, testing_corpus_dict, testing_corpus_digraph_dict)
        info_log('Fitness value: %s' % characters_placement.fitness)

        res_func(characters_placement.fitness)

    def validate_config(self, config):
        if not config['punctuation_placement']:
            config['punctuation_placement'] = [58, 59, 34, 35, 81, 82, 43, 44, 45, 90, 91, 92]
