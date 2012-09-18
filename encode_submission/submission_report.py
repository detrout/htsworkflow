import argparse
import RDF
import jinja2
from pprint import pprint

from htsworkflow.util.rdfhelp import \
     get_model, \
     get_serializer, \
     sparql_query, \
     libraryOntology, \
     load_into_model
from htsworkflow.util.rdfns import *
TYPE_N = rdfNS['type']
CREATION_DATE = libraryOntology['date']

from encode_find import DBDIR

DEFAULT_GENOME='hg19'
DEFAULT_OUTPUT='/tmp/submission_report.html'

def main(cmdline=None):
    parser = make_parser()
    args = parser.parse_args(cmdline)
    model = get_model('encode', DBDIR)
    report = what_have_we_done(model, genome=args.genome)
    with open(DEFAULT_OUTPUT,'w') as stream:
        stream.write(report)

def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--genome', default=DEFAULT_GENOME,
                        help='limit to one genome')
    parser.add_argument('--output', default='/tmp/submission_report.html',
                        help="specify where to write to write report")
    return parser

SUBMISSION_QUERY = """
PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
PREFIX ucscSubmission:<http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#>
PREFIX libraryOntology:<http://jumpgate.caltech.edu/wiki/LibraryOntology#>
PREFIX daf: <http://jumpgate.caltech.edu/wiki/UcscDaf#>
PREFIX ddf: <http://encodesubmit.ucsc.edu/pipeline/download_ddf#>

SELECT distinct ?assembly ?experiment ?library_urn ?library_name ?submission ?submission_status ?submission_name ?date
WHERE {{
  ?submission ucscSubmission:library_urn ?library_urn ;
              ucscSubmission:has_status ?status ;
              ucscSubmission:name ?submission_name ;
              libraryOntology:date ?date .
  ?status daf:assembly ?assembly ;
          ucscSubmission:status ?submission_status .
  OPTIONAL {{ ?library_urn libraryOntology:name ?library_name . }}
  OPTIONAL {{ ?library_urn libraryOntology:experiment_type ?experiment . }}
  FILTER(!regex(?submission_status, "revoked", "i"))
  {assembly_filter}
}}
ORDER BY ?assembly ?experiment ?library_urn ?submission
"""

SUBMISSION_TEMPLATE = '''
<html>
<head>
<style type="text/css">
table { border-width: 0 0 1px 1px; border-style: solid; }
th,td { border-width: 1px 1px 0 0; border-style: solid; margin: 0;}
.library { font-size: 18pt; background-color: #EEF; }
.submission { font-size: 12pt; background-color: #EFE;}
</style>
  <title>Submission report for {{ genome }}</title>
</head>
<body>
<h1>Genome: {{ genome }}</h1>
{% for experiment in libraries %}
  <h2>{{ experiment }}</h2>
  <table>
    <thead>
      <tr class="library">
      <td>Library ID</td>
      <td colspan="3">Library Name</td>
      </tr>
      <tr class="submission">
      <td>Submission ID</td>
      <td>Last Updated</td>
      <td>Status</td>
      <td>Submission name</td>
      </tr>
    </thead>
    <tbody>
      {% for liburn, records in libraries[experiment]|dictsort %}
      <!-- {{ liburn }} -->
      <tr class="library">
        <td>
          <a href="{{libraries[experiment][liburn].0.library_urn}}">
            {{ libraries[experiment][liburn].0.library_urn | trim_rdf}}
          </a>
        </td>
        <td colspan="3">{{ libraries[experiment][liburn].0.library_name }}</td>
      </tr>
      {% for record in records|sort %}
      <tr class="submission">
        <td><a href="{{record.submission}}">{{record.submission|trim_rdf}}</a></td>
        <td>{{ record.date|timestamp_to_date }}</td>
        <td>{{ record.submission_status }}</td>
        <td>{{ record.submission_name }}</td>
      </tr>
      {% endfor %}
    {% endfor %}
    </tbody>
  </table>
{% endfor %}
  </body>
</html>
'''

def what_have_we_done(model, genome):
    assembly_filter = ''
    assembly_filter = 'FILTER(regex(?assembly, "{0}", "i"))'.format(genome)

    query = SUBMISSION_QUERY.format(
        assembly_filter=assembly_filter
    )
    compiled_query = RDF.SPARQLQuery(query)
    submissions = compiled_query.execute(model)
    libraries = group_by_library(submissions)
    environment = jinja2.Environment()
    environment.filters['trim_rdf'] = trim_rdf
    environment.filters['timestamp_to_date'] = timestamp_to_date
    template = environment.from_string(SUBMISSION_TEMPLATE)
    return template.render(libraries=libraries,
                           genome=genome)

def group_by_library(submissions):
    libraries = {}
    for record in submissions:
        urn = str(record['library_urn'].uri)
        experiment = str(record['experiment'])
        libraries.setdefault(experiment, {}).setdefault(urn, []).append(record)
    return libraries

def trim_rdf(value):
    if value is None:
        return
    value = str(value)
    if len(value) == 0:
        return value
    if value[-1] == '/':
        value = value[:-1]
    split_value = value.split('/')
    if len(split_value) == 0:
        return value
    return split_value[-1]

def timestamp_to_date(value):
    datestamp, timestamp = str(value).split('T')
    return datestamp

if __name__ == "__main__":
    main()
