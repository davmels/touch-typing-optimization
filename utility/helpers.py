import json
import re
import sys
import time
import math
import random

import numpy as np

PX = 37.7952755906


# 1 centimeter = 37.7952755906 pixels

def cm2px(cm):
    """
    Convert from centimeter to pixels

    Parameters
    cm: length(s) in centimeters, whether single value, tuple or list

    Return
    length(s) in pixels, whether single value, tuple or list
    """
    if type(cm) is float or type(cm) is int:
        return round(cm * PX)
    elif type(cm) is tuple:
        return tuple([round(item * PX) for item in cm])
    elif type(cm) is list:
        return [round(item * PX) for item in cm]
    raise ValueError('\'cm\' type should be float, int, tuple or list!')


def random_color():
    """
    Randomize a bright RGB color

    Return
    tuple of 3 random numbers representing red, green and blue values
    """

    def gen():
        return round(10 * math.sqrt(random.randint(100, 255)))

    return (gen(), gen(), gen())


def get_current_time():
    """
    Local time getter function

    Return
    time formatted like: 'Fri Aug 16 14:13:41 2019'
    """
    return time.asctime(time.localtime(time.time()))


def info_log(message):
    """
    Logging function for information
    """
    print('info: %s] %s' % (get_current_time(), message))


def warning_log(message):
    """
    Logging function for warnings
    """
    print('warning: %s] %s' % (get_current_time(), message))


def error_log(message, is_exit):
    """
    Logging function for errors

    Raise
    raises a 'SystemExit' error if 'is_exit' is True
    """
    print('error: %s] %s' % (get_current_time(), message), file=sys.stderr)
    if is_exit:
        raise SystemExit(message)


def process_corpus(**kwargs):
    info_log("Constructing dictionaries of frequencies of monographs and digraphs")
    with open("data_dir/searching_corpus_dict.json", 'r', encoding='utf-8') as json_file:
        searching_corpus_dict = json.load(json_file)

    with open("data_dir/searching_corpus_digraph_dict.json", 'r', encoding='utf-8') as json_file:
        searching_corpus_digraph_dict = json.load(json_file)

    with open("data_dir/testing_corpus_dict.json", 'r', encoding='utf-8') as json_file:
        testing_corpus_dict = json.load(json_file)

    with open("data_dir/testing_corpus_digraph_dict.json", 'r', encoding='utf-8') as json_file:
        testing_corpus_digraph_dict = json.load(json_file)

    return searching_corpus_dict, searching_corpus_digraph_dict, testing_corpus_dict, testing_corpus_digraph_dict


def generate_name_from_config(config, date=True, generations=True, hands=False):
    name = [f"{config['effort_parameters']['finger_distance_weight']['weight']:.2f}"]
    for value in list(config['effort_parameters'].values())[1:-1]:
        name.append(f"{value:.2f}")

    name = " - ".join(name)
    if generations:
        name = f"{config['number_of_generations']:.2f}" + "-- " + name

    if date:
        from datetime import datetime

        current_date_time = datetime.now()
        date_string = current_date_time.strftime("%Y-%m-%d %H-%M-%S")
        name = name + " #  " + date_string

    if hands:
        name += f" - {config['effort_parameters']['hand_weights']['left']:.2f} - {config['effort_parameters']['hand_weights']['right']:.2f}"

    return name


def get_non_fixed_punctuation(characters_placement):
    punctuations = '''".',?!:;()[]{}-/&*$%#@+=<>`_^~'''
    # georgian_letters = 'აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ'
    non_fixed_punctuation = []
    for character in characters_placement:
        if character.character in punctuations and character.button_id is None:
            non_fixed_punctuation.append(character)
    return non_fixed_punctuation


def get_non_fixed_letters(characters_placement):
    # punctuations = '''".',?!:;()[]{}-/&*$%#@+=<>`_^~'''
    georgian_letters = 'აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ'
    non_fixed_letters = []
    for character in characters_placement:
        if character.character in georgian_letters and character.button_id is None:
            non_fixed_letters.append(character)
    return non_fixed_letters
