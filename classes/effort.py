from classes.character import Character
from utility.helpers import *
from copy import deepcopy


class Effort:
    def __init__(self, finger_distance_weight, load_distribution_weight, modifier_overhead_weight,
                 hand_alternation_weight, consecutive_finger_usage_weight, same_hand_finger_steps_weight,
                 hit_direction_weight, hand_weights):
        self.finger_distance_weight = finger_distance_weight['weight']  # finger distance metric weight
        self.finger_weights = finger_distance_weight['finger_weights']
        self.load_distribution_weight = load_distribution_weight  # Ideal load distribution weight for each key
        self.modifier_overhead_weight = modifier_overhead_weight  # metric of shift usage weight
        self.hand_alternation_weight = hand_alternation_weight  # hand alternation metric weight
        # frequency of digraphs written with the same finger
        self.consecutive_finger_usage_weight = consecutive_finger_usage_weight
        self.same_hand_finger_steps_weight = same_hand_finger_steps_weight
        self.hit_direction_weight = hit_direction_weight
        self.hand_weights = hand_weights

        self.ideal_load_distribution_matrix = [
            [15.21 * x * 0.0001 * 0.5 for x in
             [5.45, 6.73, 10.58, 18.27, 23.40, 15.70, 15.70, 23.40, 18.27, 10.58, 6.73, 5.45, 4.17]
             ],
            [19.57 * x * 0.0001 * 0.5 for x in
             [6.73, 10.58, 18.27, 23.40, 15.70, 15.70, 23.40, 18.27, 10.58, 6.73, 5.45, 4.17]
             ],
            [47.83 * x * 0.0001 * 0.5 for x in
             [6.73, 10.58, 18.27, 23.40, 15.70, 15.70, 23.40, 18.27, 10.58, 6.73, 5.45]
             ],
            [17.39 * x * 0.0001 * 0.5 for x in
             [6.73, 10.58, 18.27, 23.40, 15.70, 15.70, 23.40, 18.27, 10.58, 6.73]
             ],
        ]
        self.ideal_load_distribution_for_shifts = [0.85, 0.15]

        # weight to multiply effort components so they, on average, are at most 1.
        self.empirical_normalisation = [1, 25, 1, 3.5, 17, 0.88, 11]
        self.georgian_letters = 'აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ'
        self.punctuation = '''".',?!:;()[]{}-/\\&*$%#@+=|<>`_^~'''
        self.keyboard_indices = [12, 12, 11, 10, 2]

        self.finger_step_coefficients = [
            [0, 5, 8, 6],
            [5, 0, 9, 7],
            [8, 9, 0, 10],
            [6, 7, 10, 0]
        ]

        self.columns = {
            (-1, 0): 3, (1,): 2, (2,): 1, (3, 4): 0, (5, 6): 0, (7,): 1, (8,): 2, (9, 10, 11): 3}
        self.finger_to_finger = {
            0: 'index',
            1: 'middle',
            2: 'ring',
            3: 'little'
        }

    def calculate_effort(self, keyboard_structure, searching_corpus_dict, characters_set,
                         searching_corpus_digraph_dict):
        effort = 0.
        if self.finger_distance_weight != 0:
            effort += self.finger_distance_weight * self.finger_distance(keyboard_structure, searching_corpus_dict,
                                                                         characters_set)
        if self.load_distribution_weight != 0:
            effort += self.load_distribution_weight * self.load_distribution(searching_corpus_dict, characters_set)
        if self.modifier_overhead_weight != 0:
            effort += self.modifier_overhead_weight * self.modifier_overhead(searching_corpus_dict, characters_set)
        if self.hand_alternation_weight != 0:
            effort += self.hand_alternation_weight * self.hand_alternation(searching_corpus_digraph_dict,
                                                                           characters_set)
        if self.consecutive_finger_usage_weight != 0:
            effort += self.consecutive_finger_usage(searching_corpus_digraph_dict,
                                                    characters_set) * self.consecutive_finger_usage_weight
        if self.same_hand_finger_steps_weight != 0:
            effort += self.same_hand_finger_steps(searching_corpus_digraph_dict,
                                                  characters_set) * self.same_hand_finger_steps_weight
        if self.hit_direction_weight != 0:
            effort += self.hit_direction(searching_corpus_digraph_dict,
                                         characters_set) * self.hit_direction_weight

        return round(effort, 9)

    def finger_distance(self, keyboard_structure, searching_corpus_dict, characters_set):
        v0 = 0.

        total_symbols = self.find_total_symbols(searching_corpus_dict)
        character_to_index = self.find_character_indices(characters_set)

        smallest_distance = dict()
        for i, character in enumerate(characters_set):
            smallest_distance[character.character] = \
                keyboard_structure.smallest_distance_from_button_to_finger(i if i < 47 else i - 47)

        for character in searching_corpus_dict:
            if character not in smallest_distance:
                warning_log('Found unrecognized character \'%s\'' % character)
                continue

            r, c, _ = self.find_index(character_to_index[character])
            if r == 0:
                c -= 1

            hand = self.find_hand(c)

            c, _ = self.find_hand_finger(c)

            v0 += (smallest_distance[character] * (searching_corpus_dict[character] / total_symbols)) * \
                  self.finger_weights[self.finger_to_finger[c]] * self.hand_weights[hand]

        return v0 * self.empirical_normalisation[0]

    # try using np for faster calculations.
    def load_distribution(self, searching_corpus_dict, characters_set):
        v1 = 0

        total_symbols = self.find_total_symbols(searching_corpus_dict)

        for index, character in enumerate(characters_set):
            if character.character in searching_corpus_dict:
                i, index, shift = self.find_index(index)
                v1 += (searching_corpus_dict[character.character] / total_symbols -
                       self.ideal_load_distribution_matrix[i][index] * self.ideal_load_distribution_for_shifts[
                           shift]) ** 2
        return v1 * self.empirical_normalisation[
            1]  # to be 1 at most on average (not sure how I've calculated the average though...)

    # How many keys have been pressed with shift
    def modifier_overhead(self, searching_corpus_dict, characters_set):
        v2 = 0
        total_symbols = self.find_total_symbols(searching_corpus_dict)

        for index, character in enumerate(characters_set):
            if character.character in searching_corpus_dict:
                r, c, _ = self.find_index(index)
                if r == 0:
                    c -= 1
                hand = self.find_hand(c)
                v2 += searching_corpus_dict[character.character] * self.hand_weights[hand]
                if index > 46:
                    v2 += searching_corpus_dict[character.character] * self.hand_weights[hand]

        return v2 / total_symbols * self.empirical_normalisation[2]

    def hand_alternation(self, searching_corpus_digraph_dict, characters_set):
        v3 = 0
        total_digraphs = self.find_total_digraphs(searching_corpus_digraph_dict)

        character_to_index = self.find_character_indices(characters_set)

        for digraph in searching_corpus_digraph_dict:

            index_a = character_to_index[digraph[0]]
            i, index_a, shift = self.find_index(index_a)
            if i == 0:
                index_a -= 1

            index_b = character_to_index[digraph[1]]
            i, index_b, shift = self.find_index(index_b)
            if i == 0:
                index_b -= 1

            if index_a < 5 and index_b < 5 or index_a > 4 and index_b > 4:
                # if (digraph[0] in self.georgian_letters and digraph[1] in self.georgian_letters) or \
                #         (digraph[0] in self.punctuation and digraph[1] in self.punctuation):
                v3 += searching_corpus_digraph_dict[digraph]

        return v3 * self.empirical_normalisation[3] / total_digraphs

    def consecutive_finger_usage(self, searching_corpus_digraph_dict, characters_set):
        v4 = 0
        total_digraphs = self.find_total_digraphs(searching_corpus_digraph_dict)

        character_to_index = self.find_character_indices(characters_set)

        def distance(r1, c1, r2, c2):
            return math.fabs(r1 - r2) + math.fabs(c1 - c2)

        for digraph in searching_corpus_digraph_dict:
            r1, c1, sh1 = self.find_index(character_to_index[digraph[0]])
            r2, c2, sh2 = self.find_index(character_to_index[digraph[1]])
            if r1 == 0:
                c1 -= 1
            if r2 == 0:
                c2 -= 1
            hand = self.find_hand(c1)
            cc1, h1 = self.find_hand_finger(c1)
            cc2, h2 = self.find_hand_finger(c2)

            if cc1 == cc2 and h1 == h2:
                v4 += searching_corpus_digraph_dict[digraph] * distance(r1, cc1, r2, cc2) * self.hand_weights[hand]

        return v4 / total_digraphs * self.empirical_normalisation[4]

    def same_hand_finger_steps(self, searching_corpus_digraph_dict, characters_set):
        v5 = 0

        character_to_index = self.find_character_indices(characters_set)

        total_digraphs = self.find_total_digraphs(searching_corpus_digraph_dict)

        for digraph in searching_corpus_digraph_dict:
            r1, c1, sh1 = self.find_index(character_to_index[digraph[0]])
            r2, c2, sh2 = self.find_index(character_to_index[digraph[1]])
            if r1 == 0:
                c1 -= 1
            if r2 == 0:
                c2 -= 1
            hand = self.find_hand(c1)
            cc1, h1 = self.find_hand_finger(c1)
            cc2, h2 = self.find_hand_finger(c2)
            if h1 == h2:
                v5 += searching_corpus_digraph_dict[digraph] * self.finger_step_coefficients[cc1][cc2] * math.fabs(
                    r1 - r2) * self.hand_weights[hand]

        return v5 / total_digraphs * self.empirical_normalisation[5]

    def hit_direction(self, searching_corpus_digraph_dict, characters_set):
        v6 = 0
        character_to_index = self.find_character_indices(characters_set)
        total_digraphs = self.find_total_digraphs(searching_corpus_digraph_dict)

        for digraph in searching_corpus_digraph_dict:
            r1, c1, sh1 = self.find_index(character_to_index[digraph[0]])
            r2, c2, sh2 = self.find_index(character_to_index[digraph[1]])
            if r1 == 0:
                c1 -= 1
            if r2 == 0:
                c2 -= 1
            cc1, h1 = self.find_hand_finger(c1)
            cc2, h2 = self.find_hand_finger(c2)
            if h1 == h2:
                hand = self.find_hand(c1)
                if cc1 < cc2:
                    v6 += searching_corpus_digraph_dict[digraph] * self.hand_weights[hand]

        return v6 / total_digraphs * self.empirical_normalisation[6]

    def find_index(self, index):
        shift = 0
        if index > 46:
            shift = 1
            index -= 47
        i = 0
        while index >= self.keyboard_indices[i]:
            index -= self.keyboard_indices[i]
            i += 1
        if i == 0:
            index += 1
        if i == 4 and index != 1:
            i = 0
        return i, index, shift

    # index: 0, middle: 1, ring:2, pinky: 3
    def find_hand_finger(self, col):
        for key, value in self.columns.items():
            if col in key:
                return value, 0 if key[0] < 5 else 1

    def find_total_digraphs(self, searching_corpus_digraph_dict):
        total_digraphs = 0
        for count in searching_corpus_digraph_dict.values():
            total_digraphs += count
        return total_digraphs

    def find_total_symbols(self, searching_corpus_dict):
        total_symbols = 0
        for count in searching_corpus_dict.values():
            total_symbols += count
        return total_symbols

    def find_character_indices(self, characters_set):
        character_to_index = {}
        for index, character in enumerate(characters_set):
            character_to_index[character.character] = index
        return character_to_index

    def calculate_effort_detailed(self, keyboard_structure, searching_corpus_dict, characters_set,
                                  searching_corpus_digraph_dict):
        effort = {}
        if self.finger_distance_weight != 0:
            effort['finger_distance_effort'] = self.finger_distance_weight * self.finger_distance(keyboard_structure,
                                                                                                  searching_corpus_dict,
                                                                                                  characters_set)
        else:
            effort['finger_distance_effort'] = 0.
        # if self.load_distribution_weight != 0:
        #     effort['load_distribution_weight'] = (
        #             self.load_distribution_weight * self.load_distribution(searching_corpus_dict, characters_set))
        # else:
        #     effort['load_distribution_weight'] = 0.
        if self.modifier_overhead_weight != 0:
            effort['modifier_overhead_effort'] = self.modifier_overhead_weight * self.modifier_overhead(
                searching_corpus_dict, characters_set)
        else:
            effort['modifier_overhead_effort'] = 0.
        if self.hand_alternation_weight != 0:
            effort['hand_alternation_effort'] = self.hand_alternation_weight * self.hand_alternation(
                searching_corpus_digraph_dict,
                characters_set)
        else:
            effort['hand_alternation_effort'] = 0.
        if self.consecutive_finger_usage_weight != 0:
            effort['consecutive_finger_usage_effort'] = self.consecutive_finger_usage(searching_corpus_digraph_dict,
                                                                                      characters_set) * self.consecutive_finger_usage_weight
        else:
            effort['consecutive_finger_usage_effort'] = 0.
        if self.same_hand_finger_steps_weight != 0:
            effort['same_hand_finger_steps_effort'] = self.same_hand_finger_steps(searching_corpus_digraph_dict,
                                                                                  characters_set) * self.same_hand_finger_steps_weight
        else:
            effort['same_hand_finger_steps_effort'] = 0.
        if self.hit_direction_weight != 0:
            effort['hit_direction_effort'] = self.hit_direction(searching_corpus_digraph_dict,
                                                                characters_set) * self.hit_direction_weight
        else:
            effort['hit_direction_effort'] = 0.

        left_old = self.hand_weights['left']
        right_old = self.hand_weights['right']
        self.hand_weights['left'] = 1
        self.hand_weights['right'] = 0
        effort['left_hand_effort'] = self.calculate_effort(keyboard_structure, searching_corpus_dict, characters_set,
                                                           searching_corpus_digraph_dict)
        self.hand_weights['left'] = 0
        self.hand_weights['right'] = 1
        effort['right_hand_effort'] = self.calculate_effort(keyboard_structure, searching_corpus_dict, characters_set,
                                                            searching_corpus_digraph_dict)
        self.hand_weights = {"left": left_old, "right": right_old}
        effort['total_effort'] = self.calculate_effort(keyboard_structure, searching_corpus_dict, characters_set,
                                                       searching_corpus_digraph_dict)

        with open("data_dir/predefined_layouts/genetic_config_qwerty.json", 'r', encoding='utf-8') as json_file:
            qwerty_config = json.load(json_file)
            qwerty_effort = qwerty_config['effort_parameters']

            effort1 = Effort(finger_distance_weight=qwerty_effort['finger_distance_weight'],
                             load_distribution_weight=qwerty_effort['load_distribution_weight'],
                             modifier_overhead_weight=qwerty_effort['modifier_overhead_weight'],
                             hand_alternation_weight=qwerty_effort['hand_alternation_weight'],
                             consecutive_finger_usage_weight=qwerty_effort['consecutive_finger_usage_weight'],
                             same_hand_finger_steps_weight=qwerty_effort['same_hand_finger_steps_weight'],
                             hit_direction_weight=qwerty_effort['hit_direction_weight'],
                             hand_weights=self.hand_weights)
            print("right here mate")
            print(self.finger_distance_weight,
                  self.load_distribution_weight,
                  self.modifier_overhead_weight,
                  self.hand_alternation_weight,
                  self.consecutive_finger_usage_weight,
                  self.same_hand_finger_steps_weight,
                  self.hit_direction_weight,
                  self.hand_weights)
            print(effort1.finger_distance_weight,
                  effort1.load_distribution_weight,
                  effort1.modifier_overhead_weight,
                  effort1.hand_alternation_weight,
                  effort1.consecutive_finger_usage_weight,
                  effort1.same_hand_finger_steps_weight,
                  effort1.hit_direction_weight,
                  effort1.hand_weights)
            print([x.character for x in characters_set])
            characters_set2 = list()
            for character in qwerty_config['characters_set']:
                characters_set2.append(Character(
                    character=character['character'],
                    button_id=character['button_id'],
                ))
            print([x.character for x in characters_set2])

            effort['qwerty_effort'] = effort1.calculate_effort(keyboard_structure, searching_corpus_dict,
                                                               characters_set2, searching_corpus_digraph_dict)

        with open("data_dir/predefined_layouts/genetic_config_dvorjak.json", 'r', encoding='utf-8') as json_file:
            dvorjak_config = json.load(json_file)
            dvorjak_effort = dvorjak_config['effort_parameters']
            effort2 = Effort(finger_distance_weight=dvorjak_effort['finger_distance_weight'],
                             load_distribution_weight=dvorjak_effort['load_distribution_weight'],
                             modifier_overhead_weight=dvorjak_effort['modifier_overhead_weight'],
                             hand_alternation_weight=dvorjak_effort['hand_alternation_weight'],
                             consecutive_finger_usage_weight=dvorjak_effort['consecutive_finger_usage_weight'],
                             same_hand_finger_steps_weight=dvorjak_effort['same_hand_finger_steps_weight'],
                             hit_direction_weight=dvorjak_effort['hit_direction_weight'],
                             hand_weights=self.hand_weights)

            characters_set2 = list()
            for character in dvorjak_config['characters_set']:
                characters_set2.append(Character(
                    character=character['character'],
                    button_id=character['button_id'],
                ))

            effort['dvorjak_effort'] = effort2.calculate_effort(keyboard_structure, searching_corpus_dict,
                                                                characters_set2,
                                                                searching_corpus_digraph_dict)
        print(effort)
        return effort

    def find_hand(self, c):
        if c < 5:
            return "left"
        return "right"
