import logging

LOGGER = logging.getLogger(__name__)

def version():
    """Return version number
    """
    version = None
    try:
        import pkg_resources
    except ImportError as e:
        LOGGER.error("Can't find version number, please install setuptools")
        raise e

    try:
        version = pkg_resources.get_distribution("htsworkflow")
    except pkg_resources.DistributionNotFound as e:
        LOGGER.error("Package not installed")

    return version

