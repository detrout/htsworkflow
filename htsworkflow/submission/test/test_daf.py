from contextlib import contextmanager
import logging
import os
from six.moves import StringIO
import shutil
import tempfile
from unittest import TestCase, TestSuite, defaultTestLoader

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

from htsworkflow.submission import daf, results
from htsworkflow.util.rdfns import (
     dafTermOntology,
     submissionLog,
     submissionOntology
)

from htsworkflow.submission.test import test_results

test_daf = """# Lab and general info
grant             Hardison
lab               Caltech-m
dataType          ChipSeq
variables         cell, antibody,sex,age,strain,control
compositeSuffix   CaltechHistone
assembly          mm9
dafVersion        2.0
validationSettings validateFiles.bam:mismatches=2,bamPercent=99.9;validateFiles.fastq:quick=1000

# Track/view definition
view             FastqRd1
longLabelPrefix  Caltech Fastq Read 1
type             fastq
hasReplicates    yes
required         no

view             Signal
longLabelPrefix  Caltech Histone Signal
type             bigWig
hasReplicates    yes
required         no
"""

test_daf_no_rep = """# Lab and general info
grant             Hardison
lab               Caltech-m
dataType          ChipSeq
variables         cell, antibody,sex,age,strain,control
compositeSuffix   CaltechHistone
assembly          mm9
dafVersion        2.0
validationSettings validateFiles.bam:mismatches=2,bamPercent=99.9;validateFiles.fastq:quick=1000

# Track/view definition
view             FastqRd1
longLabelPrefix  Caltech Fastq Read 1
type             fastq
hasReplicates    no
required         no
"""

test_daf_extra = """# Lab and general info
grant             Hardison
lab               Caltech-m
dataType          ChipSeq
variables         cell,antibody,sex,age,strain
extraVariables    controlId,treatment
compositeSuffix   CaltechHistone
assembly          mm9
dafVersion        2.0
validationSettings validateFiles.bam:mismatches=2,bamPercent=99.9;validateFiles.fastq:quick=1000

# Track/view definition
view             FastqRd1
longLabelPrefix  Caltech Fastq Read 1
type             fastq
hasReplicates    no
required         no
"""


class TestDAF(TestCase):
    def test_parse(self):
        parsed = daf.fromstring(test_daf)

        self.assertEqual(parsed['assembly'], 'mm9')
        self.assertEqual(parsed['grant'], 'Hardison')
        self.assertEqual(len(parsed['variables']), 6)
        self.assertEqual(len(parsed['views']), 2)
        self.assertEqual(len(parsed['views']['FastqRd1']), 5)
        self.assertEqual(len(parsed['views']['Signal']), 5)
        signal = parsed['views']['Signal']
        self.assertEqual(signal['required'], False)
        self.assertEqual(signal['longLabelPrefix'],
                             'Caltech Histone Signal')

    def test_rdf(self):

        parsed = daf.fromstring(test_daf)
        model = Graph()

        name = 'cursub'
        subNS = Namespace(str(submissionLog[name]))
        daf.add_to_model(model, parsed, submissionLog[name])

        signal_view_node = subNS['/view/Signal']

        turtle = str(model.serialize(format='turtle'))

        self.assertTrue(str(signal_view_node) in turtle)

        statements = list(model.triples((signal_view_node, None, None)))
        self.assertEqual(len(statements), 6)
        names = list(model.objects(signal_view_node, dafTermOntology['name']))
        self.assertEqual(len(names), 1)
        self.assertEqual(names[0].toPython(), u'Signal')

    def test_get_view_namespace_from_string(self):
        url = "http://jumpgate.caltech.edu/wiki/SubmissionLog/cursub/"
        target = Namespace(url + 'view/')
        view_namespace = daf.get_view_namespace(url)
        self.assertEqual(view_namespace[''], target[''])

    def test_get_view_namespace_from_string_no_trailing_slash(self):
        url = "http://jumpgate.caltech.edu/wiki/SubmissionLog/cursub"
        target = Namespace(url + '/view/')
        view_namespace = daf.get_view_namespace(url)
        self.assertEqual(view_namespace[''], target[''])

    def test_get_view_namespace_from_uri_node(self):
        url = "http://jumpgate.caltech.edu/wiki/SubmissionLog/cursub/"
        node = URIRef(url)
        target = Namespace(url + 'view/')
        view_namespace = daf.get_view_namespace(node)
        self.assertEqual(view_namespace[''], target[''])


