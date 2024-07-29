from utility.helpers import *
from classes.character import Character
from classes.effort import Effort


class CharactersPlacement:
    def __init__(self, characters_set,
                 punctuation_placement, effort_parameters=None):
        self.fitness = -1
        self.punctuation_placement = sorted([x - 1 for x in [y for y in punctuation_placement if
                                                             characters_set[y - 1]['button_id'] is None]])

        self.characters_set = list()
        for character in characters_set:
            self.characters_set.append(Character(
                character=character['character'],
                button_id=character['button_id'],
            ))
        self._order_fixed_characters()
        self.effort_parameters = effort_parameters
        if effort_parameters:
            self.effort = Effort(**effort_parameters)
        else:
            self.effort = None
        self.character_indices = None
        self.non_fixed_punctuation = get_non_fixed_punctuation(self.characters_set)
        if len(punctuation_placement) > 18:
            for i in range(len(punctuation_placement) - 18):
                self.non_fixed_punctuation.append(
                    Character(character="dummy_character_" + str(i + 1), button_id=None))

        self.letters_placement = []
        for index, character in enumerate(self.characters_set):
            if character.button_id is None and index not in self.punctuation_placement:
                self.letters_placement.append(index)

    def randomize(self):
        np.random.shuffle(self.characters_set)
        self._order_fixed_characters()
        self.arrange_punctuation()

    def calculate_fitness(self, keyboard_structure, searching_corpus_dict, searching_corpus_digraph_dict):
        self.fitness = self.effort.calculate_effort(keyboard_structure, searching_corpus_dict, self.characters_set,
                                                    searching_corpus_digraph_dict)

        return self.fitness

    def mutate(self, maximum_number_of_mutation_operations):
        number_of_mutation_operations = np.random.randint(0, maximum_number_of_mutation_operations)
        for _ in range(number_of_mutation_operations):
            ind = self._non_fixed_random_character()
            i, j = ind[0], ind[1]
            self.characters_set[i], self.characters_set[j] = self.characters_set[j], self.characters_set[i]
            pass

    def _order_fixed_characters(self):
        fixed_characters = list()

        for i in range(len(self.characters_set)):
            if self.characters_set[i].button_id != None:
                fixed_characters.append(self.characters_set[i])
        self.characters_set = [character for character in self.characters_set if character.button_id == None]

        fixed_characters = sorted(fixed_characters, key=lambda character: character.button_id)

        for character in fixed_characters:
            self.characters_set.insert(character.button_id - 1, character)

    def _non_fixed_random_character(self):
        total_symbols = len(self.punctuation_placement) + len(self.letters_placement)
        if np.random.random() < len(self.punctuation_placement) / total_symbols:
            return random.sample(self.punctuation_placement, 2)
        else:
            return random.sample(self.letters_placement, 2)

    def __getitem__(self, idx):
        return self.characters_set[idx].character

    def arrange_punctuation(self):
        k = 0
        i = 0
        considered = set()
        while i < len(self.characters_set):
            if self.characters_set[i] in self.non_fixed_punctuation and i not in considered:
                self.characters_set[i], self.characters_set[self.punctuation_placement[k]] = self.characters_set[
                    self.punctuation_placement[k]], self.characters_set[i]
                considered.add(self.punctuation_placement[k])
                k += 1
                i -= 1
            i += 1

    def to_dict(self):
        return {
            'characters_set': [character.character for character in self.characters_set]
        }

    def to_json(self):
        return json.dumps(self.to_dict())
