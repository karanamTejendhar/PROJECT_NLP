import num2words
from english import lang_speak

###############################################################################
#test

def quantity_to_spoken(quantity, lang):
    """
    Express quantity as a speakable string
    :return: Speakable version of this quantity
    """
    count = quantity.value
    if quantity.unit.entity.name == "currency" and quantity.unit.currency_code:
        try:
            return num2words.num2words(
                count, to="currency", currency=quantity.unit.currency_code
            )
        except NotImplementedError:
            pass
    return lang_speak.quantity_to_spoken(quantity)


###############################################################################
def unit_to_spoken(unit, count):
    if unit.name == "dimensionless":
        return ""
    else:
        return lang_speak.unit_to_spoken(unit, count)
