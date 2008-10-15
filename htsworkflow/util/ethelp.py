"""
ElementTree helper functions
"""
def indent(elem, level=0):
    """
    reformat an element tree to be 'pretty' (indented)
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level+1)
        # we don't want the closing tag indented too far
        child.tail = i
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def flatten(elem, include_tail=0):
    """
    Extract the text from an element tree 
    (AKA extract the text that not part of XML tags)
    """
    text = elem.text or ""
    for e in elem:
        text += flatten(e, 1)
    if include_tail and elem.tail: text += elem.tail
    return text

