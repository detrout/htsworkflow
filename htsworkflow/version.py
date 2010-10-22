import logging

def version():
    """Return version number    
    """
    version = None
    try:
        import pkg_resources
    except ImportError, e:
        logging.error("Can't find version number, please install setuptools")
        raise e

    try:
        version = pkg_resources.get_distribution("htsworkflow")
    except pkg_resources.DistributionNotFound, e:
        logging.error("Package not installed")

    return version
        
