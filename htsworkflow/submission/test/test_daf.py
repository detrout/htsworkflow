from contextlib import contextmanager
import os
from StringIO import StringIO
import shutil
import tempfile
import unittest

from htsworkflow.submission import daf, results
from htsworkflow.util.rdfhelp import \
     dafTermOntology, \
     fromTypedNode, \
     rdfNS, \
     submissionLog, \
     submissionOntology, \
     get_model, \
     get_serializer

from htsworkflow.submission.test import test_results
import RDF

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


class TestDAF(unittest.TestCase):
    def test_parse(self):

        parsed = daf.fromstring(test_daf)

        self.failUnlessEqual(parsed['assembly'], 'mm9')
        self.failUnlessEqual(parsed['grant'], 'Hardison')
        self.failUnlessEqual(len(parsed['variables']), 6)
        self.failUnlessEqual(len(parsed['views']), 2)
        self.failUnlessEqual(len(parsed['views']['FastqRd1']), 5)
        self.failUnlessEqual(len(parsed['views']['Signal']), 5)
        signal = parsed['views']['Signal']
        self.failUnlessEqual(signal['required'], False)
        self.failUnlessEqual(signal['longLabelPrefix'],
                             'Caltech Histone Signal')


    def test_rdf(self):

        parsed = daf.fromstring(test_daf)
        #mem = RDF.Storage(storage_name='hashes',
        #                  options_string='hash-type="memory"'),
        mem = RDF.MemoryStorage()
        model = RDF.Model(mem)

        name = 'cursub'
        subNS = RDF.NS(str(submissionLog[name].uri))
        daf.add_to_model(model, parsed, submissionLog[name].uri)

        signal_view_node = RDF.Node(subNS['/view/Signal'].uri)

        writer = get_serializer()
        turtle =  writer.serialize_model_to_string(model)

        self.failUnless(str(signal_view_node.uri) in turtle)

        statements = list(model.find_statements(
            RDF.Statement(
                signal_view_node, None, None)))
        self.failUnlessEqual(len(statements), 6)
        name = model.get_target(signal_view_node, dafTermOntology['name'])
        self.failUnlessEqual(fromTypedNode(name), u'Signal')

    def test_get_view_namespace_from_string(self):
        url = "http://jumpgate.caltech.edu/wiki/SubmissionLog/cursub/"
        target = RDF.NS(url + 'view/')
        view_namespace = daf.get_view_namespace(url)
        self.assertEqual(view_namespace[''], target[''])

    def test_get_view_namespace_from_string_no_trailing_slash(self):
        url = "http://jumpgate.caltech.edu/wiki/SubmissionLog/cursub"
        target = RDF.NS(url + '/view/')
        view_namespace = daf.get_view_namespace(url)
        self.assertEqual(view_namespace[''], target[''])

    def test_get_view_namespace_from_uri_node(self):
        url = "http://jumpgate.caltech.edu/wiki/SubmissionLog/cursub/"
        node = RDF.Node(RDF.Uri(url))
        target = RDF.NS(url + 'view/')
        view_namespace = daf.get_view_namespace(node)
        self.assertEqual(view_namespace[''], target[''])


def load_daf_mapper(name, extra_statements=None, ns=None, test_daf=test_daf):
    """Load test model in
    """
    model = get_model()
    if ns is None:
        ns="http://extra"

    if extra_statements is not None:
        parser = RDF.Parser(name='turtle')
        parser.parse_string_into_model(model, extra_statements,
                                       ns)

    test_daf_stream = StringIO(test_daf)
    mapper = daf.UCSCSubmission(name, daf_file = test_daf_stream, model=model)
    return mapper

def dump_model(model):
    writer = get_serializer()
    turtle =  writer.serialize_model_to_string(model)
    print turtle


