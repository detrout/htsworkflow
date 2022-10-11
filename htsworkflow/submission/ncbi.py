"""Start extracting information out of NCBI SRA

It probably could be extended to extract other NCBI information.
But at the time I just needed to look up things in the short read archive.
"""

import logging
from lxml.etree import parse, XSLT, tostring, fromstring
from optparse import OptionParser
import os
import RDF
import urllib

from htsworkflow.util.rdfhelp import get_model, dump_model

from django.conf import settings
from django.template import Context, loader

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'htsworkflow.settings'

LOGGER = logging.getLogger(__name__)

ESEARCH_URL="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
EFETCH_URL="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
DB = 'sra'
DEFAULT_QUERY = 'wgEncodeCaltechRnaSeq OR wgEncodeCaltechHist OR wgEncodeCaltechTfbs'

def search_ncbi_ids(database, term, return_max=200):
    """Return list of IDs from a NCBI database
    database - which ncbi database to search
    term - ncbi query string
    return_max - maximum records to return
    """
    search = {'db': database,
              'term': term,
              'retmax': return_max}
    tree = parse(ESEARCH_URL + urllib.urlencode(search))
    root = tree.getroot()
    count = get_node_scalar(root, '/eSearchResult/Count', int)
    retmax_node = get_node_scalar(root, '/eSearchResult/RetMax', int)

    if count > retmax_node:
        raise ValueError("Too many values returned please adjust query")

    id_nodes = tree.xpath('/eSearchResult/IdList/Id')
    if len(id_nodes) != count:
        errmsg = "Weird. Length of ID list ({0}) doesn't match count ({1})"
        raise ValueError(errmsg.format(len(id_nodes), count))

    ids = [ x.text for x in id_nodes ]
    return ids

def parse_sra_metadata_into_model(model, ncbi_id):
    """Extract SRA data by looking up a NCBI ID.
    """
    search = {'db':DB,
              'id': ncbi_id}
    url = EFETCH_URL + urllib.urlencode(search)
    tree = parse(url)

    context = Context()
    sra_rdf_template = loader.get_template('sra.rdfxml.xsl')
    sra_rdf_stylesheet = sra_rdf_template.render(context)
    sra_rdf_transform = XSLT(fromstring(sra_rdf_stylesheet))
    rdfdata = tostring(sra_rdf_transform(tree))
    rdfparser = RDF.Parser(name='rdfxml')
    rdfparser.parse_string_into_model(model, rdfdata, url)

def get_node_scalar(parent, xpath, target_type=None):
    """Return a single value from an xpath search, possibily type converted

    target_type pass a constructor that takes a string to convert result
    of search
    """
    node = parent.xpath(xpath)
    if node is None or len(node) != 1:
        raise ValueError("Wrong response, incorrect number of {0} tags".xpath)
    if target_type is not None:
        return target_type(node[0].text)
    else:
        return node[0].text

def main(cmdline=None):
    """Quick driver for importing data from SRA"""
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    if opts.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif opts.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARN)

    model = get_model(opts.database, opts.dbpath)

    ids = search_ncbi_ids('sra', opts.query)
    for count, encode_id in enumerate(ids[:1]):
        LOGGER.info("processing %s %d / %d", encode_id, count+1, len(ids))
        parse_sra_metadata_into_model(model, encode_id)

    if opts.dump:
        dump_model(model)

def make_parser():
    parser = OptionParser()
    parser.add_option('--dbpath', help="Database directory",
                      default=os.getcwd())
    parser.add_option('--database', help="Database name", default=None)
    parser.add_option('--dump', help="dump database", default=False,
                      action="store_true")
    parser.add_option('--query', help='specify NCBI search terms',
                      default=DEFAULT_QUERY)
    parser.add_option("-v", "--verbose", action="store_true", default=False)
    parser.add_option("--debug", action="store_true", default=False)
    return parser

if __name__ == "__main__":
    main()
