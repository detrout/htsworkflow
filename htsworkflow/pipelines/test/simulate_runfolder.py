"""
Create simulated solexa/illumina runfolders for testing
"""
import gzip
import os
import shutil

TEST_CODE_DIR = os.path.split(__file__)[0]
TESTDATA_DIR = os.path.join(TEST_CODE_DIR, 'testdata')
LANE_LIST = range(1,9)
TILE_LIST = range(1,101)
HISEQ_TILE_LIST = [1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108,
                   1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208,
                   2101, 2102, 2103, 2104, 2105, 2106, 2107, 2108,
                   2201, 2202, 2203, 2204, 2205, 2206, 2207, 2208,]

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

def make_runinfo(runfolder_dir, flowcell_id):
    """Simulate a RunInfo.xml file created by >= RTA 1.9
    """
    xml = '''<?xml version="1.0"?>
<RunInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" Version="2">
  <Run Id="{runfolder}" Number="101">
    <Flowcell>{flowcell}</Flowcell>
    <Instrument>SN787</Instrument>
    <Date>110815</Date>
    <Reads>
      <Read Number="1" NumCycles="50" IsIndexedRead="N" />
      <Read Number="2" NumCycles="7" IsIndexedRead="Y" />
    </Reads>
    <FlowcellLayout LaneCount="8" SurfaceCount="2" SwathCount="3" TileCount="8" />
    <AlignToPhiX />
  </Run>
</RunInfo>
'''
    path, runfolder = os.path.split(runfolder_dir)
    runinfo = os.path.join(runfolder_dir, 'RunInfo.xml')
    stream = open(runinfo, 'w')
    stream.write(xml.format(runfolder=runfolder, flowcell=flowcell_id))
    stream.close()
    return runinfo

def make_bustard_config132(image_dir):
    source = os.path.join(TESTDATA_DIR, 'bustard-config132.xml')
    destination = os.path.join(image_dir, 'config.xml')
    shutil.copy(source, destination)

def make_aligned_config_1_12(aligned_dir):
    """This is rouglhly equivalent to the old gerald file"""
    source = os.path.join(TESTDATA_DIR, '1_12', 'aligned_config_1_12.xml')
    destination = os.path.join(aligned_dir, 'config.xml')
    shutil.copy(source, destination)

def make_unaligned_config_1_12(unaligned_dir):
    demultiplex_pairs = [ # (src,
      # dest),
        (os.path.join(TESTDATA_DIR, '1_12', 'demultiplex_1.12.4.2.xml'),
         os.path.join(unaligned_dir, 'DemultiplexConfig.xml')),
        (os.path.join(TESTDATA_DIR, '1_12',
                      'demultiplexed_bustard_1.12.4.2.xml'),
         os.path.join(unaligned_dir, 'DemultiplexedBustardConfig.xml')),
        (os.path.join(TESTDATA_DIR, '1_12',
                      'demultiplexed_summary_1.12.4.2.xml'),
         os.path.join(unaligned_dir, 'DemultiplexedBustardSummary.xml')),
    ]
    for src, dest in demultiplex_pairs:
        shutil.copy(src, dest)

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

def make_rta_intensities_1870(data_dir, version='1.8.70.0'):
    """
    Construct an artificial RTA Intensities parameter file and directory
    """
    intensities_dir = os.path.join(data_dir, 'Intensities')
    if not os.path.exists(intensities_dir):
      os.mkdir(intensities_dir)

    param_file = os.path.join(TESTDATA_DIR, 'rta_intensities_config_1870.xml')
    shutil.copy(param_file, os.path.join(intensities_dir, 'config.xml'))

    return intensities_dir

def make_rta_intensities_1_10(data_dir, version='1.10.36.0'):
    """
    Construct an artificial RTA Intensities parameter file and directory
    """
    intensities_dir = os.path.join(data_dir, 'Intensities')
    if not os.path.exists(intensities_dir):
      os.mkdir(intensities_dir)

    param_file = os.path.join(TESTDATA_DIR, 'rta_intensities_config_1.10.xml')
    shutil.copy(param_file, os.path.join(intensities_dir, 'config.xml'))

    return intensities_dir

