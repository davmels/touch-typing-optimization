from helpers import *

'''
იყვნენ ერთად, ლოგიკურები ერთად.
ფრჩხილები ერთად.
რამდენიმე სიმბოლოს მიეცი ისა, რო იყოს უშიფტოდ მთავარ რიგებში.
ლოგიკური ჯგუფები.
'''


# 2.3 minutes and 2.75 minutes with all effort things...
# 0.52 0.54
# 8.24 minutes,

class Effort:
    def __init__(self, finger_distance_weight, load_distribution_weight, modifier_overhead_weight,
                 hand_alternation_weight, consecutive_finger_usage_weight, same_hand_finger_steps_weight,
                 hit_direction_weight):
        self.finger_distance_weight = finger_distance_weight['weight']  # finger distance metric weight
        self.finger_weights = finger_distance_weight['finger_weights']
        self.load_distribution_weight = load_distribution_weight  # Ideal load distribution weight for each key
        self.modifier_overhead_weight = modifier_overhead_weight  # metric of shift usage weight
        self.hand_alternation_weight = hand_alternation_weight  # hand alternation metric weight
        # frequency of digraphs written with the same finger
        self.consecutive_finger_usage_weight = consecutive_finger_usage_weight
        self.same_hand_finger_steps_weight = same_hand_finger_steps_weight
        self.hit_direction_weight = hit_direction_weight

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
            c, _ = self.find_hand_finger(c)

            v0 += (smallest_distance[character] * (searching_corpus_dict[character] / total_symbols)) * \
                  self.finger_weights[self.finger_to_finger[c]]

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
                v2 += searching_corpus_dict[character.character]
                if index > 46:
                    v2 += searching_corpus_dict[character.character]

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
            cc1, h1 = self.find_hand_finger(c1)
            cc2, h2 = self.find_hand_finger(c2)

            if cc1 == cc2 and h1 == h2:
                v4 += searching_corpus_digraph_dict[digraph] * distance(r1, cc1, r2, cc2)

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
            cc1, h1 = self.find_hand_finger(c1)
            cc2, h2 = self.find_hand_finger(c2)
            if h1 == h2:
                v5 += searching_corpus_digraph_dict[digraph] * self.finger_step_coefficients[cc1][cc2] * math.fabs(
                    r1 - r2)

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
                if cc1 < cc2:
                    v6 += searching_corpus_digraph_dict[digraph]

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
