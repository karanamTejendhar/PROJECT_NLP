import re
import load
import classes as cls
from english import lang_parser
import disambiguate as dis


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
###############################################################################
def build_unit_name(dimensions):
    """
    Build the name of the unit from its dimensions.
    """
    name = lang_parser.name_from_dimensions(dimensions)


    return name


###############################################################################