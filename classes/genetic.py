import re
import os
import copy
import time
import math
import numpy as np
from tqdm import tqdm

from multiprocessing import Process, Manager
from threading import Thread
from helpers import *


class Genetic:
    def __init__(
            self,
            number_of_generations,
            number_of_characters_placements,
            number_of_parent_placements,
            number_of_accepted_characters_placements,
            number_of_randomly_injected_characters_placements,
            maximum_number_of_mutation_operations,
            corpus_path,
            searching_corpus_size,
            testing_corpus_size,
            maximum_line_length,
            random_seed,
            number_of_cores,
            keyboard_structure,
            initial_characters_placement,
            model,
            character_to_predefined_key,
            socket_emit_progress=None
    ):
        self.number_of_generations = number_of_generations
        self.number_of_characters_placements = number_of_characters_placements
        self.number_of_parent_placements = number_of_parent_placements
        self.number_of_accepted_characters_placements = number_of_accepted_characters_placements
        self.number_of_randomly_injected_characters_placements = number_of_randomly_injected_characters_placements
        self.maximum_number_of_mutation_operations = maximum_number_of_mutation_operations
        self.number_of_cores = number_of_cores
        self.keyboard_structure = keyboard_structure
        self.initial_characters_placement = initial_characters_placement
        self.model = model
        self.character_to_predefined_key = character_to_predefined_key
        self.socket_emit_progress = socket_emit_progress

        # searching_corpus, testing_corpus, searching_corpus_dict, searching_corpus_digraph_dict, testing_corpus_dict, testing_corpus_digraph_dict = process_corpus(
        #     corpus_path=corpus_path, characters_placement=self.initial_characters_placement, random_seed=random_seed,
        #     maximum_line_length=maximum_line_length, searching_corpus_size=searching_corpus_size,
        #     testing_corpus_size=testing_corpus_size)
        searching_corpus_dict, searching_corpus_digraph_dict, testing_corpus_dict, testing_corpus_digraph_dict = process_corpus(
            corpus_path=corpus_path, characters_placement=self.initial_characters_placement, random_seed=random_seed,
            maximum_line_length=maximum_line_length, searching_corpus_size=searching_corpus_size,
            testing_corpus_size=testing_corpus_size)

        # self.searching_corpus = searching_corpus
        # self.testing_corpus = testing_corpus
        self.searching_corpus_dict = searching_corpus_dict
        self.searching_corpus_digraph_dict = searching_corpus_digraph_dict
        self.testing_corpus_dict = testing_corpus_dict
        self.testing_corpus_digraph_dict = testing_corpus_digraph_dict

        info_log(f"Generating {self.number_of_characters_placements} random keyboards")
        self.characters_placements = list()
        for _ in range(self.number_of_characters_placements):
            self.characters_placements.append(copy.deepcopy(self.initial_characters_placement))
            self.characters_placements[-1].randomize()

        self.time = -1
        self.best_characters_placement = None

    def start(self):
        start_time = time.time()

        for generation in range(self.number_of_generations):
            info_log('Start generation number %s' % (generation + 1))

            if self.model != None:
                info_log('Calculate fitness function for each characters placement')
                best_characters_placements = self.calculate_fitness_for_characters_placements_DNN()
                # if self.best_characters_placement is None or best_characters_placement.fitness < self.best_characters_placement.fitness:
                #     self.best_characters_placement = best_characters_placement
                # info_log('Best characters placement fitness value: %s' % self.best_characters_placement.fitness)
                info_log('Best characters placement fitness value: %s' % best_characters_placements[0][2])

                true_fitness = []
                for b in tqdm(best_characters_placements):
                    b[0].calculate_fitness(self.keyboard_structure, self.searching_corpus_dict,
                                           self.searching_corpus_digraph_dict)
                    true_fitness.append(b[0].fitness)

                self.model.fit(
                    np.array([best_characters_placements[i][1] for i in range(len(best_characters_placements))]),
                    np.array(true_fitness), epochs=10)

                trueJoint = [[best_characters_placements[i][0], true_fitness[i]] for i in
                             range(len(best_characters_placements))]
                sorted_trueJoint = sorted(trueJoint, key=lambda x: x[1])
                self.characters_placements = [sorted_trueJoint[i][0] for i in
                                              range(self.number_of_accepted_characters_placements)]

                best_fitness_value = sorted_trueJoint[0][1]
                best_characters_placement = sorted_trueJoint[0][0]
                if self.best_characters_placement is None or best_fitness_value < self.best_fitness_value:
                    self.best_characters_placement = best_characters_placement
                    self.best_fitness_value = best_fitness_value
                info_log('Best characters placement True fitness value: %s' % self.best_fitness_value)
            else:
                info_log('Calculate fitness function for each characters placement')
                best_characters_placement = self.calculate_fitness_for_characters_placements()
                if self.best_characters_placement is None or best_characters_placement.fitness < self.best_characters_placement.fitness:
                    self.best_characters_placement = best_characters_placement
                info_log('Best characters placement fitness value: %s' % self.best_characters_placement.fitness)

            info_log('Start natural selection and crossover')
            self.natural_selection_and_crossover()

            info_log('Start mutating characters placements')
            self.mutate_characters_placements()

            info_log('Start random injection')
            self.random_injection()

            if self.socket_emit_progress:
                self.socket_emit_progress(generation + 1, self.number_of_generations)

        self.time = round((time.time() - start_time) / 60, 2)
        info_log('Time taken for genetic algorithm is %s minutes' % (self.time))
        return self.time

    def calculate_bucket_fitness(self, characters_placements, keyboard_structure, searching_corpus_dict,
                                 searching_corpus_digraph_dict, index,
                                 fitness_dict):
        for i, characters_placement in enumerate(characters_placements):
            characters_placement.calculate_fitness(keyboard_structure, searching_corpus_dict,
                                                   searching_corpus_digraph_dict)
            fitness_dict[index + i] = characters_placement.fitness

    def calculate_fitness_for_characters_placements(self):

        manager = Manager()
        fitness_dict = manager.dict()

        bucket_size = math.ceil(len(self.characters_placements) / self.number_of_cores)
        processes = list()

        for i in range(self.number_of_cores):
            start = i * bucket_size
            end = start + bucket_size
            process = Process(
                target=self.calculate_bucket_fitness,
                args=(
                    self.characters_placements[start:end],
                    self.keyboard_structure,
                    self.searching_corpus_dict,
                    self.searching_corpus_digraph_dict,
                    start,
                    fitness_dict
                )
            )
            process.start()
            processes.append(process)

        for process in processes:
            process.join()

        best_fitness_value = float('inf')
        best_characters_placement = None
        for i, characters_placement in enumerate(self.characters_placements):
            characters_placement.fitness = fitness_dict[i]
            if characters_placement.fitness < best_fitness_value:
                best_fitness_value = characters_placement.fitness
                best_characters_placement = characters_placement

        return best_characters_placement

    def calculate_fitness_for_characters_placements_DNN(self):

        num_of_characters = len(self.initial_characters_placement.characters_set)

        keyboard_onehots = np.zeros([len(self.characters_placements), num_of_characters, num_of_characters], dtype=int)
        for cp in range(len(self.characters_placements)):
            for l in range(num_of_characters):
                character = self.characters_placements[cp].characters_set[l].character
                keyboard_onehots[cp][l][self.character_to_predefined_key[character]] = 1

        fitness_dict = self.model.predict(keyboard_onehots)

        joint = [[self.characters_placements[i], keyboard_onehots[i], fitness_dict[i][0]] for i in
                 range(len(self.characters_placements))]
        sorted_joint = sorted(joint, key=lambda x: x[2])

        # return best_characters_placements,
        return sorted_joint[:self.number_of_accepted_characters_placements]

    def natural_selection_and_crossover_old(self):
        self.characters_placements = sorted(self.characters_placements,
                                            key=lambda characters_placement: characters_placement.fitness)

        temp_characters_placements = list()
        for i in range(self.number_of_accepted_characters_placements):
            temp_characters_placements.append(copy.deepcopy(self.characters_placements[i]))

        while len(temp_characters_placements) < self.number_of_characters_placements - \
                self.number_of_randomly_injected_characters_placements:
            a, b = np.random.beta(a=0.5, b=2, size=2)

            a = math.floor(a * self.number_of_characters_placements)
            b = math.floor(b * self.number_of_characters_placements)

            assert (a != self.number_of_characters_placements)
            assert (b != self.number_of_characters_placements)

            temp_characters_placements.append(self._crossover(
                self.characters_placements[a],
                self.characters_placements[b]
            ))

            if len(temp_characters_placements) >= self.number_of_characters_placements - \
                    self.number_of_randomly_injected_characters_placements:
                break

            temp_characters_placements.append(self._crossover(
                self.characters_placements[b],
                self.characters_placements[a]
            ))

        self.characters_placements = temp_characters_placements

    def natural_selection_and_crossover(self):
        if self.model == None:
            self.characters_placements = sorted(self.characters_placements,
                                                key=lambda characters_placement: characters_placement.fitness)

        temp_characters_placements = list()
        for i in range(self.number_of_accepted_characters_placements):
            temp_characters_placements.append(copy.deepcopy(self.characters_placements[i]))

        while len(temp_characters_placements) < self.number_of_characters_placements - \
                self.number_of_randomly_injected_characters_placements:
            a, b = np.random.randint(low=0, high=self.number_of_parent_placements, size=2)

            temp_characters_placement = self._cyclic_crossover(
                temp_characters_placements[a],
                temp_characters_placements[b]
            )

            temp_characters_placements.append(temp_characters_placement)

        self.characters_placements = temp_characters_placements

    def random_injection(self):
        for _ in range(self.number_of_randomly_injected_characters_placements):
            random_characters_placement = copy.deepcopy(self.characters_placements[0])
            random_characters_placement.randomize()
            self.characters_placements.append(random_characters_placement)

    def mutate_characters_placements(self):
        for characters_placement in self.characters_placements[self.number_of_accepted_characters_placements:]:
            characters_placement.mutate(self.maximum_number_of_mutation_operations)

    # def save_searching_and_testing_corpus(self, dirpath):
    #     with open(os.path.join(dirpath, 'searching_corpus'), 'w', encoding='utf-8') as file:
    #         file.write('\n'.join(self.searching_corpus))
    #
    #     with open(os.path.join(dirpath, 'testing_corpus'), 'w', encoding='utf-8') as file:
    #         file.write('\n'.join(self.testing_corpus))

    def _crossover_old(self, a, b):
        new_characters_placement = copy.deepcopy(a)

        chosen_characters = list()
        for character in new_characters_placement.characters_set:
            if character.button_id != None or np.random.rand() >= 0.5:
                chosen_characters.append(character)

        needed_characters = list()
        for character in b.characters_set:
            if character not in chosen_characters:
                needed_characters.append(character)

        j = 0
        for i in range(len(new_characters_placement.characters_set)):
            if new_characters_placement.characters_set[i] in chosen_characters:
                continue

            new_characters_placement.characters_set[i] = copy.deepcopy(needed_characters[j])
            j += 1

        return new_characters_placement

    def _cyclic_crossover(self, a, b):
        new_characters_placement = copy.deepcopy(a)

        placements = list(range(len(new_characters_placement.characters_set)))
        while len(placements) > 0:
            parent = random.choice([a, b])
            original_place = random.choice(placements)
            place = original_place
            new_place = -1
            while new_place != original_place:
                new_characters_placement.characters_set[place] = parent.characters_set[place]

                new_place = a.characters_set.index(b.characters_set[place])

                placements.remove(place)
                place = new_place

        return new_characters_placement
