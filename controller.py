import copy
import threading
from flask import request
from classes.genetic import Genetic
from helpers import *
import os
import keras
from classes.characters_placement import CharactersPlacement
from classes.keyboard_structure import KeyboardStructure
from train_network import TrainNeuralNetwork

with open('utility/config.json', 'r', encoding='utf-8') as jfr:
    config_initial = json.load(jfr)


class AppController:
    def __init__(self, app):
        self.app = app
        self.register_endpoints()

    def register_endpoints(self):
        @self.app.route("/")
        def home():
            return "Home"


class SocketController:
    def __init__(self, socketio):
        self.socketio = socketio
        self.Optimizer = Optimizer()

        self.register_event_handlers()

    def register_event_handlers(self):
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected, socket id: ', request.sid)

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected, socket it: ', request.sid)

        @self.socketio.on('custom_event')
        def handle_custom_event(data):
            print('Received custom event:', data)
            data['data'] = "oh nou"
            self.socketio.emit('custom_event', {'data': data}, to=request.sid)

        @self.socketio.on('generate_keyboard_layout')
        def generate_keyboard_layout(optimization_config):
            sid = request.sid

            def socket_progress_emit(current_generation, total_generations):
                self.socketio.emit('progress', {
                    'current_generation': current_generation, 'total_generations': total_generations},
                                   to=sid)

            def initialization_finish_emit():
                self.socketio.emit('initialization_finish', to=sid)

            def result_emit(genetic):
                self.socketio.emit('result', {
                    'characters_set': [character.to_dict() for character in
                                       genetic.best_characters_placement.characters_set]},
                                   to=sid)

            thread = threading.Thread(target=self.Optimizer.search,
                                      args=(optimization_config, socket_progress_emit, initialization_finish_emit,
                                            result_emit))

            self.socketio.emit('initialization_start', to=sid)
            thread.start()


class Optimizer:
    def __init__(self):
        self.train_neural_network = TrainNeuralNetwork()

    def search(self, optimization_config, socket_progress_emit, initialization_finish_emit, result_emit):

        config = copy.deepcopy(config_initial)
        config['effort_parameters'] = optimization_config['effort_parameters']
        config['punctuation_placement'] = optimization_config['punctuation_placement']
        config['number_of_generations'] = optimization_config['number_of_generations']

        model_name = generate_name_from_config(config, date=False, generations=False, hands=True)
        model_name = "saved_models/" + model_name + " # 10000 - 2000.keras"

        if os.path.exists(model_name):
            # Model file exists, load the model
            info_log("Loading the neural network model")
            model = keras.models.load_model(model_name)
        else:
            info_log("Couldn't find the neural network model specified, training a neural network from scratch")
            model = self.train_neural_network.train(config)

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
            character_to_predefined_key=character_to_predefined_key,
            socket_emit_progress=socket_progress_emit
        )

        initialization_finish_emit()
        genetic.start()

        result_emit(genetic)
