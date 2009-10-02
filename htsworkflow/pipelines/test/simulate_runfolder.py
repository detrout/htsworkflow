"""
Create simulated solexa/illumina runfolders for testing
"""

import os
import shutil

TEST_CODE_DIR = os.path.split(__file__)[0]
TESTDATA_DIR = os.path.join(TEST_CODE_DIR, 'testdata')
LANE_LIST = range(1,9)
TILE_LIST = range(1,101)

def make_firecrest_dir(data_dir, version="1.9.2", start=1, stop=37):
    firecrest_dir = os.path.join(data_dir, 
                                 'C%d-%d_Firecrest%s_12-04-2008_diane' % (start, stop, version)
                                 )
    os.mkdir(firecrest_dir)
    return firecrest_dir
    
def make_ipar_dir(data_dir, version='1.01'):
    """
    Construct an artificial ipar parameter file and directory
    """
    ipar1_01_file = os.path.join(TESTDATA_DIR, 'IPAR1.01.params')
    shutil.copy(ipar1_01_file, os.path.join(data_dir, '.params'))

    ipar_dir = os.path.join(data_dir, 'IPAR_%s' % (version,))
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

def make_bustard_config132(image_dir):
    source = os.path.join(TESTDATA_DIR, 'bustard-config132.xml')
    destination = os.path.join(image_dir, 'config.xml')
    shutil.copy(source, destination)

def make_rta_intensities_1460(data_dir, version='1.4.6.0'):
    """
    Construct an artificial RTA Intensities parameter file and directory
    """
    intensities_dir = os.path.join(data_dir, 'Intensities')
    if not os.path.exists(intensities_dir):
      os.mkdir(intensities_dir)
 
    param_file = os.path.join(TESTDATA_DIR, 'rta_intensities_config.xml')
    shutil.copy(param_file, os.path.join(intensities_dir, 'config.xml'))

    return intensities_dir

def make_rta_basecalls_1460(intensities_dir):
    """
    Construct an artificial RTA Intensities parameter file and directory
    """
    basecalls_dir = os.path.join(intensities_dir, 'BaseCalls')
    if not os.path.exists(basecalls_dir):
      os.mkdir(basecalls_dir)
 
    param_file = os.path.join(TESTDATA_DIR, 'rta_basecalls_config.xml')
    shutil.copy(param_file, os.path.join(basecalls_dir, 'config.xml'))

    return basecalls_dir

def make_qseqs(bustard_dir, in_temp=True):
    """
    Fill gerald directory with qseq files
    """
    # 42BRJ 8 1 0039 happened to be a better than usual tile, in that there
    # was actually sequence at the start
    source = os.path.join(TESTDATA_DIR, '42BRJAAXX_8_1_0039_qseq.txt')
    destdir = bustard_dir
    if not os.path.isdir(destdir):
        os.mkdir(destdir)
        
    for lane in LANE_LIST:
        for tile in TILE_LIST:
            destination = os.path.join(bustard_dir, 's_%d_1_%04d_qseq.txt' % (lane, tile))
            shutil.copy(source, destination)

    make_matrix_dir(bustard_dir)
    make_phasing_dir(bustard_dir)

    summary_source = os.path.join(TESTDATA_DIR, '42BRJAAXX_BustardSummary.xml')
    summary_dest = os.path.join(bustard_dir, 'BustardSummary.xml')
    shutil.copy(summary_source, summary_dest)
    
    return destdir

def make_scores(gerald_dir, in_temp=True):
    """
    Fill gerald directory with score temp files
    will create the directory if it doesn't exist.
    """
    source = os.path.join(TESTDATA_DIR, 's_1_0001_score.txt')
    destdir = gerald_dir
    if in_temp:
        destdir = os.path.join(destdir, 'Temp')
    if not os.path.isdir(destdir):
        os.mkdir(destdir)
        
    for lane in LANE_LIST:
        for tile in TILE_LIST:
            destination = os.path.join(destdir, 's_%d_%04d_score.txt' % (lane, tile))
            shutil.copy(source, destination)
            
    return destdir

