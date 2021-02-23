import re

from english import lang_regex
import load

###############################################################
def suffixes(lang="en_US"):
    return lang_regex.SUFFIXES

def units():
    return lang_regex.UNITS


def tens():
    return lang_regex.TENS


def scales():
    return lang_regex.SCALES


def decimals():
    return lang_regex.DECIMALS


def miscnum():
    return lang_regex.MISCNUM


def powers(lang="en_US"):
    return lang_regex.POWERS


def exponents_regex():
    return lang_regex.EXPONENTS_REGEX


def ranges():
    ranges_ = {"-"}
    ranges_.update(lang_regex.RANGES)
    return ranges_


def uncertainties():
    uncertainties_ = {r"\+/-", r"±"}
    uncertainties_.update(lang_regex.UNCERTAINTIES)
    return uncertainties_


###############################################################


def decimal_operators():
    return lang_regex.DECIMAL_OPERATORS


def decimal_operators_regex():
    return "".join(decimal_operators())


def unicode_fractions():
    uni_frac = {
        u"¼": "1/4",
        u"½": "1/2",
        u"¾": "3/4",
        u"⅐": "1/7",
        u"⅑": "1/9",
        u"⅒": "1/10",
        u"⅓": "1/3",
        u"⅔": "2/3",
        u"⅕": "1/5",
        u"⅖": "2/5",
        u"⅗": "3/5",
        u"⅘": "4/5",
        u"⅙": "1/6",
        u"⅚": "5/6",
        u"⅛": "1/8",
        u"⅜": "3/8",
        u"⅝": "5/8",
        u"⅞": "7/8",
    }
    return uni_frac


def unicode_fractions_regex():
    return re.escape("".join(list(unicode_fractions().keys())))


def unicode_superscript():
    uni_super = {
        u"¹": "1",
        u"²": "2",
        u"³": "3",
        u"⁴": "4",
        u"⁵": "5",
        u"⁶": "6",
        u"⁷": "7",
        u"⁸": "8",
        u"⁹": "9",
        u"⁰": "0",
    }
    return uni_super


def unicode_superscript_regex():
    return re.escape("".join(list(unicode_superscript().keys())))


def multiplication_operators():
    mul = {u"*", u" ", u"·", u"x"}
    mul.update(lang_regex.MULTIPLICATION_OPERATORS)
    return mul


def multiplication_operators_regex():
    return r"|".join(r"%s" % re.escape(i) for i in multiplication_operators())


def grouping_operators():
    grouping_ops = {" "}
    grouping_ops.update(lang_regex.GROUPING_OPERATORS)
    return grouping_ops


def grouping_operators_regex():
    return "".join(grouping_operators())


def division_operators():
    div = {u"/"}
    div.update(lang_regex.DIVISION_OPERATORS)
    return div


def operators():
    ops = set()
    ops.update(multiplication_operators())
    ops.update(division_operators())
    return ops

# Pattern for extracting a digit-based number


NUM_PATTERN = r"""
    (?{number}              # required number
        [+-]?                  #   optional sign
        (\.?\d+|[{unicode_fract}])     #   required digits or unicode fraction
        (?:[{grouping}]\d{{3}})*         #   allowed grouping
        (?{decimals}[{decimal_operators}]\d+)?    #   optional decimals
    )
    (?{scale}               # optional exponent
        (?:{multipliers})?                #   multiplicative operators
        (?{base}(E|e|\d+)\^?)    #   required exponent prefix
        (?{exponent}[+-]?\d+|[{superscript}]) # required exponent, superscript
                                              # or normal
    )?
    (?{fraction}             # optional fraction
        \ \d+/\d+|\ ?[{unicode_fract}]|/\d+
    )?
"""


# Pattern for extracting a digit-based number
def number_pattern():
    return NUM_PATTERN


def number_pattern_no_groups():
    return NUM_PATTERN.format(
        number=":",
        decimals=":",
        scale=":",
        base=":",
        exponent=":",
        fraction=":",
        grouping=grouping_operators_regex(),
        multipliers=multiplication_operators_regex(),
        superscript=unicode_superscript_regex(),
        unicode_fract=unicode_fractions_regex(),
        decimal_operators=decimal_operators_regex(),
    )