def make_rta_intensities_1_12(data_dir, version='1.12.4.2'):
    """
    Construct an artificial RTA Intensities parameter file and directory
    """
    intensities_dir = os.path.join(data_dir, 'Intensities')
    if not os.path.exists(intensities_dir):
      os.mkdir(intensities_dir)

    param_file = os.path.join(TESTDATA_DIR, '1_12',
                              'rta_intensities_config_1.12.4.2.xml')
    shutil.copy(param_file, os.path.join(intensities_dir, 'RTAConfig.xml'))

    return intensities_dir

def make_rta_basecalls_1870(intensities_dir):
    """
    Construct an artificial RTA Intensities parameter file and directory
    """
    basecalls_dir = os.path.join(intensities_dir, 'BaseCalls')
    if not os.path.exists(basecalls_dir):
      os.mkdir(basecalls_dir)

    param_file = os.path.join(TESTDATA_DIR, 'rta_basecalls_config_1870.xml')
    shutil.copy(param_file, os.path.join(basecalls_dir, 'config.xml'))

    return basecalls_dir

def make_rta_basecalls_1_10(intensities_dir):
    """
    Construct an artificial RTA Intensities parameter file and directory
    """
    basecalls_dir = os.path.join(intensities_dir, 'BaseCalls')
    if not os.path.exists(basecalls_dir):
        os.mkdir(basecalls_dir)

    make_qseqs(basecalls_dir, basecall_info=ABXX_BASE_CALL_INFO)
    param_file = os.path.join(TESTDATA_DIR, 'rta_basecalls_config_1.10.xml')
    shutil.copy(param_file, os.path.join(basecalls_dir, 'config.xml'))

    return basecalls_dir

def make_rta_basecalls_1_12(intensities_dir):
    """
    Construct an artificial RTA Intensities parameter file and directory
    """
    basecalls_dir = os.path.join(intensities_dir, 'BaseCalls')
    if not os.path.exists(basecalls_dir):
        os.mkdir(basecalls_dir)

    make_qseqs(basecalls_dir, basecall_info=ABXX_BASE_CALL_INFO)
    param_file = os.path.join(TESTDATA_DIR, '1_12',
                              'rta_basecalls_config_1.12.4.2.xml')
    shutil.copy(param_file, os.path.join(basecalls_dir, 'config.xml'))

    return basecalls_dir


def make_qseqs(bustard_dir, basecall_info=None):
    """
    Fill gerald directory with qseq files
    """
    if basecall_info is None:
        qseq_file = '42BRJAAXX_8_1_0039_qseq.txt'
        tile_list = TILE_LIST
        summary_file = '42BRJAAXX_BustardSummary.xml'
    else:
        qseq_file = basecall_info.qseq_file
        tile_list = basecall_info.tile_list
        summary_file = basecall_info.basecall_summary

    # 42BRJ 8 1 0039 happened to be a better than usual tile, in that there
    # was actually sequence at the start
    source = os.path.join(TESTDATA_DIR, qseq_file)
    destdir = bustard_dir
    if not os.path.isdir(destdir):
        os.mkdir(destdir)

    for lane in LANE_LIST:
        for tile in tile_list:
            destination = os.path.join(bustard_dir, 's_%d_1_%04d_qseq.txt' % (lane, tile))
            shutil.copy(source, destination)

    make_matrix_dir(bustard_dir)
    make_phasing_dir(bustard_dir)

    summary_source = os.path.join(TESTDATA_DIR, summary_file)
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

def make_matrix_dir_rta160(bustard_dir):
    """
    Create several matrix files in <bustard_dir>/Matrix/
    """
    destdir = os.path.join(bustard_dir, 'Matrix')
    if not os.path.isdir(destdir):
        os.mkdir(destdir)

    source = os.path.join(TESTDATA_DIR, '61MMFAAXX_4_1_matrix.txt')
    lane_fragments = [ "_%d" % (l,) for l in LANE_LIST]
    for fragment in lane_fragments:
        destination = os.path.join(destdir, 's%s_1_matrix.txt' % ( fragment, ))
        shutil.copy(source, destination)

def make_matrix_dir_rta_1_10(bustard_dir):
    make_matrix_dir_rta160(bustard_dir)

