"""Code shared between test cases.
"""
import RDF
import logging
import os
import tempfile
import htsworkflow.util.rdfhelp

S1_NAME = '1000-sample'
S2_NAME = '2000-sample'
SCOMBINED_NAME = 'directory'

S1_FILES = [
    os.path.join(S1_NAME, 'file1_l8_r1.fastq'),
    os.path.join(S1_NAME, 'file1_l8_r2.fastq'),
]

S2_FILES = [
    os.path.join(S2_NAME, 'file1.bam'),
    os.path.join(S2_NAME, 'file1_l5.fastq'),
]

SCOMBINED_FILES = [
    os.path.join(SCOMBINED_NAME, 's1_file1.bam'),
    os.path.join(SCOMBINED_NAME, 's1_l5.fastq'),
    os.path.join(SCOMBINED_NAME, 's2_file1.bam'),
    os.path.join(SCOMBINED_NAME, 's2_l4.read1.fastq'),
    os.path.join(SCOMBINED_NAME, 's2_l4.read2.fastq'),
]

TURTLE_PREFIX = htsworkflow.util.rdfhelp.get_turtle_header()

S1_TURTLE = TURTLE_PREFIX + """
<http://localhost/library/1000/>
  htswlib:cell_line "Cell1000" ;
  htswlib:library_id "1000" ;
  htswlib:library_type "Single End (non-multiplexed)" ;
  htswlib:replicate "1" ;
  htswlib:has_lane <http://localhost/lane/1> ;
  a htswlib:IlluminaLibrary .

<http://localhost/lane/1>
  htswlib:flowcell <http://localhost/flowcel/1234ABXXX> ;
  htswlib:lane_number "1"@en;
  a htswlib:IlluminaLane .
"""

S2_TURTLE = TURTLE_PREFIX + """
<http://localhost/library/2000/>
  htswlib:cell_line "Cell2000" ;
  htswlib:library_id "2000" ;
  htswlib:library_type "Paired End (non-multiplexed)" ;
  htswlib:replicate "2" ;
  htswlib:has_lane <http://localhost/lane/2> ;
  a htswlib:Library .

<http://localhost/lane/2>
  htswlib:flowcell <http://localhost/flowcel/1234ABXXX> ;
  htswlib:lane_number "2"@en ;
  a htswlib:IlluminaLane .
"""

class MockAddDetails(object):
    def __init__(self, model, turtle=None):
        self.model = model
        if turtle:
            self.add_turtle(turtle)

    def add_turtle(self, turtle):
        parser = RDF.Parser('turtle')
        parser.parse_string_into_model(self.model, turtle, "http://localhost")

    def __call__(self, libNode):
        q = RDF.Statement(libNode, None, None)
        found = False
        for s in self.model.find_statements(q):
            found = True
            break
        assert found

def generate_sample_results_tree(obj, prefix):
    obj.tempdir = tempfile.mkdtemp(prefix=prefix)
    obj.sourcedir = os.path.join(obj.tempdir, 'source')
    os.mkdir(obj.sourcedir)
    obj.resultdir = os.path.join(obj.tempdir, 'results')
    os.mkdir(obj.resultdir)

    for d in [os.path.join(obj.sourcedir, S1_NAME),
              os.path.join(obj.sourcedir, S2_NAME),
              ]:
        logging.debug("Creating: %s", d)
        os.mkdir(d)

    tomake = []
    tomake.extend(S1_FILES)
    tomake.extend(S2_FILES)
    for f in tomake:
        target = os.path.join(obj.sourcedir, f)
        logging.debug("Creating: %s", target)
        stream = open(target, 'w')
        stream.write(f)
        stream.close()

