from collections import defaultdict
import re
import load
import regex as reg
from fractions import Fraction
from english import lang_parser
from english import lang_regex
import disambiguate as dis
import classes as cls


def extract_spellout_values(text):
    return lang_parser.extract_spellout_values(text)


####################################################
def is_quote_artifact(orig_text, span):
    """
    Distinguish between quotes and units.
    """

    res = False
    cursor = re.finditer(r'["\'][^ .,:;?!()*+-].*?["\']', orig_text)

    for item in cursor:
        if span[0] <= item.span()[1] <= span[1]:
            res = item
            break

    return res


###############################################################################
def substitute_values(text, values):
    """
    Convert spelled out numbers in a given text to digits.
    """

    shift, final_text, shifts = 0, text, defaultdict(int)
    for value in values:
        first = value["old_span"][0] + shift
        second = value["old_span"][1] + shift
        final_text = final_text[0:first] + value["new_surface"] + final_text[second:]
        shift += len(value["new_surface"]) - len(value["old_surface"])
        for char in range(first + 1, len(final_text)):
            shifts[char] = shift

    return final_text, shifts


###############################################################################


def get_values(item):
    """
    Extract value from regex hit.
    """

    def callback(pattern):
        return " %s" % (reg.unicode_fractions()[pattern.group(0)])

    fracs = r"|".join(reg.unicode_fractions())

    value = item.group("value")
    # Remove grouping operators
    value = re.sub(
        r"(?<=\d)[%s](?=\d{3})" % reg.grouping_operators_regex(), "", value
    )
    # Replace unusual exponents by e (including e)
    value = re.sub(
        r"(?<=\d)(%s)(e|E|10)\^?" % reg.multiplication_operators_regex(), "e", value
    )
    # calculate other exponents
    value, factors = resolve_exponents(value)

    value = re.sub(fracs, callback, value, re.IGNORECASE)

    range_separator = re.findall(
        r"\d+ ?((?:- )?(?:%s)) ?\d" % "|".join(reg.ranges()), value
    )
    uncer_separator = re.findall(
        r"\d+ ?(%s) ?\d" % "|".join(reg.uncertainties()), value
    )
    fract_separator = re.findall(r"\d+/\d+", value)

    value = re.sub(" +", " ", value)
    uncertainty = None
    if range_separator:
        # A range just describes an uncertain quantity
        values = value.split(range_separator[0])
        values = [
            float(re.sub(r"-$", "", v)) * factors[i] for i, v in enumerate(values)
        ]
        if values[1] < values[0]:
            raise ValueError(
                "Invalid range, with second item being smaller than the first " "item"
            )
        mean = sum(values) / len(values)
        uncertainty = mean - min(values)
        values = [mean]
    elif uncer_separator:
        values = [float(i) for i in value.split(uncer_separator[0])]
        uncertainty = values[1] * factors[1]
        values = [values[0] * factors[0]]
    elif fract_separator:
        values = value.split()
        try:
            if len(values) > 1:
                values = [float(values[0]) * factors[0] + float(Fraction(values[1]))]
            else:
                values = [float(Fraction(values[0]))]
        except ZeroDivisionError as e:
            raise ValueError("{} is not a number".format(values[0]), e)
    else:
        values = [float(re.sub(r"-$", "", value)) * factors[0]]

    return uncertainty, values


###############################################################################
def clean_text(text):
    # replacing some unicode charecters

    unicodes = {"–": "-", "−": "-", "×": "x"}
    for element in unicodes:
        text = text.replace(element, unicodes[element])

    text = lang_parser.clean_text(text)
    return text


####################################################

def resolve_exponents(value):
    """Resolve unusual exponents (like 2^4) and return substituted string and
       factor
    Params:
        value: str, string with only one value
    Returns:
        str, string with basis and exponent removed
        array of float, factors for multiplication
    """
    factors = []
    matches = re.finditer(
        reg.number_pattern_groups(), value, re.IGNORECASE | re.VERBOSE
    )
    for item in matches:
        if item.group("base") and item.group("exponent"):
            base = item.group("base")
            exp = item.group("exponent")
            if base in ["e", "E"]:
                # already handled by float
                factors.append(1)
                continue
                # exp = '10'
            # Expect that in a pure decimal base,
            # either ^ or superscript notation is used
            if re.match(r"\d+\^?", base):
                if not (
                        "^" in base
                        or re.match(r"[%s]" % reg.unicode_superscript_regex(), exp)
                ):
                    factors.append(1)
                    continue
            for superscript, substitute in reg.unicode_superscript().items():
                exp.replace(superscript, substitute)
            exp = float(exp)
            base = float(base.replace("^", ""))
            factor = base ** exp
            stripped = str(value).replace(item.group("scale"), "")
            value = stripped
            factors.append(factor)

        else:
            factors.append(1)
            continue
    return value, factors


###############################################################################
###############################################################################
def parse_unit(item, unit, slash):
    """
    Parse surface and power from unit text.
    """
    return lang_parser.parse_unit(item, unit, slash)


###############################################################################
###############################################################################
def build_unit_name(dimensions):
    """
    Build the name of the unit from its dimensions.
    """
    name = lang_parser.name_from_dimensions(dimensions)

    return name


###############################################################################

