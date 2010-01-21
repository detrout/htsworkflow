"""
Miscellaneous, more refined type casting functions
"""

def unicode_or_none(value):
    """
    Convert value to unicode if its not none.
    """
    if value is None:
        return None
    else:
        return unicode(value)
