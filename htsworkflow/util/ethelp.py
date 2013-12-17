"""ElementTree helper functions
"""
import logging
import os
LOGGER = logging.getLogger(__name__)

import lxml.etree

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

def validate_xhtml(html, base_url='http://localhost'):
    """Helper for validating xhtml, mostly intended for test code

    Defaults to assuming XHTML+RDFa
    Returns None if there was a problem configuring validation
    Logs messages from lxml.etree using python logging
    Returns True if it passed validation
    and False if it fails.
    """
    try:
        XHTML_RDF_DTD = lxml.etree.DTD(external_id='-//W3C//DTD XHTML+RDFa 1.0//EN')
    except lxml.etree.DTDParseError as e:
        LOGGER.warn("Unable to load XHTML DTD %s" % (str(e),))
        return

    try:
        root = lxml.etree.fromstring(html, base_url=base_url)
    except lxml.etree.ParseError as e:
        LOGGER.warn("Unable to parse document: %s" % (str(e),))
        return False

    if XHTML_RDF_DTD.validate(root):
        # so unlikely.
        return True

    isgood = True
    for msg in XHTML_RDF_DTD.error_log.filter_from_errors():
        # I have no idea how to suppress this error
        # but I need the xmlns attributes for of my RDFa 1.0 encoding
        if 'ERROR:VALID:DTD_UNKNOWN_ATTRIBUTE' in str(msg):
            continue
        else:
            LOGGER.error(msg)
            isgood = False

    return isgood