def make_matrix_dir(bustard_dir):
    """
    Create several matrix files in <bustard_dir>/Matrix/

    from pipeline 1.4    
    """
    destdir = os.path.join(bustard_dir, 'Matrix')
    if not os.path.isdir(destdir):
        os.mkdir(destdir)
        
    source = os.path.join(TESTDATA_DIR, '42BRJAAXX_8_02_matrix.txt')
    for lane in LANE_LIST:
        destination = os.path.join(destdir, 's_%d_02_matrix.txt' % ( lane, ))
        shutil.copy(source, destination)
        
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

def make_phasing_dir(bustard_dir):
    """
    Create several phasing files in <bustard_dir>/Phasing/

    from pipeline 1.4
    """
    destdir = os.path.join(bustard_dir, 'Phasing')
    if not os.path.isdir(destdir):
        os.mkdir(destdir)
        
    source = os.path.join(TESTDATA_DIR, '42BRJAAXX_8_01_phasing.xml')
    for lane in LANE_LIST:
        destination = os.path.join(destdir, 's_%d_01_phasing.xml' % ( lane, ))
        shutil.copy(source, destination)
    
def make_phasing_params(bustard_dir):
    for lane in LANE_LIST:
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
    for i in LANE_LIST:
        pathname = os.path.join(gerald_dir,
                                's_%d_eland_result.txt' % (i,))
        f = open(pathname, 'w')
        f.write(eland_result)
        f.close()

def make_eland_multi(gerald_dir, paired=False, lane_list=LANE_LIST):
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
            for i in lane_list:
                pathname = os.path.join(gerald_dir,
                                        's_%d_%d_eland_multi.txt' % (i,e))
                f = open(pathname, 'w')
                f.write(eland_multi[e-1])
                f.close()
    else:
        for i in lane_list:
            pathname = os.path.join(gerald_dir,
                                    's_%d_eland_multi.txt' % (i,))
            f = open(pathname, 'w')
            f.write(eland_multi[0])
            f.close()

def make_scarf(gerald_dir, lane_list=LANE_LIST):
    seq = """HWI-EAS229_92_30VNBAAXX:1:1:0:161:NCAATTACACGACGCTAGCCCTAAAGCTATTTCGAGG:E[aaaabb^a\a_^^a[S`ba_WZUXaaaaaaUKPER
HWI-EAS229_92_30VNBAAXX:1:1:0:447:NAGATGCGCATTTGAAGTAGGAGCAAAAGATCAAGGT:EUabaab^baabaaaaaaaa^^Uaaaaa\aaaa__`a
HWI-EAS229_92_30VNBAAXX:1:1:0:1210:NATAGCCTCTATAGAAGCCACTATTATTTTTTTCTTA:EUa`]`baaaaa^XQU^a`S``S_`J_aaaaaabb^V
HWI-EAS229_92_30VNBAAXX:1:1:0:1867:NTGGAGCAGATATAAAAACAGATGGTGACGTTGAAGT:E[^UaaaUaba^aaa^aa^XV\baaLaLaaaaQVXV^
HWI-EAS229_92_30VNBAAXX:1:1:0:1898:NAGCTCGTGTCGTGAGATGTTAGGTTAAGTCCTGCAA:EK_aaaaaaaaaaaUZaaZaXM[aaaXSM\aaZ]URE
"""
    for l in lane_list:
        pathname = os.path.join(gerald_dir, 's_%d_sequence.txt' %(l,))
        f = open(pathname,'w')
        f.write(seq)
        f.close()

def make_fastq(gerald_dir, lane_list=LANE_LIST):
    seq = """@HWI-EAS229:1:2:182:712#0/1
AAAAAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAA
+HWI-EAS229:1:2:182:712#0/1
\bab_bbaabbababbaaa]]D]bb_baabbab\baa
@HWI-EAS229:1:2:198:621#0/1
CCCCCCCCCCCCCCCCCCCCCNCCCCCCCCCCCCCCC
+HWI-EAS229:1:2:198:621#0/1
[aaaaaaa`_`aaaaaaa[`ZDZaaaaaaaaaaaaaa
@HWI-EAS229:1:2:209:1321#0/1
AAAAAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAA
+HWI-EAS229:1:2:209:1321#0/1
_bbbbbaaababaabbbbab]D]aaaaaaaaaaaaaa
"""
    for l in lane_list:
        pathname = os.path.join(gerald_dir, 's_%d_sequence.txt' %(l,))
        f = open(pathname,'w')
        f.write(seq)
        f.close()