def number_pattern_groups():
    return NUM_PATTERN.format(
        number="P<number>",
        decimals="P<decimals>",
        scale="P<scale>",
        base="P<base>",
        exponent="P<exponent>",
        fraction="P<fraction>",
        grouping=grouping_operators_regex(),
        multipliers=multiplication_operators_regex(),
        superscript=unicode_superscript_regex(),
        unicode_fract=unicode_fractions_regex(),
        decimal_operators=decimal_operators_regex(),
    )


def range_pattern():
    num_pattern_no_groups = number_pattern_no_groups()
    return r"""                        # Pattern for a range of numbers
    (?:                                    # First number
        (?<![a-zA-Z0-9+.-])                # lookbehind, avoid "Area51"
        %s
    )
    (?:                                    # Second number
        \ ?(?:(?:-\ )?(?:%s|%s))\ ?  # Group for ranges or uncertainties
    %s)?
    """ % (
        num_pattern_no_groups,
        "|".join(ranges()),
        "|".join(uncertainties()),
        num_pattern_no_groups,
    )

################################################################


def numberwords():
    """
    Convert number words to integers in a given text.
    """

    numwords = {}

    numwords.update(miscnum())

    for idx, word in enumerate(units()):
        numwords[word] = (1, idx)
    for idx, word in enumerate(tens()):
        numwords[word] = (1, idx * 10)
    for idx, word in enumerate(scales()):
        numwords[word] = (10 ** (idx * 3 or 2), 0)
    for word, factor in decimals().items():
        numwords[word] = (factor, 0)
        numwords[load.pluralize(word)] = (factor, 0)

    return numwords


def numberwords_regex():
    all_numbers = r"|".join(
        r"((?<=\W)|^)%s((?=\W)|$)" % i for i in list(numberwords().keys()) if i
    )
    return all_numbers

#################################################################


def text_pattern_reg():
    txt_pattern = lang_regex.TEXT_PATTERN.format(
        number_pattern_no_groups=number_pattern_no_groups(),
        numberwords_regex=numberwords_regex(),
    )
    reg_txt = re.compile(txt_pattern, re.VERBOSE | re.IGNORECASE)
    return reg_txt

###############################################################################


def units_regex():
    """
    Build a compiled regex object. Groups of the extracted items, with 4
    repetitions, are:
        0: whole surface
        1: prefixed symbol
        2: numerical value
        3: first operator
        4: first unit
        5: second operator
        6: second unit
        7: third operator
        8: third unit
        9: fourth operator
        10: fourth unit
    Example, 'I want $20/h'
        0: $20/h
        1: $
        2: 20
        3: /
        4: h
        5: None
        6: None
        7: None
        8: None
        9: None
        10: None
    """

    op_keys = sorted(list(operators()), key=len, reverse=True)
    unit_keys = sorted(
        list(load.units().surfaces.keys()) + list(load.units().symbols.keys()),
        key=len,
        reverse=True,
    )
    symbol_keys = sorted(
        list(load.units().prefix_symbols.keys()), key=len, reverse=True
    )

    exponent = exponents_regex().format(superscripts=unicode_superscript_regex())

    all_ops = "|".join([r"{}".format(re.escape(i)) for i in op_keys])
    all_units = "|".join([r"{}".format(re.escape(i)) for i in unit_keys])
    all_symbols = "|".join([r"{}".format(re.escape(i)) for i in symbol_keys])

    pattern = r"""
        (?<!\w)                                     # "begin" of word
        (?P<prefix>(?:%s)(?![a-zA-Z]))?         # Currencies, mainly
        (?P<value>%s)-?                           # Number
        (?:(?P<operator1>%s(?=(%s)%s))?(?P<unit1>(?:%s)%s)?)    # Operator + Unit (1)
        (?:(?P<operator2>%s(?=(%s)%s))?(?P<unit2>(?:%s)%s)?)    # Operator + Unit (2)
        (?:(?P<operator3>%s(?=(%s)%s))?(?P<unit3>(?:%s)%s)?)    # Operator + Unit (3)
        (?:(?P<operator4>%s(?=(%s)%s))?(?P<unit4>(?:%s)%s)?)    # Operator + Unit (4)
        (?!\w)                                      # "end" of word
    """ % tuple(
        [all_symbols, range_pattern()]
        + 4 * [all_ops, all_units, exponent, all_units, exponent]
    )

    regex = re.compile(pattern, re.VERBOSE | re.IGNORECASE)

    return regex
