from unittest import TestCase

from six.moves import StringIO
from htsworkflow.pipelines import genome_mapper

class testGenomeMapper(TestCase):
    def test_construct_mapper(self):
        genomes = {
        'Arabidopsis thaliana': {'v01212004': '/arabidopsis'},
        'Homo sapiens': {'hg18': '/hg18'},
        'Mus musculus': {'mm8': '/mm8',
                        'mm9': '/mm9',
                        'mm10': '/mm10'},
        'Phage': {'174': '/phi'},
        }
        genome_map = genome_mapper.constructMapperDict(genomes)
        
        self.assertEqual("%(Mus musculus|mm8)s" % (genome_map), "/mm8")
        self.assertEqual("%(Phage|174)s" % (genome_map), "/phi")
        self.assertEqual("%(Mus musculus)s" % (genome_map), "/mm10")
        self.assertEqual("%(Mus musculus|mm8)s" % (genome_map), "/mm8")
        self.assertEqual("%(Mus musculus|mm10)s" % (genome_map), "/mm10")
        
        self.assertEqual(len(genome_map.keys()), 6)
        self.assertEqual(len(genome_map.values()), 6)
        self.assertEqual(len(genome_map.items()), 6)
        
        
def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testGenomeMapper))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
