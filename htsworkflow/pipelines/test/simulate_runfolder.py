"""
Create simulated solexa/illumina runfolders for testing
"""

import os
import shutil

TEST_CODE_DIR = os.path.split(__file__)[0]
TESTDATA_DIR = os.path.join(TEST_CODE_DIR, 'testdata')
 
def make_firecrest_dir(data_dir, version="1.9.2", start=1, stop=37):
    firecrest_dir = os.path.join(data_dir, 
                                 'C%d-%d_Firecrest%s_12-04-2008_diane' % (start, stop, version)
                                 )
    os.mkdir(firecrest_dir)
    return firecrest_dir
    
def make_ipar_dir(data_dir):
    """
    Construct an artificial ipar parameter file and directory
    """
    ipar1_01_file = os.path.join(TESTDATA_DIR, 'IPAR1.01.params')
    shutil.copy(ipar1_01_file, os.path.join(data_dir, '.params'))

    ipar_dir = os.path.join(data_dir, 'IPAR_1.01')
    if not os.path.exists(ipar_dir):
      os.mkdir(ipar_dir)
    return ipar_dir

def make_flowcell_id(runfolder_dir, flowcell_id=None):
    if flowcell_id is None:
        flowcell_id = '207BTAAXY'

    config = """<?xml version="1.0"?>
<FlowcellId>
  <Text>%s</Text>
</FlowcellId>""" % (flowcell_id,)
    config_dir = os.path.join(runfolder_dir, 'Config')

    if not os.path.exists(config_dir):
        os.mkdir(config_dir)
    pathname = os.path.join(config_dir, 'FlowcellId.xml')
    f = open(pathname,'w')
    f.write(config)
    f.close()

def make_matrix(matrix_filename):
    contents = """# Auto-generated frequency response matrix
> A
> C
> G
> T
0.77 0.15 -0.04 -0.04
0.76 1.02 -0.05 -0.06
-0.10 -0.10 1.17 -0.03
-0.13 -0.12 0.80 1.27
"""
    f = open(matrix_filename, 'w')
    f.write(contents)
    f.close()

def make_phasing_params(bustard_dir):
    for lane in range(1,9):
        pathname = os.path.join(bustard_dir, 'params%d.xml' % (lane))
        f = open(pathname, 'w')
        f.write("""<Parameters>
  <Phasing>0.009900</Phasing>
  <Prephasing>0.003500</Prephasing>
</Parameters>
""")
        f.close()

def make_gerald_config_026(gerald_dir):
    source = os.path.join(TESTDATA_DIR, 'gerald_config_0.2.6.xml')
    destination = os.path.join(gerald_dir, 'config.xml')
    shutil.copy(source, destination)

def make_gerald_config_100(gerald_dir):
    source = os.path.join(TESTDATA_DIR, 'gerald_config_1.0.xml')
    destination = os.path.join(gerald_dir, 'config.xml')
    shutil.copy(source, destination)

def make_summary_htm_100(gerald_dir):
    source = os.path.join(TESTDATA_DIR, 'Summary-pipeline100.htm')
    destination = os.path.join(gerald_dir, 'Summary.htm')
    shutil.copy(source, destination)

def make_summary_htm_110(gerald_dir):
    source = os.path.join(TESTDATA_DIR, 'Summary-pipeline110.htm')
    destination = os.path.join(gerald_dir, 'Summary.htm')
    shutil.copy(source, destination)

def make_summary_paired_htm(gerald_dir):
    source = os.path.join(TESTDATA_DIR, 'Summary-paired-pipeline110.htm')
    destination = os.path.join(gerald_dir, 'Summary.htm')
    shutil.copy(source, destination)

def make_summary_ipar130_htm(gerald_dir):
    source = os.path.join(TESTDATA_DIR, 'Summary-ipar130.htm')
    destination = os.path.join(gerald_dir, 'Summary.htm')
    shutil.copy(source, destination)

def make_eland_results(gerald_dir):
    eland_result = """>HWI-EAS229_24_207BTAAXX:1:7:599:759    ACATAGNCACAGACATAAACATAGACATAGAC U0      1       1       3       chrUextra.fa    28189829        R       D.
>HWI-EAS229_24_207BTAAXX:1:7:205:842    AAACAANNCTCCCAAACACGTAAACTGGAAAA  U1      0       1       0       chr2L.fa        8796855 R       DD      24T
>HWI-EAS229_24_207BTAAXX:1:7:776:582    AGCTCANCCGATCGAAAACCTCNCCAAGCAAT        NM      0       0       0
>HWI-EAS229_24_207BTAAXX:1:7:205:842    AAACAANNCTCCCAAACACGTAAACTGGAAAA        U1      0       1       0       Lambda.fa        8796855 R       DD      24T
"""
    for i in range(1,9):
        pathname = os.path.join(gerald_dir,
                                's_%d_eland_result.txt' % (i,))
        f = open(pathname, 'w')
        f.write(eland_result)
        f.close()

