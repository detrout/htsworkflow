#!/usr/bin/env python
"""
Gather information about our submissions into a single RDF store
"""

from datetime import datetime
import hashlib
import httplib2
import keyring
import logging
from lxml.html import fromstring
from operator import attrgetter
from optparse import OptionParser, OptionGroup
# python keyring
import os
import re
# redland rdf lib
import RDF
import sys
import urllib
import urlparse

from htsworkflow.submission import daf, ucsc

from htsworkflow.util import api
from htsworkflow.util.rdfhelp import \
     dafTermOntology, \
     dublinCoreNS, \
     get_model, \
     get_serializer, \
     sparql_query, \
     submissionOntology, \
     libraryOntology, \
     load_into_model, \
     rdfNS, \
     rdfsNS, \
     xsdNS
TYPE_N = rdfNS['type']
CREATION_DATE = libraryOntology['date']

# URL mappings
LIBRARY_NS = RDF.NS("http://jumpgate.caltech.edu/library/")

from htsworkflow.submission.ucsc import \
     daf_download_url, \
     ddf_download_url, \
     get_ucsc_file_index, \
     submission_view_url, \
     UCSCEncodePipeline

DCC_NS = RDF.NS(UCSCEncodePipeline + 'download_ddf#')

DBDIR = os.path.expanduser("~diane/proj/submission")

LOGGER = logging.getLogger("encode_find")

LOGIN_URL = 'http://encodesubmit.ucsc.edu/account/login'
USER_URL = 'http://encodesubmit.ucsc.edu/pipeline/show_user'

USERNAME = 'detrout'
CHARSET = 'utf-8'

GOLDEN_PATH_TEST = "http://hgdownload-test.cse.ucsc.edu/goldenPath/"\
                   "{genome}/encodeDCC/{composite}/"
def main(cmdline=None):
    """
    Parse command line arguments

    Takes a list of arguments (assuming arg[0] is the program name) or None
    If None, it looks at sys.argv
    """
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    if opts.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif opts.verbose:
        logging.basicConfig(level=logging.INFO)

    htsw_authdata = api.make_auth_from_opts(opts, parser)
    htswapi = api.HtswApi(opts.host, htsw_authdata)

    cookie = None
    model = get_model(opts.load_model, DBDIR)

    if opts.load_rdf is not None:
        ns_uri = submissionOntology[''].uri
        load_into_model(model, opts.rdf_parser_name, opts.load_rdf, ns_uri)

    if len(args) == 0:
        limit = None
    else:
        limit = args

    if opts.update:
        cookie = login(cookie=cookie)
        load_my_submissions(model, limit=limit, cookie=cookie)
        load_encode_libraries(model, htswapi)
        our_tracks = [
            {'genome':'hg19', 'composite':'wgEncodeCaltechRnaSeq'},
            {'genome':'mm9',  'composite':'wgEncodeCaltechHist'},
            {'genome':'mm9',  'composite':'wgEncodeCaltechHistone'},
            {'genome':'mm9',  'composite':'wgEncodeCaltechTfbs'}
        ]
        for track_info in our_tracks:
            load_encodedcc_files(model, GOLDEN_PATH_TEST.format(**track_info))


    if opts.sparql is not None:
        sparql_query(model, opts.sparql)

    if opts.find_submission_with_no_library:
        find_submissions_with_no_library(model)

    if opts.print_rdf:
        serializer = get_serializer(name=opts.rdf_parser_name)
        print serializer.serialize_model_to_string(model)


def make_parser():
    """Construct option parser
    """
    parser = OptionParser()
    commands = OptionGroup(parser, "Commands")
    commands.add_option('--load-model', default=None,
      help="Load model database")
    commands.add_option('--load-rdf', default=None,
      help="load rdf statements into model")
    commands.add_option('--print-rdf', action="store_true", default=False,
      help="print ending model state")
    commands.add_option('--update', action="store_true", default=False,
      help="Query remote data sources and update our database")
    #commands.add_option('--update-ucsc-status', default=None,
    #  help="download status from ucsc, requires filename for extra rules")
    #commands.add_option('--update-ddfs', action="store_true", default=False,
    #  help="download ddf information for known submission")
    #commands.add_option('--update-library', default=None,
    #  help="download library info from htsw, "\
    #       "requires filename for extra rules")
    parser.add_option_group(commands)

    queries = OptionGroup(parser, "Queries")
    queries.add_option('--sparql', default=None,
      help="execute arbitrary sparql query")
    queries.add_option('--find-submission-with-no-library', default=False,
      action="store_true",
      help="find submissions with no library ID")
    parser.add_option_group(queries)

    options = OptionGroup(parser, "Options")
    options.add_option("--rdf-parser-name", default="turtle",
      help="set rdf file parser type")
    options.add_option("-v", "--verbose", action="store_true", default=False)
    options.add_option("--debug", action="store_true", default=False)
    parser.add_option_group(options)

    api.add_auth_options(parser)

    return parser


