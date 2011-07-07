from contextlib import contextmanager
import os
from StringIO import StringIO
import shutil
import tempfile
import unittest

from htsworkflow.submission import daf
from htsworkflow.util.rdfhelp import \
     dafTermOntology, \
     fromTypedNode, \
     rdfNS, \
     submissionLog, \
     submissionOntology, \
     get_model, \
     get_serializer

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
        daf.add_to_model(model, parsed, name)

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

def load_daf_mapper(name, extra_statements=None):
    """Load test model in
    """
    model = get_model()
    if extra_statements is not None:
        parser = RDF.Parser(name='turtle')
        parser.parse_string_into_model(model, extra_statements,
                                       'http://extra.extra')
        
    test_daf_stream = StringIO(test_daf)
    mapper = daf.DAFMapper(name, daf_file = test_daf_stream, model=model)
    return mapper

def dump_model(model):
    writer = get_serializer()
    turtle =  writer.serialize_model_to_string(model)
    print turtle
    
class TestDAFMapper(unittest.TestCase):
    def test_create_mapper_add_pattern(self):
        name = 'testsub'
        mapper = load_daf_mapper(name)
        pattern = '.bam\Z(?ms)'
        mapper.add_pattern('Signal', pattern)

        s = RDF.Statement(daf.get_view_namespace(name)['Signal'],
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
        extra = '''@prefix dafTerm:<http://jumpgate.caltech.edu/wiki/UcscDaf#> .

<%(submissionLog)s/testfind/view/Signal> dafTerm:filename_re ".*\\\\.bam" .
<%(submissionLog)s/testfind/view/FastqRd1> dafTerm:filename_re ".*_r1\\\\.fastq" .
''' % {'submissionLog': 'http://jumpgate.caltech.edu/wiki/SubmissionsLog'}

        daf_mapper = load_daf_mapper('testfind', extra_statements = extra)

        view = daf_mapper.find_view('filename_r1.fastq')
        self.failUnlessEqual(str(view),
                             str(submissionLog['testfind/view/FastqRd1']))

        #writer = get_serializer()
        #turtle =  writer.serialize_model_to_string(model)
        #print turtle

    def test_find_overlapping_view(self):
        extra = '''@prefix dafTerm:<http://jumpgate.caltech.edu/wiki/UcscDaf#> .

<%(submissionLog)s/testfind/view/fastq> dafTerm:filename_re ".*\\\\.fastq" .
<%(submissionLog)s/testfind/view/FastqRd1> dafTerm:filename_re ".*_r1\\\\.fastq" .
''' % {'submissionLog': 'http://jumpgate.caltech.edu/wiki/SubmissionsLog'}

        daf_mapper = load_daf_mapper('testfind', extra_statements = extra)

        self.failUnlessRaises(daf.ModelException,
                              daf_mapper.find_view,
                              'filename_r1.fastq')

    def test_find_attributes(self):
        lib_id = '11204'
        lib_url = 'http://jumpgate.caltech.edu/library/%s/' %(lib_id)
        extra = '''@prefix dafTerm: <http://jumpgate.caltech.edu/wiki/UcscDaf#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<%(submissionLog)s/testfind/view/Signal> dafTerm:filename_re ".*\\\\.bam" .
<%(submissionLog)s/testfind/view/FastqRd1> dafTerm:filename_re ".*\\\\.fastq" .
<%(libUrl)s> <%(libraryOntology)sgel_cut> "100"^^xsd:decimal . 
''' % {'submissionLog': 'http://jumpgate.caltech.edu/wiki/SubmissionsLog',
       'libraryOntology': 'http://jumpgate.caltech.edu/wiki/LibraryOntology#',
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
                print 'dir', os.listdir(analysis_dir)
                daf_mapper.construct_file_attributes(analysis_dir,
                                                     libNode,
                                                     filename)
            
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

@contextmanager
def mktempdir(prefix='tmp'):
    d = tempfile.mkdtemp(prefix=prefix)
    print "made", d
    yield d
    shutil.rmtree(d)
    print "unmade", d

@contextmanager
def mktempfile(suffix='', prefix='tmp', dir=None):
    fd, pathname = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    yield pathname
    print "made", pathname
    os.close(fd)
    os.unlink(pathname)
    print "unmade", pathname
    
def suite():
    suite = unittest.makeSuite(TestDAF, 'test')
    suite.addTest(unittest.makeSuite(TestDAFMapper, 'test'))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
