import keras
import copy
from tqdm import tqdm
from classes.keyboard_structure import KeyboardStructure
from classes.characters_placement import CharactersPlacement
from classes.effort import Effort
from utility.helpers import *


class TrainNeuralNetwork:
    def __init__(self, number_of_keyboards=2000, number_of_characters=94, characters_placements=None,
                 number_of_epochs=200):
        if characters_placements is None:
            self.characters_placements = []
        else:
            self.characters_placements = characters_placements
        self.number_of_keyboards = number_of_keyboards
        self.number_of_characters = number_of_characters
        self.number_of_epochs = number_of_epochs

    def train(self, genetic_config):
        info_log('Construct initial characters placement')
        initial_characters_placement = CharactersPlacement(characters_set=genetic_config['characters_set'],
                                                           effort_parameters=genetic_config['effort_parameters'],
                                                           punctuation_placement=genetic_config[
                                                               'punctuation_placement'])

        info_log('Construct keyboard structure')
        keyboard_structure = KeyboardStructure(
            name='nothing',
            width=genetic_config['keyboard_structure']['width'],
            height=genetic_config['keyboard_structure']['height'],
            buttons=genetic_config['keyboard_structure']['buttons'],
            hands=genetic_config['hands'],
        )

        effort = Effort(**genetic_config['effort_parameters'])

        with open("data_dir/character_to_predefined_key.json", 'r', encoding='utf-8') as json_file_read:
            character_to_predefined_key = json.load(json_file_read)

        for _ in range(self.number_of_keyboards):
            random_characters_placement = copy.deepcopy(initial_characters_placement)
            random_characters_placement.randomize()
            self.characters_placements.append(random_characters_placement)

        data = np.zeros([self.number_of_keyboards, self.number_of_characters, self.number_of_characters], dtype=int)
        labels = np.zeros([self.number_of_keyboards], dtype=float)

        searching_corpus_dict, searching_corpus_digraph_dict, testing_corpus_dict, testing_corpus_digraph_dict = process_corpus()

        info_log(f"preparing dataset for training consisting of {self.number_of_keyboards} keyboards")
        for keyboard in tqdm(range(self.number_of_keyboards)):
            #print(keyboard, [character.character for character in self.characters_placements[keyboard].characters_set])
            for index, character in enumerate(self.characters_placements[keyboard].characters_set):
                data[keyboard][index][character_to_predefined_key[character.character]] = 1
            labels[keyboard] = effort.calculate_effort(keyboard_structure, searching_corpus_dict,
                                                       self.characters_placements[keyboard].characters_set,
                                                       searching_corpus_digraph_dict)

        split_point = int(0.8 * self.number_of_keyboards)
        info_log(
            f"training neural network on {math.floor(split_point)} random keyboards for {self.number_of_epochs} epochs.")

        x_train = data
        y_train = labels

        input_shape = (self.number_of_characters, self.number_of_characters)
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

        model.fit(x_train, y_train, epochs=self.number_of_epochs, validation_split=0.2)

        return model