def make_matrix_dir_rta_1_12(bustard_dir):
    make_matrix_dir_rta160(bustard_dir)

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

def make_gerald_config_1_7(gerald_dir):
    """CASAVA 1.7 gerald config"""
    source = os.path.join(TESTDATA_DIR, 'gerald_config_1.7.xml')
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

def make_summary_rta160_xml(gerald_dir):
    source = os.path.join(TESTDATA_DIR, 'Summary-rta160.xml')
    destination = os.path.join(gerald_dir, 'Summary.xml')
    shutil.copy(source, destination)


def make_summary_casava1_7_xml(gerald_dir):
    source = os.path.join(TESTDATA_DIR, 'Summary-casava1.7.xml')
    destination = os.path.join(gerald_dir, 'Summary.xml')
    shutil.copy(source, destination)

def make_status_rta1_12(datadir):
    sourcedir = os.path.join(TESTDATA_DIR, '1_12')
    status_htm = os.path.join(sourcedir, 'Status.htm')
    destination = os.path.join(datadir, 'Status.htm')
    shutil.copy(status_htm, destination)

    status_dir = os.path.join(datadir, 'Status_Files')
    status_source_dir = os.path.join(sourcedir, 'Status_Files')
    shutil.copytree(status_source_dir, status_dir)

    report_source_dir = os.path.join(sourcedir, 'reports')
    report_dir = os.path.join(datadir, 'reports')
    shutil.copytree(report_source_dir, report_dir)

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

def make_eland_export(gerald_dir, paired=False, lane_list=LANE_LIST):
    source = os.path.join(TESTDATA_DIR, 'casava_1.7_export.txt')

    for i in lane_list:
        destination = os.path.join(gerald_dir,
                                   's_%d_export.txt' % (i,))
        shutil.copy(source, destination)


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
\\bab_bbaabbababbaaa]]D]bb_baabbab\baa
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

UNALIGNED_READS = [1,2]
UNALIGNED_SAMPLES = [ (1, UNALIGNED_READS, '11111', None, None),
                      (2, UNALIGNED_READS, '11112', None, None),
                      (3, UNALIGNED_READS, '11113', 1, 'ATCACG'),
                      (3, UNALIGNED_READS, '11113', 2, 'CGATGT'),
                      (3, UNALIGNED_READS, '11113', 3, 'TTAGGC'),
                      (4, UNALIGNED_READS, '11114', 6, 'GCCAAT'),
                      (5, UNALIGNED_READS, '11115', 1, 'ATCACG'),
                      (5, UNALIGNED_READS, '11116', 7, 'ACTTGA'),
                      (5, UNALIGNED_READS, '11117', 9, 'GATCAG'),
                      (6, UNALIGNED_READS, '11118', 1, 'ATCACG'),
                      (7, UNALIGNED_READS, '11119', 2, 'CGATGT'),
                      (8, UNALIGNED_READS, '11120', 3, 'TTAGGC'),
                      (1, UNALIGNED_READS, None, None, None),
                      (2, UNALIGNED_READS, None, None, None),
                      (3, UNALIGNED_READS, None, None, None),
                      (4, UNALIGNED_READS, None, None, None),
                      (5, UNALIGNED_READS, None, None, None)]


def make_aligned_eland_export(aligned_dir, flowcell_id):
    summary_source = os.path.join(TESTDATA_DIR, 'sample_summary_1_12.htm')
    for lane, read, project_id, index_id, index_seq in UNALIGNED_SAMPLES:
        paths = DemultiplexedPaths(aligned_dir,
                                   flowcell_id,
                                   lane,
                                   project_id,
                                   index_id,
                                   index_seq)
        paths.make_sample_dirs()
        paths.make_summary_dirs()
        summary_dest = os.path.join(paths.summary_dir, 'Sample_Summary.htm')
        shutil.copy(summary_source, summary_dest)

        body = get_aligned_sample_export(lane, index_seq)
        for split in ['001','002']:
            for read in UNALIGNED_READS:
                suffix = 'R{0}_{1}_export.txt.gz'.format(read, split)
                pathname = paths.make_test_filename(suffix)
                stream = gzip.open(pathname, 'w')
                stream.write(body)
                stream.close()


