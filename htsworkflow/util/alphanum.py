# from http://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
# modified by Diane Trout

import re

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    if isinstance(s, type("")) or isinstance(s, type(u"")):
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(_nsre, s)]
    elif isinstance(s, int):
        return [s]
    else:
        raise ValueError("Unsupported type %s for input %s" % (type(s), s))
