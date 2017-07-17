from unittest import TestCase, TestSuite, defaultTestLoader
from six.moves import StringIO

from htsworkflow.submission import ucsc


ENCODE_FILES="""wgEncodeGisChiaPetHCT116D000005593.bed.gz	project=wgEncode; grant=Ruan; lab=GIS-Ruan; composite=wgEncodeGisChiaPet; dataType=ChiaPet; view=Interactions; cell=HCT-116; antibody=Pol2; replicate=1; origAssembly=hg19; dataVersion=ENCODE Jan 2011 Freeze; dccAccession=wgEncodeEH001427; dateSubmitted=2011-02-04; dateUnrestricted=2011-11-04; subId=3267; labVersion=CHH524; tableName=wgEncodeGisChiaPetHCT116D000005593; type=bed; md5sum=a3c7420aece4acfb15f80f4dfe9f1fb3; size=924K
wgEncodeCaltechRnaSeqGm12878R2x75Il200FastqRd2Rep1.fastq.tgz	project=wgEncode; grant=Myers; lab=Caltech; composite=wgEncodeCaltechRnaSeq; dataType=RnaSeq; view=FastqRd2; cell=GM12878; localization=cell; rnaExtract=longPolyA; readType=2x75; insertLength=200; replicate=1; origAssembly=hg18; dataVersion=ENCODE Jan 2011 Freeze; dccAccession=wgEncodeEH000122; dateSubmitted=2010-07-14; dateResubmitted=2010-06-21; dateUnrestricted=2011-04-14; subId=1647; type=fastq; md5sum=51c4d1679b0ad29888bea2b40e26364a; size=4.8G
"""


class TestUCSCInfo(TestCase):
    def test_parse_encodedcc_file(self):
        stream = StringIO(ENCODE_FILES)
        file_index = ucsc.parse_ucsc_file_index(stream, 'http://example.com/files')
        self.assertEqual(len(file_index), 2)

        for attributes in file_index.values():
            self.assertTrue('subId' in attributes)
            self.assertTrue('project' in attributes)
            self.assertEqual(attributes['project'], 'wgEncode')

def suite():
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestUCSCInfo))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest='suite')