def load_my_submissions(model, limit=None, cookie=None):
    """Parse all the submissions from UCSC into model
    It will look at the global USER_URL to figure out who to scrape
    cookie contains the session cookie, if none, will attempt to login
    """
    if cookie is None:
        cookie = login()

    tree = get_url_as_tree(USER_URL, 'GET', cookie)
    table_rows = tree.xpath('//table[@id="projects"]/tr')
    # first record is header
    name_n = submissionOntology['name']
    species_n = submissionOntology['species']
    library_urn = submissionOntology['library_urn']

    # skip header
    for row in table_rows[1:]:
        cell = row.xpath('td')
        if cell is not None and len(cell) > 1:
            submission_id = str(cell[0].text_content())
            if limit is None or submission_id in limit:
                subUrn = RDF.Uri(submission_view_url(submission_id))

                add_stmt(model,
                         subUrn,
                         TYPE_N,
                         submissionOntology['Submission'])
                add_stmt(model,
                         subUrn,
                         DCC_NS['subId'],
                         RDF.Node(submission_id))

                name = str(cell[4].text_content())
                add_stmt(model, subUrn, name_n, name)

                species = str(cell[2].text_content())
                if species is not None:
                    add_stmt(model, subUrn, species_n, species)

                library_id = get_library_id(name)
                if library_id is not None:
                    add_submission_to_library_urn(model,
                                                  subUrn,
                                                  library_urn,
                                                  library_id)
                else:
                    errmsg = 'Unable to find library id in {0} for {1}'
                    LOGGER.warn(errmsg.format(name, str(subUrn)))

                add_submission_creation_date(model, subUrn, cookie)

                # grab changing atttributes
                status = str(cell[6].text_content()).strip()
                last_mod_datetime = get_date_contents(cell[8])
                last_mod = last_mod_datetime.isoformat()

                update_submission_detail(model, subUrn, status, last_mod,
                                         cookie=cookie)

                LOGGER.info("Processed {0}".format(subUrn))


def add_submission_to_library_urn(model, submissionUrn, predicate, library_id):
    """Add a link from a UCSC submission to woldlab library if needed
    """
    libraryUrn = LIBRARY_NS[library_id + '/']
    query = RDF.Statement(submissionUrn, predicate, libraryUrn)
    if not model.contains_statement(query):
        link = RDF.Statement(submissionUrn, predicate, libraryUrn)
        LOGGER.info("Adding Sub -> Lib link: {0}".format(link))
        model.add_statement(link)
    else:
        LOGGER.debug("Found: {0}".format(str(query)))


def find_submissions_with_no_library(model):
    missing_lib_query_text = """
PREFIX submissionOntology:<{submissionOntology}>

SELECT
 ?subid ?name
WHERE {{
  ?subid submissionOntology:name ?name
  OPTIONAL {{ ?subid submissionOntology:library_urn ?libid }}
  FILTER  (!bound(?libid))
}}""".format(submissionOntology=submissionOntology[''].uri)
    missing_lib_query = RDF.SPARQLQuery(missing_lib_query_text)

    results = missing_lib_query.execute(model)
    for row in results:
        subid = row['subid']
        name = row['name']
        print "# {0}".format(name)
        print "<{0}>".format(subid.uri)
        print "  encodeSubmit:library_urn "\
              "<http://jumpgate.caltech.edu/library/> ."
        print ""


def add_submission_creation_date(model, subUrn, cookie):
    # in theory the submission page might have more information on it.
    creation_dates = get_creation_dates(model, subUrn)
    if len(creation_dates) == 0:
        LOGGER.info("Getting creation date for: {0}".format(str(subUrn)))
        submissionTree = get_url_as_tree(str(subUrn), 'GET', cookie)
        parse_submission_page(model, cells, subUrn)
    else:
        LOGGER.debug("Found creation date for: {0}".format(str(subUrn)))