###############################################################################
def get_entity_from_dimensions(dimensions, text):
    """
    Infer the underlying entity of a unit (e.g. "volume" for "m^3") based on
    its dimensionality.
    """

    new_derived = [
        {"base": load.units().names[i["base"]].entity.name, "power": i["power"]}
        for i in dimensions
    ]

    final_derived = sorted(new_derived, key=lambda x: x["base"])
    key = load.get_key_from_dimensions(final_derived)

    ent = dis.disambiguate_entity(key, text)
    if ent is None:
        ent = cls.Entity(name="unknown", dimensions=new_derived)

    return ent


###############################################################################
def get_unit_from_dimensions(dimensions, text):
    """
    Reconcile a unit based on its dimensionality.
    """

    key = load.get_key_from_dimensions(dimensions)

    try:
        unit = load.units().derived[key]
    except KeyError:
        unit = cls.Unit(
            name=build_unit_name(dimensions),
            dimensions=dimensions,
            entity=get_entity_from_dimensions(dimensions, text),
        )

    # Carry on original composition
    unit.original_dimensions = dimensions
    return unit


###############################################################################


def get_unit(item, text):
    """
    Extract unit from regex hit.
    """

    group_units = ["prefix", "unit1", "unit2", "unit3", "unit4"]
    group_operators = ["operator1", "operator2", "operator3", "operator4"]
    # How much of the end is removed because of an "incorrect" regex match
    unit_shortening = 0
    item_units = [item.group(i) for i in group_units if item.group(i)]
    if len(item_units) == 0:
        unit = load.units().names["dimensionless"]
    else:
        derived, slash = [], False
        multiplication_operator = False
        for index in range(0, 5):
            unit = item.group(group_units[index])
            operator_index = None if index < 1 else group_operators[index - 1]
            operator = None if index < 1 else item.group(operator_index)

            # disallow spaces as operators in units expressed in their symbols
            # Enforce consistency among multiplication and division operators
            # Single exceptions are colloquial number abbreviations (5k miles)
            if operator in reg.multiplication_operators() or (
                    operator is None
                    and unit
                    and not (index == 1 and unit in lang_regex.SUFFIXES)
            ):
                if multiplication_operator != operator and not (
                        index == 1 and str(operator).isspace()
                ):
                    if multiplication_operator is False:
                        multiplication_operator = operator
                    else:
                        # Cut if inconsistent multiplication operator
                        # treat the None operator differently - remove the
                        # whole word of it
                        if operator is None:
                            # For this, use the last consistent operator
                            # (before the current) with a space
                            # which should always be the preceding operator
                            derived.pop()
                            operator_index = group_operators[index - 2]
                        # Remove (original length - new end) characters
                        unit_shortening = item.end() - item.start(operator_index)

                        break

            # Determine whether a negative power has to be applied to following
            # units
            if operator and not slash:
                slash = any(i in operator for i in reg.division_operators())
            # Determine which unit follows
            if unit:
                unit_surface, power = parse_unit(item, unit, slash)
                base = dis.disambiguate_unit(unit_surface, text)
                derived += [{"base": base, "power": power, "surface": unit_surface}]
        unit = get_unit_from_dimensions(derived, text)

    return unit, unit_shortening


###############################################################################


# Extract all quantities from the text
def parse(text):
    #for cleaning text
    text = clean_text(text)
    #for 
    orig_text = text
    values = extract_spellout_values(text)
    text, shifts = substitute_values(text, values)

    quantities = []
    for item in reg.units_regex().finditer(text):
        #iterating through all the measures
        groups = dict([i for i in item.groupdict().items() if i[1] and i[1].strip()])
        try:
            #getting the value of the measure
            uncert, values = get_values(item)
            #getting the unit of the measure
            unit, unit_shortening = get_unit(item, text)
            #getting the span of the measure
            surface, span = get_surface(shifts, orig_text, item, text, unit_shortening)
            #building them to a single object
            objs = build_quantity(
                orig_text, text, item, values, unit, surface, span, uncert
            )
            if objs is not None:
                quantities += objs
        except ValueError as err:
            pass
    return quantities


def name_from_dimensions(dimensions):
    """
    Build the name of a unit from its dimensions.
    Param:
        dimensions: List of dimensions
    """
    return lang_parser.name_from_dimensions(dimensions)


###############################################################################
###############################################################################
def get_surface(shifts, orig_text, item, text, unit_shortening=0):
    """
    Extract surface from regex hit.
    """

    # handle cut end
    span = (item.start(), item.end() - unit_shortening)
    # extend with as many spaces as are possible (this is to handle cleaned text)
    i = span[1]
    while i < len(text) and text[i] == " ":
        i += 1
    span = (span[0], i)

    real_span = (span[0] - shifts[span[0]], span[1] - shifts[span[1] - 1])
    surface = orig_text[real_span[0]: real_span[1]]

    while any(surface.endswith(i) for i in [" ", "-"]):
        surface = surface[:-1]
        real_span = (real_span[0], real_span[1] - 1)

    while surface.startswith(" "):
        surface = surface[1:]
        real_span = (real_span[0] + 1, real_span[1])

    return surface, real_span


#####################################################################################################################


def build_quantity(orig_text, text, item, values, unit, surface, span, uncert):
    """
    Build a Quantity object out of extracted information.
    Takes care of caveats and common errors
    """
    return lang_parser.build_quantity(orig_text, text, item, values, unit, surface, span, uncert)


# parse("I ran 3 km and 5 meters today for 500 seconds ")

###############################################################################