def make_eland_multi(gerald_dir, paired=False):
    eland_multi = [""">HWI-EAS229_60_30DP9AAXX:1:1:1221:788   AAGATATCTACGACGTGGTATGGCGGTGTCTGGTCGT      NM
>HWI-EAS229_60_30DP9AAXX:1:1:931:747    AAAAAAGCAAATTTCATTCACATGTTCTGTGTTCATA   1:0:2   chr5.fa:55269838R0
>HWI-EAS229_60_30DP9AAXX:1:1:1121:379   AGAAGAGACATTAAGAGTTCCTGAAATTTATATCTGG   2:1:0   chr16.fa:46189180R1,chr7.fa:122968519R0,chr8.fa:48197174F0
>HWI-EAS229_60_30DP9AAXX:1:1:892:1155   ACATTCTCCTTTCCTTCTGAAGTTTTTACGATTCTTT   0:9:10  chr10.fa:114298201F1,chr12.fa:8125072F1,19500297F2,42341293R2,chr13.fa:27688155R2,95069772R1,chr15.fa:51016475F2,chr16.fa:27052155F2,chr1.fa:192426217R2,chr21.fa:23685310R2,chr2.fa:106680068F1,chr3.fa:185226695F2,chr4.fa:106626808R2,chr5.fa:14704894F1,43530779F1,126543189F2,chr6.fa:74284101F1,chr7.fa:22516603F1,chr9.fa:134886204R
>HWI-EAS229_60_30DP9AAXX:1:1:931:747    AAAAAAGCAAATTTCATTCACATGTTCTGTGTTCATA   1:0:0   spike.fa/sample1:55269838R0
>HWI-EAS229_60_30DP9AAXX:1:1:931:747    AAAAAAGCAAATTTCATTCACATGTTCTGTGTTCATA   1:0:0   spike.fa/sample2:55269838R0
""", """>HWI-EAS229_60_30DP9AAXX:1:1:1221:788   AAGATATCTACGACGTGGTATGGCGGTGTCTGGTCGT      NM
>HWI-EAS229_60_30DP9AAXX:1:1:1221:788   NNNNNNNNNNNNNNGTGGTATGGCGGTGTCTGGTCGT     QC 
>HWI-EAS229_60_30DP9AAXX:1:1:931:747    AAAAAAGCAAATTTCATTCACATGTTCTGTGTTCATA   1:0:2   chr5.fa:55269838R0
>HWI-EAS229_60_30DP9AAXX:1:1:1121:379   AGAAGAGACATTAAGAGTTCCTGAAATTTATATCTGG   2:1:0   chr16.fa:46189180R1,chr7.fa:122968519R0,chr8.fa:48197174F0,chr7.fa:22516603F1,chr9.fa:134886204R
>HWI-EAS229_60_30DP9AAXX:1:1:892:1155   ACATTCTCCTTTCCTTCTGAAGTTTTTACGATTCTTT   0:9:10  chr10.fa:114298201F1,chr12.fa:8125072F1,19500297F2,42341293R2,chr13.fa:27688155R2,95069772R1,chr15.fa:51016475F2,chr16.fa:27052155F2,chr1.fa:192426217R2,chr21.fa:23685310R2,chr2.fa:106680068F1,chr3.fa:185226695F2,chr4.fa:106626808R2,chr5.fa:14704894F1,43530779F1,126543189F2,chr6.fa:74284101F1
>HWI-EAS229_60_30DP9AAXX:1:1:931:747    AAAAAAGCAAATTTCATTCACATGTTCTGTGTTCATA   1:0:0   spike.fa/sample1:55269838R0
>HWI-EAS229_60_30DP9AAXX:1:1:931:747    AAAAAAGCAAATTTCATTCACATGTTCTGTGTTCATA   1:0:0   spike.fa/sample2:55269838R0
"""]
    if paired:
        for e in [1,2]:
            for i in range(1,9):
                pathname = os.path.join(gerald_dir,
                                        's_%d_%d_eland_multi.txt' % (i,e))
                f = open(pathname, 'w')
                f.write(eland_multi[e-1])
                f.close()
    else:
        for i in range(1,9):
            pathname = os.path.join(gerald_dir,
                                    's_%d_eland_multi.txt' % (i,))
            f = open(pathname, 'w')
            f.write(eland_multi[0])
            f.close()