def get_creation_dates(model, subUrn):
    query = RDF.Statement(subUrn, CREATION_DATE, None)
    creation_dates = list(model.find_statements(query))
    return creation_dates

def parse_submission_page(model, submissionTree, subUrn):
    cells = submissionTree.findall('.//td')
    dateTimeType = xsdNS['dateTime']
    created_label = [x for x in cells
                     if x.text_content().startswith('Created')]
    if len(created_label) == 1:
        created_date = get_date_contents(created_label[0].getnext())
        created_date_node = RDF.Node(literal=created_date.isoformat(),
                                     datatype=dateTimeType.uri)
        add_stmt(model, subUrn, CREATION_DATE, created_date_node)
    else:
        msg = 'Unable to find creation date for {0}'.format(str(subUrn))
        LOGGER.warn(msg)
        raise Warning(msg)


def update_submission_detail(model, subUrn, status, recent_update, cookie):
    HasStatusN = submissionOntology['has_status']
    StatusN = submissionOntology['status']
    LastModifyN = submissionOntology['last_modify_date']

    status_nodes_query = RDF.Statement(subUrn, HasStatusN, None)
    status_nodes = list(model.find_statements(status_nodes_query))

    if len(status_nodes) == 0:
        # has no status node, add one
        LOGGER.info("Adding status node to {0}".format(subUrn))
        status_node = create_status_node(subUrn, recent_update)
        add_stmt(model, subUrn, HasStatusN, status_node)
        add_stmt(model, status_node, rdfNS['type'], StatusN)
        add_stmt(model, status_node, StatusN, status)
        add_stmt(model, status_node, LastModifyN, recent_update)
        update_ddf(model, subUrn, status_node, cookie=cookie)
        update_daf(model, subUrn, status_node, cookie=cookie)
    else:
        LOGGER.info("Found {0} status blanks".format(len(status_nodes)))
        for status_statement in status_nodes:
            status_node = status_statement.object
            last_modified_query = RDF.Statement(status_node,
                                                LastModifyN,
                                                None)
            last_mod_nodes = model.find_statements(last_modified_query)
            for last_mod_statement in last_mod_nodes:
                last_mod_date = str(last_mod_statement.object)
                if recent_update == str(last_mod_date):
                    update_ddf(model, subUrn, status_node, cookie=cookie)
                    update_daf(model, subUrn, status_node, cookie=cookie)
                    break


def update_daf(model, submission_url, status_node, cookie):
    download_daf_uri = str(submission_url).replace('show', 'download_daf')
    daf_uri = RDF.Uri(download_daf_uri)

    status_is_daf = RDF.Statement(status_node, TYPE_N, dafTermOntology[''])
    if not model.contains_statement(status_is_daf):
        LOGGER.info('Adding daf to {0}, {1}'.format(submission_url,
                                                     status_node))
        daf_text = get_url_as_text(download_daf_uri, 'GET', cookie)
        daf_hash = hashlib.md5(daf_text).hexdigest()
        daf_hash_stmt = RDF.Statement(status_node,
                                      dafTermOntology['md5sum'],
                                      daf_hash)
        model.add_statement(daf_hash_stmt)
        daf.fromstring_into_model(model, status_node, daf_text)


def update_ddf(model, subUrn, statusNode, cookie):
    download_ddf_url = str(subUrn).replace('show', 'download_ddf')
    ddfUrn = RDF.Uri(download_ddf_url)

    status_is_ddf = RDF.Statement(statusNode, TYPE_N, DCC_NS[''])
    if not model.contains_statement(status_is_ddf):
        LOGGER.info('Adding ddf to {0}, {1}'.format(subUrn, statusNode))
        ddf_text = get_url_as_text(download_ddf_url, 'GET', cookie)
        add_ddf_statements(model, statusNode, ddf_text)
        model.add_statement(status_is_ddf)


