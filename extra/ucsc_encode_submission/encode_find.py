#!/usr/bin/env python

from BeautifulSoup import BeautifulSoup
from datetime import datetime
import httplib2
from operator import attrgetter
from optparse import OptionParser, OptionGroup
# python keyring
import keyring
import logging
import os
import re
# redland rdf lib
import RDF 
import sys
import urllib

from htsworkflow.util import api

logger = logging.getLogger("encode_find")

libraryNS = RDF.NS("http://jumpgate.caltech.edu/library/")
submissionNS = RDF.NS("http://encodesubmit.ucsc.edu/pipeline/show/")
submitOntologyNS = RDF.NS("http://jumpgate.caltech.edu/wiki/UCSCSubmissionOntology#")
ddfNS = RDF.NS("http://encodesubmit.ucsc.edu/pipeline/download_ddf#")
libOntNS = RDF.NS("http://jumpgate.caltech.edu/wiki/LibraryOntology#")

dublinCoreNS = RDF.NS("http://purl.org/dc/elements/1.1/")
rdfNS = RDF.NS("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfsNS= RDF.NS("http://www.w3.org/2000/01/rdf-schema#")
xsdNS = RDF.NS("http://www.w3.org/2001/XMLSchema#")

LOGIN_URL = 'http://encodesubmit.ucsc.edu/account/login'
USER_URL = 'http://encodesubmit.ucsc.edu/pipeline/show_user'

USERNAME = 'detrout'
CHARSET = 'utf-8'

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    if opts.verbose:
        logging.basicConfig(level=logging.INFO)

    htsw_authdata = api.make_auth_from_opts(opts, parser)
    htswapi = api.HtswApi(opts.host, htsw_authdata)
    
    cookie = None
    model = get_model(opts.load_model)
    
    if opts.load_rdf is not None:
        load_into_model(model, opts.rdf_parser_name, opts.load_rdf)
        
    if opts.update:
        cookie = login(cookie=cookie)
        load_my_submissions(model, cookie=cookie)
        load_encode_libraries(model, htswapi)

    if opts.sparql is not None:
        sparql_query(model, opts.sparql)

    if opts.find_submission_with_no_library:
        missing = find_submissions_with_no_library(model)
                
    if opts.print_rdf:
        serializer = RDF.Serializer(name=opts.rdf_parser_name)
        print serializer.serialize_model_to_string(model)


def make_parser():
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
    #  help="download library info from htsw, requires filename for extra rules")
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
    parser.add_option_group(options)
    
    api.add_auth_options(parser)

    return parser

def get_model(model_name=None):
    if model_name is None:
        storage = RDF.MemoryStorage()
    else:
        storage = RDF.HashStorage(model_name, options="hash-type='bdb',dir='/tmp'")
    model = RDF.Model(storage)
    return model
        
def load_my_submissions(model, cookie=None):
    if cookie is None:
        cookie = login()
        
    soup = get_url_as_soup(USER_URL, 'GET', cookie)
    p = soup.find('table', attrs={'id':'projects'})
    tr = p.findNext('tr')
    # first record is header
    tr = tr.findNext()
    TypeN = rdfsNS['type']
    NameN = submitOntologyNS['name']
    SpeciesN = submitOntologyNS['species']
    LibraryURN = submitOntologyNS['library_urn']

    while tr is not None:
        td = tr.findAll('td')
        if td is not None and len(td) > 1:
            subUrnText = td[0].contents[0].contents[0].encode(CHARSET)
            subUrn = submissionNS[subUrnText]

            add_stmt(model, subUrn, TypeN, submitOntologyNS['Submission'])
                
            name = get_contents(td[4])
            add_stmt(model, subUrn, NameN, name)
                
            species = get_contents(td[2])
            if species is not None:
                add_stmt(model, subUrn, SpeciesN, species)

            library_id = get_library_id(name)
            if library_id is not None:
                add_submission_to_library_urn(model,
                                              subUrn,
                                              LibraryURN,
                                              library_id)

            add_submission_creation_date(model, subUrn, cookie)

            # grab changing atttributes
            status = get_contents(td[6]).strip()
            last_mod_datetime = get_date_contents(td[8])
            last_mod = last_mod_datetime.isoformat()

            update_submission_detail(model, subUrn, status, last_mod, cookie=cookie)

            logging.info("Processed {0}".format( subUrn))
            
        tr = tr.findNext('tr')


def add_submission_to_library_urn(model, submissionUrn, predicate, library_id):
    """Add a link from a UCSC submission to woldlab library if needed
    """
    libraryUrn = libraryNS[library_id]
    query = RDF.Statement(submissionUrn, predicate, libraryUrn)
    if not model.contains_statement(query):
        link = RDF.Statement(submissionUrn, predicate, libraryNS[library_id])
        logger.info("Adding Sub -> Lib link: {0}".format(link))
        model.add_statement(link)
    else:
        logger.debug("Found: {0}".format(str(query)))

    
def find_submissions_with_no_library(model):
    missing_lib_query = RDF.SPARQLQuery("""
PREFIX submissionOntology:<{submissionOntology}>

SELECT 
 ?subid ?name
WHERE {{
  ?subid submissionOntology:name ?name
  OPTIONAL {{ ?subid submissionOntology:library_urn ?libid }}
  FILTER  (!bound(?libid))
}}""".format(submissionOntology=submitOntologyNS[''].uri)
)    

    results = missing_lib_query.execute(model)
    for row in results:
        subid = row['subid']
        name = row['name']
        print "# {0}".format(name)
        print "<{0}>".format(subid.uri)
        print "  encodeSubmit:library_urn <http://jumpgate.caltech.edu/library/> ."
        print ""
    

def add_submission_creation_date(model, subUrn, cookie):
    # in theory the submission page might have more information on it.
    creationDateN = libOntNS['date']
    dateTimeType = xsdNS['dateTime']
    query = RDF.Statement(subUrn, creationDateN, None)
    creation_dates = list(model.find_statements(query))
    if len(creation_dates) == 0:
        logger.info("Getting creation date for: {0}".format(str(subUrn)))
        soup = get_url_as_soup(str(subUrn.uri), 'GET', cookie)
        created_label = soup.find(text="Created: ")
        if created_label:
            created_date = get_date_contents(created_label.next)
            created_date_node = RDF.Node(literal=created_date.isoformat(),
                                         datatype=dateTimeType.uri)
            add_stmt(model, subUrn, creationDateN, created_date_node)
    else:
        logger.debug("Found creation date for: {0}".format(str(subUrn)))

def update_submission_detail(model, subUrn, status, recent_update, cookie):
    HasStatusN = submitOntologyNS['has_status']
    StatusN = submitOntologyNS['status']
    LastModifyN = submitOntologyNS['last_modify_date']

    status_nodes_query = RDF.Statement(subUrn, HasStatusN, None)
    status_nodes = list(model.find_statements(status_nodes_query))

    if len(status_nodes) == 0:
        # has no status node, add one
        logging.info("Adding status node to {0}".format(subUrn))
        status_blank = RDF.Node()
        add_stmt(model, subUrn, HasStatusN, status_blank)
        add_stmt(model, status_blank, rdfs['type'], StatusT)
        add_stmt(model, status_blank, StatusN, status)
        add_stmt(model, status_blank, LastModifyN, recent_update)
        update_ddf(model, subUrn, status_blank, cookie=cookie)
    else:
        logging.info("Found {0} status blanks".format(len(status_nodes)))
        for status_statement in status_nodes:
            status_blank = status_statement.object
            last_modified_query = RDF.Statement(status_blank, LastModifyN, None)
            last_mod_nodes = model.find_statements(last_modified_query)
            for last_mod_statement in last_mod_nodes:
                last_mod_date = str(last_mod_statement.object)
                if recent_update == str(last_mod_date):
                    update_ddf(model, subUrn, status_blank, cookie=cookie)
                    break


    
def update_ddf(model, subUrn, statusNode, cookie):
    TypeN = rdfsNS['type']
    
    download_ddf_url = str(subUrn).replace('show', 'download_ddf')
    ddfUrn = RDF.Uri(download_ddf_url)
    
    status_is_ddf = RDF.Statement(statusNode, TypeN, ddfNS['ddf'])
    if not model.contains_statement(status_is_ddf):
        logging.info('Adding ddf to {0}, {1}'.format(subUrn, statusNode))
        ddf_text = get_url_as_text(download_ddf_url, 'GET', cookie)
        add_ddf_statements(model, statusNode, ddf_text)
        model.add_statement(status_is_ddf)


def add_ddf_statements(model, statusNode, ddf_string):
    """Convert a ddf text file into RDF Statements
    """
    ddf_lines = ddf_string.split('\n')
    # first line is header
    header = ddf_lines[0].split()
    attributes = [ ddfNS[x] for x in header ]
    statements = []

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
            add_stmt(model, statusNode, submitOntologyNS['has_file'], fileNode)
            add_stmt(model, fileNode, rdfsNS['type'], ddfNS['file'])
            add_stmt(model, fileNode, ddfNS['filename'], f)

            for predicate, object in zip( attributes[1:], file_attributes):
                add_stmt(model, fileNode, predicate, object)


def load_encode_libraries(model, htswapi):
    """Get libraries associated with encode.
    """
    encodeUrl = os.path.join(htswapi.root_url + "/library/?affiliations__id__exact=44")
    rdfaParser = RDF.Parser(name='rdfa')
    print encodeUrl
    rdfaParser.parse_into_model(model, encodeUrl)
    query = RDF.Statement(None, libOntNS['library_id'], None)
    libraries = model.find_statements(query)
    for statement in libraries:
        libraryUrn = statement.subject
        load_library_detail(model, libraryUrn)


def load_library_detail(model, libraryUrn):
    """Grab detail information from library page
    """
    rdfaParser = RDF.Parser(name='rdfa')
    query = RDF.Statement(libraryUrn, libOntNS['date'], None)
    results = list(model.find_statements(query))
    if len(results) == 0:
        logger.info("Loading {0}".format(str(libraryUrn)))
        rdfaParser.parse_into_model(model, libraryUrn.uri)
    elif len(results) == 1:
        pass # Assuming that a loaded dataset has one record
    else:
        logging.warning("Many dates for {0}".format(libraryUrn))
                        
def get_library_id(name):
    """Guess library ID from library name
    """
    match = re.search(r"[ -](?P<id>([\d]{5})|(SL[\d]{4}))", name)
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
    
    
def get_date_contents(element):
    data = get_contents(element)
    if data:
        return datetime.strptime(data, "%Y-%m-%d %H:%M")
    else:
        return None

def sparql_query(model, query_filename):
    """Execute sparql query from file
    """
    query_body = open(query_filename,'r').read()
    query = RDF.SPARQLQuery(query_body)
    results = query.execute(model)
    for row in results:
        output = []
        for k,v in row.items()[::-1]:
            print "{0}: {1}".format(k,v)
        print 

        
def load_into_model(model, parser_name, filename):
    if not os.path.exists(filename):
        raise IOError("Can't find {0}".format(filename))
    
    data = open(filename, 'r').read()
    rdf_parser = RDF.Parser(name=parser_name)
    ns_uri = submitOntologyNS[''].uri
    rdf_parser.parse_string_into_model(model, data, ns_uri)

def add_stmt(model, subject, predicate, object):
    """Convienence create RDF Statement and add to a model
    """
    return model.add_statement(
        RDF.Statement(subject, predicate, object)
    )

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
    logging.debug("Login to {0}, status {1}".format(LOGIN_URL,
                                                    response['status']))
    
    cookie = response.get('set-cookie', None)
    if cookie is None:
        raise RuntimeError("Wasn't able to log into: {0}".format(LOGIN_URL))
    return cookie

                
def get_url_as_soup(url, method, cookie=None):
    http = httplib2.Http()
    headers = {}
    if cookie is not None:
        headers['Cookie'] = cookie
    response, content = http.request(url, method, headers=headers)
    if response['status'] == '200':
        soup = BeautifulSoup(content,
                             fromEncoding="utf-8", # should read from header
                             convertEntities=BeautifulSoup.HTML_ENTITIES
                             )
        return soup
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
    subl = [ (x.library_id, x) for x in submission_list if x.library_id ]
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
        lib_url = libraryNS[lib_id].uri
        report.append('<td><a href="{0}">{1}</a></td>'.format(lib_url, lib_id))
        submissions = selected_libraries[lib_id]
        report.append('<td>{0}</td>'.format(submissions[0].name))
        batched = {}
        for sub in submissions:
            date = date_to_freeze(sub.date)
            batched.setdefault(date, []).append(sub)
        print lib_id, batched
        for d in freezes:
            report.append('<td>')
            for s in batched.get(d, []):
                show_url = submissionNS[s.subid].uri
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
    freezes = [ (datetime(2010, 1, 30), '2010-Jan'),
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
    
