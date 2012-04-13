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

def parse_flowcell_id(flowcell_id):
    """
    Return flowcell id and any status encoded in the id

    We stored the status information in the flowcell id name.
    this was dumb, but database schemas are hard to update.
    """
    fields = flowcell_id.split()
    fcid = None
    status = None
    if len(fields) > 0:
        fcid = fields[0]
    if len(fields) > 1:
        status = fields[1]
    return fcid, status

def parse_slice(slice_text):
    if slice_text is None or len(slice_text) == 0:
        return slice(None)

    slice_data = []
    for element in slice_text.split(':'):
        if len(element) == 0:
            element = None
        else:
            element = int(element)
        slice_data.append(element)

    return slice(*slice_data)