def add_ddf_statements(model, statusNode, ddf_string):
    """Convert a ddf text file into RDF Statements
    """
    ddf_lines = ddf_string.split('\n')
    # first line is header
    header = ddf_lines[0].split()
    attributes = [DCC_NS[x] for x in header]

    for ddf_line in ddf_lines[1:]:
        ddf_line = ddf_line.strip()
        if len(ddf_line) == 0:
            continue
        if ddf_line.startswith("#"):
            continue

        ddf_record = ddf_line.split('\t')
        files = ddf_record[0].split(',')
        file_attributes = ddf_record[1:]

        for f in files:
            fileNode = RDF.Node()
            add_stmt(model,
                     statusNode,
                     submissionOntology['has_file'],
                     fileNode)
            add_stmt(model, fileNode, rdfNS['type'], DCC_NS['file'])
            add_stmt(model, fileNode, DCC_NS['filename'], f)

            for predicate, object in zip(attributes[1:], file_attributes):
                add_stmt(model, fileNode, predicate, object)


def load_encode_libraries(model, htswapi):
    """Get libraries associated with encode.
    """
    encodeFilters = ["/library/?affiliations__id__exact=44",
                     "/library/?affiliations__id__exact=80",
                    ]

    encodeUrls = [os.path.join(htswapi.root_url + u) for u in encodeFilters]
    rdfaParser = RDF.Parser(name='rdfa')
    for encodeUrl in encodeUrls:
        LOGGER.info("Scanning library url {0}".format(encodeUrl))
        rdfaParser.parse_into_model(model, encodeUrl)
        query = RDF.Statement(None, libraryOntology['library_id'], None)
        libraries = model.find_statements(query)
        for statement in libraries:
            libraryUrn = statement.subject
            LOGGER.info("Scanning {0}".format(str(libraryUrn)))
            load_library_detail(model, libraryUrn)


def load_encodedcc_files(model, base_url):
    if base_url[-1] != '/':
        base_url += '/'

    file_index = ucsc.get_ucsc_file_index(base_url)
    for filename, attributes in file_index.items():
        s = RDF.Node(RDF.Uri(base_url + filename))
        for name, value in attributes.items():
            p = RDF.Node(DCC_NS[name])
            o = RDF.Node(value)
            model.add_statement(RDF.Statement(s,p,o))

def load_library_detail(model, libraryUrn):
    """Grab detail information from library page
    """
    rdfaParser = RDF.Parser(name='rdfa')
    query = RDF.Statement(libraryUrn, libraryOntology['date'], None)
    results = list(model.find_statements(query))
    log_message = "Found {0} statements for {1}"
    LOGGER.debug(log_message.format(len(results), libraryUrn))
    if len(results) == 0:
        LOGGER.info("Loading {0}".format(str(libraryUrn)))
        rdfaParser.parse_into_model(model, libraryUrn.uri)
    elif len(results) == 1:
        pass  # Assuming that a loaded dataset has one record
    else:
        LOGGER.warning("Many dates for {0}".format(libraryUrn))


def get_library_id(name):
    """Guess library ID from library name

    >>> get_library_id('2x75-GM12892-rep1-11039 20110217 elements')
    '11039'
    >>> get_library_id('10150 C2C12-24h-myogenin-2PCR-Rep1.32mers')
    '10150'
    """
    match = re.search(r"([ -]|^)(?P<id>([\d]{5})|(SL[\d]{4}))", name)
    library_id = None
    if match is not None:
        library_id = match.group('id')
    return library_id


def get_contents(element):
    """Return contents or none.
    """
    if len(element.contents) == 0:
        return None

    a = element.find('a')
    if a is not None:
        return a.contents[0].encode(CHARSET)

    return element.contents[0].encode(CHARSET)


def create_status_node(submission_uri, timestamp):
    submission_uri = daf.submission_uri_to_string(submission_uri)
    if submission_uri[-1] != '/':
        sumbission_uri += '/'
    status_uri = submission_uri + timestamp
    return RDF.Node(RDF.Uri(status_uri))


def get_date_contents(element):
    data = element.text_content()
    if data:
        return datetime.strptime(data, "%Y-%m-%d %H:%M")
    else:
        return None


def add_stmt(model, subject, predicate, rdf_object):
    """Convienence create RDF Statement and add to a model
    """
    return model.add_statement(
        RDF.Statement(subject, predicate, rdf_object))


def login(cookie=None):
    """Login if we don't have a cookie
    """
    if cookie is not None:
        return cookie

    keys = keyring.get_keyring()
    password = keys.get_password(LOGIN_URL, USERNAME)
    credentials = {'login': USERNAME,
                   'password': password}
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    http = httplib2.Http()
    response, content = http.request(LOGIN_URL,
                                     'POST',
                                     headers=headers,
                                     body=urllib.urlencode(credentials))
    LOGGER.debug("Login to {0}, status {1}".format(LOGIN_URL,
                                                    response['status']))

    cookie = response.get('set-cookie', None)
    if cookie is None:
        raise RuntimeError("Wasn't able to log into: {0}".format(LOGIN_URL))
    return cookie