def make_unaligned_fastqs_1_12(unaligned_dir, flowcell_id):
    """Create a default mix of unaligned sample files
    """
    for lane, read, name, index_id, index in UNALIGNED_SAMPLES:
        make_unaligned_fastq_sample_1_12(unaligned_dir,
                                         flowcell_id,
                                         lane,
                                         read,
                                         name,
                                         index_id,
                                         index)

def make_unaligned_fastq_sample_1_12(unaligned_dir,
                                     flowcell_id,
                                     lane,
                                     reads,
                                     project_id,
                                     index_id=None,
                                     index_seq=None):

    paths = DemultiplexedPaths(unaligned_dir,
                               flowcell_id,
                               lane,
                               project_id,
                               index_id,
                               index_seq)
    paths.make_sample_dirs()

    sample_seq = get_unaligned_sample_fastq_data(flowcell_id, lane, index_seq)
    for split in ['001','002']:
        for read in reads:
            suffix = 'R{0}_{1}.fastq.gz'.format(read, split)
            pathname = paths.make_test_filename(suffix)
            stream = gzip.open(pathname, 'w')
            stream.write(sample_seq)
            stream.close()

    sheetname = os.path.join(paths.sample_dir, 'SampleSheet.csv')
    stream = open(sheetname, 'w')
    stream.write('FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject'+os.linesep)
    template = '{flowcell},{lane},{id},mm9,{index},Sample #{id},N,PR_indexing,Operator,{sample_project}'+os.linesep
    stream.write(template.format(flowcell=flowcell_id,
                                 lane=lane,
                                 id=paths.sample_id,
                                 index=paths.index_seq,
                                 sample_project=paths.sample_project))
    stream.close()


class DemultiplexedPaths(object):
    def __init__(self, basedir, flowcell_id, lane, project_id, index_id, index_seq):
        if lane not in LANE_LIST:
            raise ValueError("Invalid lane ID: {0}".format(lane))
        self.basedir = basedir
        self.flowcell_id = flowcell_id
        self.lane = lane

        if project_id is None:
            # undetermined
            self.index_seq = ''
            self.sample_id = 'lane{0}'.format(lane)
            self.sample_project = 'Undetermined_indices'
            self.rootname = 'lane{lane}_Undetermined_L00{lane}_'.format(
                lane=lane)
            self.project_dir = 'Undetermined_indices'
            self.sample_dir = 'Sample_lane{lane}'.format(lane=lane)
        elif index_seq is None:
            self.index_seq = ''
            self.sample_id = project_id
            self.sample_project = '{project_id}'.format(project_id=project_id)
            self.rootname = '{project_id}_NoIndex_L00{lane}_'.format(
                project_id=project_id,
                lane=lane)
            self.project_dir = 'Project_' + self.sample_project
            self.sample_dir = 'Sample_{project_id}'.format(
                project_id=project_id)
        else:
            self.index_seq = index_seq
            self.sample_id = project_id
            self.sample_project = '{project_id}_Index{index_id}'.format(
                project_id=project_id,
                index_id=index_id)
            self.rootname = '{project_id}_{index}_L00{lane}_'.format(
                project_id=project_id,
                index=index_seq,
                lane=lane)
            self.project_dir = 'Project_' + self.sample_project
            self.sample_dir = 'Sample_{project_id}'.format(
                project_id=project_id)

        self.project_dir = os.path.join(self.basedir, self.project_dir)
        self.sample_dir = os.path.join(self.project_dir, self.sample_dir)
        self.summary_dir = 'Summary_Stats_{0}'.format(self.flowcell_id)
        self.summary_dir = os.path.join(self.project_dir, self.summary_dir)


    def make_sample_dirs(self):
        if not os.path.isdir(self.project_dir):
            os.mkdir(self.project_dir)
        if not os.path.isdir(self.sample_dir):
            os.mkdir(self.sample_dir)

    def make_summary_dirs(self):
        if not os.path.isdir(self.summary_dir):
            os.mkdir(self.summary_dir)

    def make_test_filename(self, suffix):
        filename = self.rootname + suffix
        pathname = os.path.join(self.sample_dir, filename)
        return pathname

    def dump(self):
        print ('index seq: {0}'.format(self.index_seq))

        print ('project dir: {0}'.format(self.project_dir))
        print ('sample dir: {0}'.format(self.sample_dir))
        print ('rootname: {0}'.format(self.rootname))
        print ('path: {0}'.format(
            os.path.join(self.project_dir,
                         self.sample_dir,
                         self.rootname+'R1_001.fastq.gz')))


