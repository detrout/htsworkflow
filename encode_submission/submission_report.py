import RDF
import jinja2

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

from encode_find import DBDIR

def main():
    model = get_model('encode', DBDIR)
    what_have_we_done(model)

SUBMISSION_QUERY = """
PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
PREFIX ucscSubmission:<http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#>
PREFIX libraryOntology:<http://jumpgate.caltech.edu/wiki/LibraryOntology#>
PREFIX daf: <http://jumpgate.caltech.edu/wiki/UcscDaf#>
PREFIX ddf: <http://encodesubmit.ucsc.edu/pipeline/download_ddf#>

SELECT distinct ?library_urn ?library_name ?assembly ?submission ?submission_status ?date
WHERE {
  ?submission ucscSubmission:library_urn ?library_urn ;
              ucscSubmission:has_status ?status ;
              libraryOntology:date ?date .
  ?status daf:assembly ?assembly ;
          ucscSubmission:status ?submission_status .
  OPTIONAL { ?library_urn libraryOntology:name ?library_name . }
  FILTER(!regex(?submission_status, "revoked", "i"))
  FILTER(regex(?assembly, "mm9", "i"))
  #FILTER(!BOUND(?library_name))
}
ORDER BY ?library_urn ?submission
"""

SUBMISSION_TEMPLATE = """
<html>
<head>
<style type="text/css">
table { border-width: 0 0 1px 1px; border-style: solid; }
th,td { border-width: 1px 1px 0 0; border-style: solid; margin: 0;}
</style>
</head>
<body>
<table>
<thead>
  <tr>
  <td>Library ID</td><td>Submission ID</td><td>Last Updated</td><td>Status</td>
  <td>Library Name</td>
  </tr>
</thead>
<tbody>
{% for record in submissions %}
  <tr>
    <td><a href="{{record.library_urn}}">{{ record.library_urn | trim_rdf}}</a></td>
    <td><a href="{{record.submission}}">{{record.submission|trim_rdf}}</a></td>
    <td>{{ record.date|timestamp_to_date }}</td>
    <td>{{ record.submission_status }}</td>
    <td>{{ record.library_name }}</td>
  </tr>
{% endfor %}
</tbody>
</table>
</body>
</html>
"""

def what_have_we_done(model):
    compiled_query = RDF.SPARQLQuery(SUBMISSION_QUERY)
    submissions = compiled_query.execute(model)
    environment = jinja2.Environment()
    environment.filters['trim_rdf'] = trim_rdf
    environment.filters['timestamp_to_date'] = timestamp_to_date
    template = environment.from_string(SUBMISSION_TEMPLATE)
    print template.render(submissions = submissions)

def trim_rdf(value):
    if value is None:
        return
    value = str(value)
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