class TestUCSCSubmission(unittest.TestCase):
    def setUp(self):
        test_results.generate_sample_results_tree(self)

    def tearDown(self):
        # see things created by temp_results.generate_sample_results_tree
        shutil.rmtree(self.tempdir)

    def test_create_mapper_add_pattern(self):
        name = 'testsub'
        mapper = load_daf_mapper(name)
        pattern = '.bam\Z(?ms)'
        mapper.add_pattern('Signal', pattern)

        s = RDF.Statement(mapper.viewNS['Signal'],
                          dafTermOntology['filename_re'],
                          None)
        search = list(mapper.model.find_statements(s))
        self.failUnlessEqual(len(search), 1)
        self.failUnlessEqual(str(search[0].subject),
                             str(submissionLog['testsub/view/Signal']))
        self.failUnlessEqual(str(search[0].predicate),
                             str(dafTermOntology['filename_re']))
        #self.failUnlessEqual(search[0].object.literal_value['string'], pattern)


    def test_find_one_view(self):
        name='testfind'
        extra = '''@prefix dafTerm:<http://jumpgate.caltech.edu/wiki/UcscDaf#> .
@prefix thisView: <http://jumpgate.caltech.edu/wiki/SubmissionsLog/{0}/view/> .

thisView:Signal dafTerm:filename_re ".*\\\\.bam" .
thisView:FastqRd1 dafTerm:filename_re ".*_r1\\\\.fastq" .
'''.format(name)
        daf_mapper = load_daf_mapper(name, extra_statements = extra)

        view = daf_mapper.find_view('filename_r1.fastq')

        # dump_model(daf_mapper.model)
        view_root = 'http://jumpgate.caltech.edu/wiki/SubmissionsLog/{0}/view/'
        view_root = view_root.format(name)
        self.failUnlessEqual(str(view.uri),
                             '{0}{1}'.format(view_root,'FastqRd1'))

    def test_find_overlapping_view(self):
        name = 'testfind'
        extra = '''@prefix dafTerm:<http://jumpgate.caltech.edu/wiki/UcscDaf#> .
@prefix thisView: <http://jumpgate.caltech.edu/wiki/SubmissionsLog/{0}/view/> .

thisView:fastq dafTerm:filename_re ".*\\\\.fastq" .
thisView:FastqRd1 dafTerm:filename_re ".*_r1\\\\.fastq" .
'''.format(name)
        daf_mapper = load_daf_mapper(name, extra_statements = extra)

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
        libNode = RDF.Node(RDF.Uri(lib_url))
        daf_mapper._add_library_details_to_model(libNode)
        gel_cut = daf_mapper._get_library_attribute(libNode, 'gel_cut')
        # make sure we can override attributes, the value in our
        # server is 500 for this library
        self.failUnlessEqual(gel_cut, 100)

        species = daf_mapper._get_library_attribute(libNode, 'species')
        self.failUnlessEqual(species, "Homo sapiens")

        with mktempdir('analysis') as analysis_dir:
            path, analysis_name = os.path.split(analysis_dir)
            with mktempfile('.bam', dir=analysis_dir) as filename:
                daf_mapper.construct_track_attributes(analysis_dir,
                                                      libNode,
                                                      filename)

        #dump_model(daf_mapper.model)

        sub_root = "http://jumpgate.caltech.edu/wiki/SubmissionsLog/testfind/"
        submission_name = sub_root + analysis_name
        source = daf_mapper.model.get_source(rdfNS['type'], submissionOntology['submission'])
        self.failUnlessEqual(str(source.uri), submission_name)

        view_name = submission_name + '/Signal'
        view = daf_mapper.model.get_target(source, submissionOntology['has_view'])
        self.failUnlessEqual(str(view.uri), view_name)


    def test_library_url(self):
        daf_mapper = load_daf_mapper('urltest')

        self.failUnlessEqual(daf_mapper.library_url,
                             'http://jumpgate.caltech.edu/library/')
        daf_mapper.library_url = 'http://google.com'
        self.failUnlessEqual(daf_mapper.library_url, 'http://google.com' )

    def test_daf_with_replicate(self):
        daf_mapper = load_daf_mapper('test_rep')
        self.failUnlessEqual(daf_mapper.need_replicate(), True)
        self.failUnless('replicate' in daf_mapper.get_daf_variables())

    def test_daf_without_replicate(self):
        daf_mapper = load_daf_mapper('test_rep',test_daf=test_daf_no_rep)
        self.failUnlessEqual(daf_mapper.need_replicate(), False)
        self.failUnless('replicate' not in daf_mapper.get_daf_variables())

    def test_daf_with_extra(self):
        daf_mapper = load_daf_mapper('test_rep',test_daf=test_daf_extra)
        variables = daf_mapper.get_daf_variables()
        self.assertEqual(len(variables), 11)
        self.failUnless('treatment' in variables)
        self.failUnless('controlId' in variables)


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
        self.failUnless(os.path.exists(created_daf))
        stream = open(created_daf,'r')
        daf_body = stream.read()
        stream.close()

        self.failUnlessEqual(test_daf, daf_body)


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
    suite = unittest.makeSuite(TestDAF, 'test')
    suite.addTest(unittest.makeSuite(TestUCSCSubmission, 'test'))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
