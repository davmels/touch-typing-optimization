from ControllerService.NeuralNetworkModel import NeuralNetworkModel
from classes.characters_placement import CharactersPlacement
from classes.genetic import Genetic
from classes.keyboard_structure import KeyboardStructure
from utility.helpers import *
import copy

with open('data_dir/config.json', 'r', encoding='utf-8') as jfr:
    config_initial = json.load(jfr)


class Optimizer:
    def __init__(self):
        pass

    def search(self, optimization_config, socket_progress_emit, initialization_finish_emit, result_emit):
        config = copy.deepcopy(config_initial)

        config['effort_parameters'] = optimization_config['effort_parameters']
        config['punctuation_placement'] = optimization_config['punctuation_placement']
        config['number_of_generations'] = optimization_config['number_of_generations']
        config['characters_set'] = optimization_config['characters_set']

        self.validate_config(config)

        model = NeuralNetworkModel(config, date=False, generations=False, hands=True).get()

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

        with open("data_dir/character_to_predefined_key.json", 'r', encoding='utf-8') as json_file_read:
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
            character_to_predefined_key=character_to_predefined_key,
            socket_emit_progress=socket_progress_emit
        )

        initialization_finish_emit()
        genetic.start()

        result_emit(genetic)

    def validate_config(self, config):
        if not config['punctuation_placement']:
            config['punctuation_placement'] = [58, 59, 34, 35, 81, 82, 43, 44, 45, 90, 91, 92]
        