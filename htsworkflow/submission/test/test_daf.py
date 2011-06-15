import unittest

from htsworkflow.submission import daf

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
view             Peaks
longLabelPrefix  Caltech Histone Peaks
type             narrowPeak
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
        self.failUnlessEqual(len(parsed['views']['Peaks']), 5)
        self.failUnlessEqual(len(parsed['views']['Signal']), 5)
        signal = parsed['views']['Signal']
        self.failUnlessEqual(signal['required'], False)
        self.failUnlessEqual(signal['longLabelPrefix'],
                             'Caltech Histone Signal')

    def test_rdf(self):
        try:
            import RDF

            parsed = daf.fromstring(test_daf)
            #mem = RDF.Storage(storage_name='hashes',
            #                  options_string='hash-type="memory"'),
            mem = RDF.MemoryStorage()
            model = RDF.Model(mem)
            
            daf.add_to_model(model, parsed)

            writer = RDF.Serializer(name='turtle')
            print writer.serialize_model_to_string(model)
            
        except ImportError, e:
            print "Skipped test_rdf"

def suite():
    return unittest.makeSuite(TestDAF, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
