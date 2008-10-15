import unittest

from StringIO import StringIO
from htsworkflow.pipeline import genome_mapper

class testGenomeMapper(unittest.TestCase):
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
        
        self.failUnlessEqual("%(Mus musculus|mm8)s" % (genome_map), "/mm8")
        self.failUnlessEqual("%(Phage|174)s" % (genome_map), "/phi")
        self.failUnlessEqual("%(Mus musculus)s" % (genome_map), "/mm10")
        self.failUnlessEqual("%(Mus musculus|mm8)s" % (genome_map), "/mm8")
        self.failUnlessEqual("%(Mus musculus|mm10)s" % (genome_map), "/mm10")
        
        self.failUnlessEqual(len(genome_map.keys()), 6)
        self.failUnlessEqual(len(genome_map.values()), 6)
        self.failUnlessEqual(len(genome_map.items()), 6)
        
        
def suite():
    return unittest.makeSuite(testGenomeMapper,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