def get_url_as_tree(url, method, cookie=None):
    http = httplib2.Http()
    headers = {}
    if cookie is not None:
        headers['Cookie'] = cookie
    response, content = http.request(url, method, headers=headers)
    if response['status'] == '200':
        tree = fromstring(content, base_url=url)
        return tree
    else:
        msg = "error accessing {0}, status {1}"
        msg = msg.format(url, response['status'])
        e = httplib2.HttpLib2ErrorWithResponse(msg, response, content)


def get_url_as_text(url, method, cookie=None):
    http = httplib2.Http()
    headers = {}
    if cookie is not None:
        headers['Cookie'] = cookie
    response, content = http.request(url, method, headers=headers)
    if response['status'] == '200':
        return content
    else:
        msg = "error accessing {0}, status {1}"
        msg = msg.format(url, response['status'])
        e = httplib2.HttpLib2ErrorWithResponse(msg, response, content)

################
#  old stuff
SUBMISSIONS_LACKING_LIBID = [
    ('1x75-Directional-HeLa-Rep1',    '11208'),
    ('1x75-Directional-HeLa-Rep2',    '11207'),
    ('1x75-Directional-HepG2-Rep1',   '11210'),
    ('1x75-Directional-HepG2-Rep2',   '11209'),
    ('1x75-Directional-H1-hESC-Rep1', '10947'),
    ('1x75-Directional-H1-hESC-Rep2', '11009'),
    ('1x75-Directional-HUVEC-Rep1',   '11206'),
    ('1x75-Directional-HUVEC-Rep2',   '11205'),
    ('1x75-Directional-K562-Rep1',    '11008'),
    ('1x75-Directional-K562-Rep2',    '11007'),
    ('1x75-Directional-NHEK-Rep1',    '11204'),
    ('1x75-Directional-GM12878-Rep1', '11011'),
    ('1x75-Directional-GM12878-Rep2', '11010'),
    ]


def select_by_library_id(submission_list):
    subl = [(x.library_id, x) for x in submission_list if x.library_id]
    libraries = {}
    for lib_id, subobj in subl:
        libraries.setdefault(lib_id, []).append(subobj)

    for submission in libraries.values():
        submission.sort(key=attrgetter('date'), reverse=True)

    return libraries


def library_to_freeze(selected_libraries):
    freezes = ['2010-Jan', '2010-Jul', '2011-Jan']
    lib_ids = sorted(selected_libraries.keys())
    report = ['<html><table border="1">']
    report = ["""<html>
<head>
<style type="text/css">
 td {border-width:0 0 1px 1px; border-style:solid;}
</style>
</head>
<body>
<table>
"""]
    report.append('<thead>')
    report.append('<tr><td>Library ID</td><td>Name</td>')
    for f in freezes:
        report.append('<td>{0}</td>'.format(f))
    report.append('</tr>')
    report.append('</thead>')
    report.append('<tbody>')
    for lib_id in lib_ids:
        report.append('<tr>')
        lib_url = LIBRARY_NS[lib_id].uri
        report.append('<td><a href="{0}">{1}</a></td>'.format(lib_url, lib_id))
        submissions = selected_libraries[lib_id]
        report.append('<td>{0}</td>'.format(submissions[0].name))
        batched = {}
        for sub in submissions:
            date = date_to_freeze(sub.date)
            batched.setdefault(date, []).append(sub)
        for d in freezes:
            report.append('<td>')
            for s in batched.get(d, []):
                show_url = submission_view_url(s.subid)
                subid = '<a href="{0}">{1}</a>'.format(show_url, s.subid)
                report.append("{0}:{1}".format(subid, s.status))
            report.append('</td>')
        else:
            report.append('<td></td>')
        report.append("</tr>")
    report.append('</tbody>')
    report.append("</table></html>")
    return "\n".join(report)


def date_to_freeze(d):
    freezes = [(datetime(2010, 1, 30), '2010-Jan'),
               (datetime(2010, 7, 30), '2010-Jul'),
               (datetime(2011, 1, 30), '2011-Jan'),
               ]
    for end, name in freezes:
        if d < end:
            return name
    else:
        return None

if __name__ == "__main__":
    main()
