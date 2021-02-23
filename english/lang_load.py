import inflect
import os
import json
from collections import defaultdict


TOPDIR = os.path.dirname(__file__) or "."


PLURALS = inflect.engine()


###############################################################################
def pluralize(singular, count=None):
    return PLURALS.plural(singular, count)


def number_to_words(number):
    return PLURALS.number_to_words(number)

###############################################################################

###############################################################################


def load_common_words():
    path = os.path.join(TOPDIR, "common-words.json")
    dumped = {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            dumped = json.load(file)
    except OSError:  # pragma: no cover
        pass

    words = defaultdict(list)  # Collect words based on length
    for length, word_list in dumped.items():
        words[int(length)] = word_list
    return words


COMMON_WORDS = load_common_words()