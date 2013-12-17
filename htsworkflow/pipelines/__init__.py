"""
Provide code to interact with the vendor tools to produce useable "raw" data.

the illumina sub-package contains components to interact with the Illumina provided
GAPipeline
"""
import lxml.etree as ElementTree

EUROPEAN_STRPTIME = "%d-%m-%Y"
EUROPEAN_DATE_RE = "([0-9]{1,2}-[0-9]{1,2}-[0-9]{4,4})"
VERSION_RE = "([0-9\.]+)"
USER_RE = "([a-zA-Z0-9]+)"
LANES_PER_FLOWCELL = 8
LANE_LIST = range(1, LANES_PER_FLOWCELL + 1)

