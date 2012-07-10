#!/usr/bin/env python
"""More direct synthetic test cases for the eland output file processing
"""
import os
from StringIO import StringIO
import shutil
import tempfile
import unittest

from htsworkflow.pipelines.runfolder import ElementTree
from htsworkflow.pipelines import genomemap

class TestGenomeMap(unittest.TestCase):
    def test_genomesizes_xml(self):
        xml = ElementTree.fromstring("""<sequenceSizes>
        <chromosome fileName="chr2.fa" contigName="chr2" totalBases="181748087"/>
        <chromosome fileName="chr1.fa" contigName="chr1" totalBases="197195432"/>
 </sequenceSizes>
""")
        g = genomemap.GenomeMap()
        g.build_map_from_element(xml)

        self.assertTrue('chr1.fa' in g)
        self.assertEqual(g['chr1.fa'], 'mm9/chr1.fa')

    def test_simulated_genome_dir(self):
        vlds = [genomemap.vldInfo('chr1.fa.vld', False),
                genomemap.vldInfo('chr2.fa.vld', False),
                genomemap.vldInfo('chr3.fa.vld', False),
                genomemap.vldInfo('Lambda.fa.vld', True),]

        g = genomemap.GenomeMap()
        g.build_map_from_dir('mm9', vlds)

        self.assertTrue('chr1.fa' in g)
        self.assertEqual(len(g), 4)
        self.assertEqual(g['chr1.fa'], 'mm9/chr1.fa')
        self.assertEqual(g['Lambda.fa'], 'Lambda.fa')

    def test_genome_dir(self):
        g = genomemap.GenomeMap()
        names = ['chr1', 'chr2', 'chr3']
        tempdir = None
        try:
            tempdir = tempfile.mkdtemp(prefix='tmp_mm9')
            for base in names:
                name = os.path.join(tempdir, base + '.fa.vld')
                stream = open(name, 'w')
                stream.write(name)
                stream.close()
            g.scan_genome_dir(tempdir)
        finally:
            if tempdir is not None:
                shutil.rmtree(tempdir)

        temppath, tempgenome = os.path.split(tempdir)
        self.assertTrue('chr1.fa' in g)
        self.assertEqual(len(g), 3)
        self.assertEqual(g['chr1.fa'], '{0}/chr1.fa'.format(tempgenome))
if __name__ == "__main__":
    unittest.main()
