

def report_error(message):
    """
    Return a dictionary with a command to display 'message'
    """
    return {'mode': 'Error', 'status': message}
    

def redirect_to_url(url):
    """
    Return a bcm dictionary with a command to redirect to 'url'
    """
    return {'mode': 'redirect', 'url': url}
    

def autofill(field, value):
    """
    Return a bcm dictionary with a command to automatically fill the
    corresponding "field" with "value"
    """
    return {'mode': 'autofill', 'field': field, 'value': value}