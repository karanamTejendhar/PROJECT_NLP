import load
import no_classifier as no_clf
###############################################################################


def disambiguate_unit(unit_surface, text):
    """
    Resolve ambiguity between units with same names, symbols or abbreviations.
    :returns (str) unit name of the resolved unit
    """

    base = (
        load.units().symbols[unit_surface]
        or load.units().surfaces[unit_surface]
        or load.units().surfaces_lower[unit_surface.lower()]
        or load.units().symbols_lower[unit_surface.lower()]
    )
    '''
    if len(base) > 1:
        base = no_clf.disambiguate_no_classifier(base, text)
    elif len(base) == 1:
        base = next(iter(base))
    '''
    base = next(iter(base))
    if base:
        base = base.name
    else:
        base = "unk"

    return base


###############################################################################
def disambiguate_entity(key, text):
    """
    Resolve ambiguity between entities with same dimensionality.
    """
    try:

        derived = load.entities().derived[key]
        if len(derived) > 1:
            ent = no_clf.disambiguate_no_classifier(derived, text)
            ent = load.entities().names[ent]
        elif len(derived) == 1:
            ent = next(iter(derived))
        else:
            ent = None
    except (KeyError, StopIteration):
        ent = None

    return ent
