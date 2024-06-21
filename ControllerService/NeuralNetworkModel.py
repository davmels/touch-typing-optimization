import os

import keras

from ControllerService.train_network import TrainNeuralNetwork
from utility.helpers import *


class NeuralNetworkModel:
    def __init__(self, config, date, generations, hands):
        self.train_neural_network = TrainNeuralNetwork()
        model_name = generate_name_from_config(config, date=False, generations=False, hands=True)
        model_name = "saved_models/" + model_name + " # 10000 - 2000 - "

        with open("data_dir/punctuation_placements.json", 'r') as json_file:
            punctuation_placements = json.load(json_file)

        punctuation_placement = sorted(config['punctuation_placement'])
        for key, value in punctuation_placements.items():
            sorted_value = sorted(value)
            if punctuation_placement == sorted_value:
                model_name = model_name + key + ".keras"
                break

        if os.path.exists(model_name):
            info_log("Loading the neural network model")
            self.model = keras.models.load_model(model_name)
        else:
            info_log("Couldn't find the neural network model specified, training a neural network from scratch")
            self.model = self.train_neural_network.train(config)

    def get(self):
        return self.model
