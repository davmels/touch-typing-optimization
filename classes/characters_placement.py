import time
import numpy as np

from helpers import *
from classes.character import Character
from classes.effort import Effort


# if some key is left without a character, then We'll go over shift characters with highest monograph frequency and choose them.
class CharactersPlacement:
    def __init__(self, characters_set, effort_parameters=None):
        self.fitness = -1
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
        self.prohibited_indices = [11, 23, 34, 44]
        for i in range(4):
            self.prohibited_indices.append(self.prohibited_indices[i] + 47)

    def randomize(self):
        # while True:
        np.random.shuffle(self.characters_set)
        self._order_fixed_characters()
            # if self.validate_end_key_parenthesis():
            #     break
        # self.character_indices = self.effort.find_character_indices(characters_set=self.characters_set)
        # self.put_parenthesis_together()

    def calculate_fitness(self, keyboard_structure, searching_corpus_dict, searching_corpus_digraph_dict):
        self.fitness = self.effort.calculate_effort(keyboard_structure, searching_corpus_dict, self.characters_set,
                                                    searching_corpus_digraph_dict)

        return self.fitness

    def mutate(self, maximum_number_of_mutation_operations):
        number_of_mutation_operations = np.random.randint(0, maximum_number_of_mutation_operations)
        for _ in range(number_of_mutation_operations):
            i = self._non_fixed_random_character()
            j = self._non_fixed_random_character()
            self.characters_set[i], self.characters_set[j] = self.characters_set[j], self.characters_set[i]

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
        rand = np.random.randint(0, len(self.characters_set) - 1)
        while self.characters_set[rand].button_id != None:
            rand = np.random.randint(0, len(self.characters_set) - 1)
        return rand

    def validate_parenthesis(self):
        self.character_indices = self.effort.find_character_indices(self.characters_set)
        if self.character_indices['['] in self.prohibited_indices or self.character_indices[
            '('] in self.prohibited_indices or \
                self.character_indices['{'] in self.prohibited_indices or self.character_indices[
            '<'] in self.prohibited_indices:
            return False
        if self.character_indices['['] + 1 != self.character_indices[']'] or self.character_indices['('] + 1 != \
                self.character_indices[
                    ')'] or self.character_indices['{'] + 1 != self.character_indices['}'] or self.character_indices[
            '<'] + 1 != \
                self.character_indices['>']:
            return False
        return True

    def validate_end_key_parenthesis(self):
        self.character_indices = self.effort.find_character_indices(self.characters_set)
        parenthesis = "{}[]()<>"
        for p in parenthesis:
            if self.character_indices[p] in self.prohibited_indices:
                return False
        return True

    def put_parenthesis_together(self):
        if self.character_indices is not None:
            parenthesis = [
                ('(', ')'),
                ('[', ']'),
                ('{', '}'),
                ('<', '>'),
            ]
            while True:
                fixed = True
                for p in parenthesis:
                    if self.character_indices[p[0]] + 1 != self.character_indices[p[1]]:
                        i = self.character_indices[p[0]] + 1
                        j = self.character_indices[p[1]]
                        self.characters_set[i], self.characters_set[j] = self.characters_set[j], self.characters_set[i]
                        self.character_indices[p[1]] = i
                        self.character_indices[self.characters_set[j].character] = j
                        fixed = False
                if fixed:
                    break

    def __getitem__(self, idx):
        return self.characters_set[idx].character
