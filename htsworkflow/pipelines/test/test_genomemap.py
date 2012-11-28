#!/usr/bin/env python
"""More direct synthetic test cases for the eland output file processing
"""
import os
from StringIO import StringIO
import shutil
import tempfile
from unittest2 import TestCase

from htsworkflow.pipelines.runfolder import ElementTree
from htsworkflow.pipelines import genomemap

MINI_GENOME_XML = '''<sequenceSizes>
        <chromosome fileName="chr2.fa" contigName="chr2" totalBases="181748087"/>
        <chromosome fileName="chr1.fa" contigName="chr1" totalBases="197195432"/>
</sequenceSizes>
'''
class TestGenomeMap(TestCase):
    def test_genomesizes_xml(self):
        xml = ElementTree.fromstring(MINI_GENOME_XML)
        g = genomemap.GenomeMap()
        g.build_map_from_element(xml)

        self.assertTrue('chr1.fa' in g)
        self.assertEqual(g['chr1.fa'], 'mm9/chr1.fa')

    def test_genomesizes_file(self):
        g = genomemap.GenomeMap()
        try:
            tempdir = tempfile.mkdtemp(prefix='tmp_genome')
            name = os.path.join(tempdir, '11111_NoIndex_L001_genomesize.xml')
            stream = open(name, 'w')
            stream.write(MINI_GENOME_XML)
            stream.close()
            g.parse_genomesize(name)
        finally:
            shutil.rmtree(tempdir)

        self.assertTrue('chr1.fa' in g)
        self.assertEqual(len(g), 2)
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


def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestGenomeMap))
    return suite


if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