def get_unaligned_sample_fastq_data(flowcell_id, lane, index_seq):
    seq = """@HWI-ST0787:101:{flowcell}:{lane}:1101:2416:3469 1:Y:0:{index}
TCCTTCATTCCACCGGAGTCTGTGGAATTCTCGGGTGCCAAGGAACTCCA
+
CCCFFFFFHHHHHJJJJJJJJJIJJJJJJJJJJJJJJJJIIJJIIJJJJJ
@HWI-ST0787:101:{flowcell}:{lane}:1101:2677:3293 1:Y:0:{index}
TGGAAATCCATTGGGGTTTCCCCTGGAATTCTCGGGTGCCAAGGAACTCC
+
@CCFF3BDHHHHHIIIIIHHIIIDIIIGIIIEGIIIIIIIIIIIIIIIHH
@HWI-ST0787:101:{flowcell}:{lane}:1101:2616:3297 1:Y:0:{index}
TAATACTGCCGGGTAATGATGGCTGGAATTCTCGGGTGCCAAGGAACTCC
+
CCCFFFFFHHHHHCGHJJJJJJJJJJJJJJJJJIIJJJJJJJJJIHJJJI
@HWI-ST0787:101:{flowcell}:{lane}:1101:2545:3319 1:N:0:{index}
TCCTTCATTCCACCGGAGTCTGCTGGAATTCTCGGGTGCCAAGGAACTCC
+
CCCFFFFFHHHFHJGIGHIJHIIGHIGIGIGEHFIJJJIHIJHJIIJJIH
""".format(flowcell=flowcell_id, lane=lane, index=index_seq)
    return seq

def get_aligned_sample_export(lane, index_seq):
    body = """HWI-ST0787\t102\t{lane}\t1101\t1207\t1993\t{index}\t1\tAANGGATTCGATCCGGCTTAAGAGATGAAAACCGAAAGGGCCGACCGAA\taaBS`ccceg[`ae[dRR_[[SPPPP__ececfYYWaegh^\\ZLLY\\X`\tNM\t\t\t\t\t\t
HWI-ST0787\t102\t{lane}\t1101\t1478\t1997\t{index}\t1\tCAAGAACCCCGGGGGGGGGGGGGCAGAGAGGGGGAATTTTTTTTTTGTT\tBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB\tNM\t\t\t\t\t\t\t\t\t\t\tN
HWI-ST0787\t102\t{lane}\t1101\t1625\t1994\t{index}\t1\tAANAATGCTACAGAGACAAAACAAAACTGATATGAAAGTTGAGAATAAA\tB^BS\cccgegg[Q[QQQ[`egdgffbeggfgh^^YcfgfhXaHY^O^c\tchr9.fa\t67717938\tR\t99\t72
HWI-ST0787\t102\t{lane}\t1101\t1625\t1994\t{index}\t1\tAANAATGCTACAGAGACAAAACAAAACTGATATGAAAGTTGAGAATAAA\tB^BS\cccgegg[Q[QQQ[`egdgffbeggfgh^^YcfgfhXaHY^O^c\t3:4:3\t\t\t\t\t\t\t\t\t\t\tY
""".format(lane=lane, index=index_seq)
    return body

def print_ls_tree(root):
    """List tree contents, useful for debugging.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            print os.path.join(dirpath, filename)


class BaseCallInfo(object):
    """Provide customization for how to setup the base call mock data
    """
    def __init__(self, qseq_file, tile_list, basecall_summary):
        self.qseq_file = qseq_file
        self.tile_list = tile_list
        self.basecall_summary = basecall_summary

# First generation HiSeq Flowcell
ABXX_BASE_CALL_INFO = BaseCallInfo(
    qseq_file='AA01CCABXX_8_2_2207_qseq.txt',
    tile_list = HISEQ_TILE_LIST,
    basecall_summary = 'AA01CCABXX_BustardSummary.xml')
