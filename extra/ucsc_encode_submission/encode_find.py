#!/usr/bin/env python

from BeautifulSoup import BeautifulSoup
from datetime import datetime
import httplib2
from operator import attrgetter
from optparse import OptionParser
# python keyring
import keyring
import logging
import os
import re
# redland rdf lib
import RDF 
import sys
import urllib

libraryNS = RDF.NS("http://jumpgate.caltech.edu/library/")
submissionNS = RDF.NS("http://encodesubmit.ucsc.edu/pipeline/show/")
submitNS = RDF.NS("http://jumpgate.caltech.edu/wiki/EncodeSubmit#")
dublinCoreNS = RDF.NS("http://purl.org/dc/elements/1.1/")
rdfNS = RDF.NS("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfsNS= RDF.NS("http://www.w3.org/2000/01/rdf-schema#")

LOGIN_URL = 'http://encodesubmit.ucsc.edu/account/login'
USER_URL = 'http://encodesubmit.ucsc.edu/pipeline/show_user'
DETAIL_URL = 'http://encodesubmit.ucsc.edu/pipeline/show/{0}'
LIBRARY_URL = 'http://jumpgate.caltech.edu/library/{0}'
USERNAME = 'detrout'

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    cookie = login()
    if cookie is None:
        print "Failed to login"

    submissions = my_submissions(cookie)
    for s in submissions:
        for t in s.triples():
            print t
            
def make_parser():
    parser = OptionParser()
    return parser


def login():
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
    return cookie

def my_submissions(cookie):
    soup = get_url_as_soup(USER_URL, 'GET', cookie)
    p = soup.find('table', attrs={'id':'projects'})
    tr = p.findNext('tr')
    # first record is header
    tr = tr.findNext()
    submissions = []
    while tr is not None:
        td = tr.findAll('td')
        if td is not None and len(td) > 1:
            subid = td[0].contents[0].contents[0]
            species = get_contents(td[2])
            name = get_contents(td[4])
            status = get_contents(td[6]).strip()
            date = get_date_contents(td[8])
            age = get_contents(td[10])
            submissions.append(
                Submission(subid, species, name, status, date, age, cookie)
            )
        tr = tr.findNext('tr')
    return submissions

def get_contents(element):
    """Return contents or none.
    """
    if len(element.contents) == 0:
        return None

    a = element.find('a')
    if a is not None:
        return a.contents[0]

    return element.contents[0]

def get_date_contents(element):
    data = get_contents(element)
    if data:
        return datetime.strptime(data, "%Y-%m-%d %H:%M")
    else:
        return None

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
    ]

class Submission(object):
    def __init__(self, subid, species, name, status, date, age, cookie=None):
        self.cookie = cookie
        self.subid = subid
        self.species = species
        self.name = name
        self.status = status
        self.date = date
        self.age = age
        self._library_id = None
        self._created_date = None

    def triples(self):
        subNode = submissionNS[self.subid.encode('utf-8')]
        dateNode = self.date.strftime("%Y-%m-%d")
        s = [RDF.Statement(subNode, submitNS['name'],
                           self.name.encode('utf-8')),
             RDF.Statement(subNode, submitNS['status'],
                           self.status.encode('utf-8')),
             RDF.Statement(subNode, submitNS['last_modify_date'], dateNode),
             ]
        if self.species is not None:
            s.append(RDF.Statement(subNode, submitNS['species'],
                                   self.species.encode('utf-8')))
        if self.library_id is not None:
             libId = libraryNS[self.library_id.encode('utf-8')]
             s.append(RDF.Statement(subNode, rdfsNS['seeAlso'], libId))
        
        return s
        

    def _get_library_id(self):
        if self._library_id is None:
            match = re.search(r"[ -](?P<id>([\d]{5})|(SL[\d]{4}))", self.name)
            if match is not None:
                self._library_id = match.group('id')
            else:
                for dir_lib_name, lib_id in SUBMISSIONS_LACKING_LIBID:
                    if dir_lib_name in self.name:
                        self._library_id = lib_id
                        break
            
        return self._library_id
    
    library_id = property(_get_library_id)

    def _get_detail(self):
        detail = DETAIL_URL.format(self.subid)
        soup = get_url_as_soup(detail, 'GET', self.cookie)

        created_label = soup.find(text="Created: ")
        if created_label:
            self._created_date = get_date_contents(created_label.next)
            
    def _get_created_date(self):
        if self._created_date is None:
            self._get_detail()
        return self._created_date
    created_date = property(_get_created_date)
    
    def __unicode__(self):
        return u"{0}\t{1}\t{2}".format(self.subid, self.library_id, self.name)

    def __repr__(self):
        return u"<Submission ({0}) '{1}'>".format(self.subid, self.name)


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
        lib_url = LIBRARY_URL.format(lib_id)
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
                subid = '<a href="http://encodesubmit.ucsc.edu/pipeline/show/{0}">{0}</a>'.format(s.subid)
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

if __name__ == "__main__":
    main()
    