def load_daf_mapper(name, extra_statements=None, ns=None, test_daf=test_daf):
    """Load test model in
    """
    model = Graph()
    if ns is None:
        ns = "http://extra"

    if extra_statements is not None:
        model.parse(data=extra_statements, format='turtle', publicID=ns)

    test_daf_stream = StringIO(test_daf)
    mapper = daf.UCSCSubmission(name, daf_file=test_daf_stream, model=model)
    return mapper


class TestUCSCSubmission(TestCase):
    def setUp(self):
        test_results.generate_sample_results_tree(self, 'daf_results')

    def tearDown(self):
        # see things created by temp_results.generate_sample_results_tree
        shutil.rmtree(self.tempdir)

    def test_create_mapper_add_pattern(self):
        name = 'testsub'
        mapper = load_daf_mapper(name)
        pattern = '.bam\Z(?ms)'
        mapper.add_pattern('Signal', pattern)

        s = (mapper.viewNS['Signal'],
             dafTermOntology['filename_re'],
             None)
        search = list(mapper.model.triples(s))
        self.assertEqual(len(search), 1)
        self.assertEqual(str(search[0][0]),
                             str(submissionLog['testsub/view/Signal']))
        self.assertEqual(str(search[0][1]),
                             str(dafTermOntology['filename_re']))
        #self.assertEqual(search[0].object.literal_value['string'], pattern)


    def test_find_one_view(self):
        name='testfind'
        extra = '''@prefix dafTerm:<http://jumpgate.caltech.edu/wiki/UcscDaf#> .
@prefix thisView: <http://jumpgate.caltech.edu/wiki/SubmissionsLog/{0}/view/> .

thisView:Signal dafTerm:filename_re ".*\\\\.bam" .
thisView:FastqRd1 dafTerm:filename_re ".*_r1\\\\.fastq" .
'''.format(name)
        daf_mapper = load_daf_mapper(name, extra_statements=extra)

        view = daf_mapper.find_view('filename_r1.fastq')

        view_root = 'http://jumpgate.caltech.edu/wiki/SubmissionsLog/{0}/view/'
        view_root = view_root.format(name)
        self.assertEqual(str(view),
                             '{0}{1}'.format(view_root, 'FastqRd1'))

    def test_find_overlapping_view(self):
        name = 'testfind'
        extra = '''@prefix dafTerm:<http://jumpgate.caltech.edu/wiki/UcscDaf#> .
@prefix thisView: <http://jumpgate.caltech.edu/wiki/SubmissionsLog/{0}/view/> .

thisView:fastq dafTerm:filename_re ".*\\\\.fastq" .
thisView:FastqRd1 dafTerm:filename_re ".*_r1\\\\.fastq" .
'''.format(name)
        daf_mapper = load_daf_mapper(name, extra_statements=extra)

        self.failUnlessRaises(daf.ModelException,
                              daf_mapper.find_view,
                              'filename_r1.fastq')

    def test_find_attributes(self):
        lib_id = '11204'
        lib_url = 'http://jumpgate.caltech.edu/library/%s/' %(lib_id)
        extra = '''@prefix dafTerm: <http://jumpgate.caltech.edu/wiki/UcscDaf#> .
@prefix submissionOntology: <http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#> .
@prefix thisView: <http://jumpgate.caltech.edu/wiki/SubmissionsLog/testfind/view/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

thisView:Signal dafTerm:filename_re ".*\\\\.bam" ;
      submissionOntology:view_name "Signal" .
thisView:FastqRd1 dafTerm:filename_re ".*\\\\.fastq" ;
        submissionOntology:view_name "FastqRd1" .
<%(libUrl)s> <%(libraryOntology)sgel_cut> "100"^^xsd:decimal .
''' % {'libraryOntology': 'http://jumpgate.caltech.edu/wiki/LibraryOntology#',
       'libUrl': lib_url}

        daf_mapper = load_daf_mapper('testfind', extra)
        libNode = URIRef(lib_url)
        daf_mapper._add_library_details_to_model(libNode)
        gel_cut = daf_mapper._get_library_attribute(libNode, 'gel_cut')
        # make sure we can override attributes, the value in our
        # server is 500 for this library
        self.assertEqual(gel_cut, 100)

        species = daf_mapper._get_library_attribute(libNode, 'species_name')
        self.assertEqual(species, "Homo sapiens")

        with mktempdir('analysis') as analysis_dir:
            path, analysis_name = os.path.split(analysis_dir)
            with mktempfile('.bam', dir=analysis_dir) as filename:
                daf_mapper.construct_track_attributes(analysis_dir,
                                                      libNode,
                                                      filename)

        sub_root = "http://jumpgate.caltech.edu/wiki/SubmissionsLog/testfind/"
        submission_name = sub_root + analysis_name
        sources = list(daf_mapper.model.subjects(RDF['type'], submissionOntology['submission']))
        self.assertEqual(len(sources), 1)
        source = sources[0]
        self.assertEqual(str(source), submission_name)

        view_name = submission_name + '/Signal'
        views = list(daf_mapper.model.objects(source, submissionOntology['has_view']))
        self.assertEqual(len(views), 1)
        self.assertEqual(str(views[0]), view_name)

    def test_library_url(self):
        daf_mapper = load_daf_mapper('urltest')

        self.assertEqual(daf_mapper.library_url,
                             'http://jumpgate.caltech.edu/library/')
        daf_mapper.library_url = 'http://google.com'
        self.assertEqual(daf_mapper.library_url, 'http://google.com')

    def test_daf_with_replicate(self):
        daf_mapper = load_daf_mapper('test_rep')
        self.assertEqual(daf_mapper.need_replicate(), True)
        self.assertTrue('replicate' in daf_mapper.get_daf_variables())

    def test_daf_without_replicate(self):
        daf_mapper = load_daf_mapper('test_rep', test_daf=test_daf_no_rep)
        self.assertEqual(daf_mapper.need_replicate(), False)
        self.assertTrue('replicate' not in daf_mapper.get_daf_variables())

    def test_daf_with_extra(self):
        daf_mapper = load_daf_mapper('test_rep', test_daf=test_daf_extra)
        variables = daf_mapper.get_daf_variables()

        self.assertEqual(len(variables), 11)
        self.assertTrue('treatment' in variables)
        self.assertTrue('controlId' in variables)

    def test_link_daf(self):
        name = 'testsub'
        submission = load_daf_mapper(name, test_daf=test_daf)
        result_map = results.ResultMap()
        result_dir = os.path.join(self.sourcedir,
                                  test_results.S1_NAME)
        result_map['1000'] = result_dir

        submission.link_daf(result_map)

        # make sure daf gets linked
        created_daf = os.path.join(result_dir, name+'.daf')
        self.assertTrue(os.path.exists(created_daf))
        stream = open(created_daf, 'r')
        daf_body = stream.read()
        stream.close()

        self.assertEqual(test_daf, daf_body)


@contextmanager
def mktempdir(prefix='tmp'):
    d = tempfile.mkdtemp(prefix=prefix)
    yield d
    shutil.rmtree(d)


@contextmanager
def mktempfile(suffix='', prefix='tmp', dir=None):
    fd, pathname = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    yield pathname
    os.close(fd)
    os.unlink(pathname)

def suite():
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestDAF))
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestUCSCSubmission))
    return suite

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    from unittest import main
    main(defaultTest='suite')
