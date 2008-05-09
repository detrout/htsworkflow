#!/usr/bin/env python

from datetime import datetime, date
import os
import tempfile
import shutil
import unittest

from gaworkflow.pipeline import firecrest
from gaworkflow.pipeline import bustard
from gaworkflow.pipeline import gerald
from gaworkflow.pipeline import runfolder
from gaworkflow.pipeline.runfolder import ElementTree


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

def make_matrix(matrix_dir):
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
    s_matrix = os.path.join(matrix_dir, 's_matrix.txt')
    f = open(s_matrix, 'w')
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

def make_gerald_config(gerald_dir):
    config_xml = """<RunParameters>
<ChipWideRunParameters>
  <ANALYSIS>default</ANALYSIS>
  <BAD_LANES></BAD_LANES>
  <BAD_TILES></BAD_TILES>
  <CONTAM_DIR></CONTAM_DIR>
  <CONTAM_FILE></CONTAM_FILE>
  <ELAND_GENOME>Need_to_specify_ELAND_genome_directory</ELAND_GENOME>
  <ELAND_MULTIPLE_INSTANCES>8</ELAND_MULTIPLE_INSTANCES>
  <ELAND_REPEAT></ELAND_REPEAT>
  <EMAIL_DOMAIN>domain.com</EMAIL_DOMAIN>
  <EMAIL_LIST>diane</EMAIL_LIST>
  <EMAIL_SERVER>localhost:25</EMAIL_SERVER>
  <EXPT_DIR>/home/diane/gec/080416_HWI-EAS229_0024_207BTAAXX/Data/C1-33_Firecrest1.8.28_19-04-2008_diane/Bustard1.8.28_19-04-2008_diane</EXPT_DIR>
  <EXPT_DIR_ROOT>/home/diane/gec</EXPT_DIR_ROOT>
  <FORCE>1</FORCE>
  <GENOME_DIR>/home/diane/proj/SolexaPipeline-0.2.2.6/Goat/../Gerald/../../Genomes</GENOME_DIR>
  <GENOME_FILE>Need_to_specify_genome_file_name</GENOME_FILE>
  <HAMSTER_FLAG>genome</HAMSTER_FLAG>
  <OUT_DIR>/home/diane/gec/080416_HWI-EAS229_0024_207BTAAXX/Data/C1-33_Firecrest1.8.28_19-04-2008_diane/Bustard1.8.28_19-04-2008_diane/GERALD_19-04-2008_diane</OUT_DIR>
  <POST_RUN_COMMAND></POST_RUN_COMMAND>
  <PRB_FILE_SUFFIX>_prb.txt</PRB_FILE_SUFFIX>
  <PURE_BASES>12</PURE_BASES>
  <QF_PARAMS>'((CHASTITY&gt;=0.6))'</QF_PARAMS>
  <QHG_FILE_SUFFIX>_qhg.txt</QHG_FILE_SUFFIX>
  <QUALITY_FORMAT>--symbolic</QUALITY_FORMAT>
  <READ_LENGTH>32</READ_LENGTH>
  <SEQUENCE_FORMAT>--scarf</SEQUENCE_FORMAT>
  <SEQ_FILE_SUFFIX>_seq.txt</SEQ_FILE_SUFFIX>
  <SIG_FILE_SUFFIX_DEPHASED>_sig2.txt</SIG_FILE_SUFFIX_DEPHASED>
  <SIG_FILE_SUFFIX_NOT_DEPHASED>_sig.txt</SIG_FILE_SUFFIX_NOT_DEPHASED>
  <SOFTWARE_VERSION>@(#) Id: GERALD.pl,v 1.68.2.2 2007/06/13 11:08:49 km Exp</SOFTWARE_VERSION>
  <TILE_REGEX>s_[1-8]_[0-9][0-9][0-9][0-9]</TILE_REGEX>
  <TILE_ROOT>s</TILE_ROOT>
  <TIME_STAMP>Sat Apr 19 19:08:30 2008</TIME_STAMP>
  <TOOLS_DIR>/home/diane/proj/SolexaPipeline-0.2.2.6/Goat/../Gerald</TOOLS_DIR>
  <USE_BASES>all</USE_BASES>
  <WEB_DIR_ROOT>http://host.domain.com/yourshare/</WEB_DIR_ROOT>
</ChipWideRunParameters>
<LaneSpecificRunParameters>
  <ANALYSIS>
    <s_1>eland</s_1>
    <s_2>eland</s_2>
    <s_3>eland</s_3>
    <s_4>eland</s_4>
    <s_5>eland</s_5>
    <s_6>eland</s_6>
    <s_7>eland</s_7>
    <s_8>eland</s_8>
  </ANALYSIS>
  <ELAND_GENOME>
    <s_1>/g/dm3</s_1>
    <s_2>/g/equcab1</s_2>
    <s_3>/g/equcab1</s_3>
    <s_4>/g/canfam2</s_4>
    <s_5>/g/hg18</s_5>
    <s_6>/g/hg18</s_6>
    <s_7>/g/hg18</s_7>
    <s_8>/g/hg18</s_8>
  </ELAND_GENOME>
  <READ_LENGTH>
    <s_1>32</s_1>
    <s_2>32</s_2>
    <s_3>32</s_3>
    <s_4>32</s_4>
    <s_5>32</s_5>
    <s_6>32</s_6>
    <s_7>32</s_7>
    <s_8>32</s_8>
  </READ_LENGTH>
  <USE_BASES>
    <s_1>YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY</s_1>
    <s_2>YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY</s_2>
    <s_3>YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY</s_3>
    <s_4>YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY</s_4>
    <s_5>YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY</s_5>
    <s_6>YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY</s_6>
    <s_7>YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY</s_7>
    <s_8>YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY</s_8>
  </USE_BASES>
</LaneSpecificRunParameters>
</RunParameters>
"""
    pathname = os.path.join(gerald_dir, 'config.xml')
    f = open(pathname,'w')
    f.write(config_xml)
    f.close()
    

def make_summary_htm(gerald_dir):
    summary_htm = """<!--RUN_TIME Mon Apr 21 11:52:25 2008 -->
<!--SOFTWARE_VERSION @(#) $Id: jerboa.pl,v 1.31 2007/03/05 17:52:15 km Exp $-->
<html>
<body>

<a name="Top"><h2><title>080416_HWI-EAS229_0024_207BTAAXX Summary</title></h2></a>
<h1>Summary Information For Experiment 080416_HWI-EAS229_0024_207BTAAXX on Machine HWI-EAS229</h1>
<h2><br></br>Chip Summary<br></br></h2>
<table border="1" cellpadding="5">
<tr><td>Machine</td><td>HWI-EAS229</td></tr>
<tr><td>Run Folder</td><td>080416_HWI-EAS229_0024_207BTAAXX</td></tr>
<tr><td>Chip ID</td><td>unknown</td></tr>
</table>
<h2><br></br>Lane Parameter Summary<br></br></h2>
<table border="1" cellpadding="5">
<tr>
<td>Lane</td>
<td>Sample ID</td>
<td>Sample Target</td>
<td>Sample Type</td>
<td>Length</td>
<td>Filter</td>
<td>Tiles</td>
</tr>
<tr>
<td>1</td>
<td>unknown</td>
<td>dm3</td>
<td>ELAND</td>
<td>32</td>
<td>'((CHASTITY>=0.6))'</td>
<td><a href="#Lane1">Lane 1</a></td>
</tr>
<tr>
<td>2</td>
<td>unknown</td>
<td>equcab1</td>
<td>ELAND</td>
<td>32</td>
<td>'((CHASTITY>=0.6))'</td>
<td><a href="#Lane2">Lane 2</a></td>
</tr>
<tr>
<td>3</td>
<td>unknown</td>
<td>equcab1</td>
<td>ELAND</td>
<td>32</td>
<td>'((CHASTITY>=0.6))'</td>
<td><a href="#Lane3">Lane 3</a></td>
</tr>
<tr>
<td>4</td>
<td>unknown</td>
<td>canfam2</td>
<td>ELAND</td>
<td>32</td>
<td>'((CHASTITY>=0.6))'</td>
<td><a href="#Lane4">Lane 4</a></td>
</tr>
<tr>
<td>5</td>
<td>unknown</td>
<td>hg18</td>
<td>ELAND</td>
<td>32</td>
<td>'((CHASTITY>=0.6))'</td>
<td><a href="#Lane5">Lane 5</a></td>
</tr>
<tr>
<td>6</td>
<td>unknown</td>
<td>hg18</td>
<td>ELAND</td>
<td>32</td>
<td>'((CHASTITY>=0.6))'</td>
<td><a href="#Lane6">Lane 6</a></td>
</tr>
<tr>
<td>7</td>
<td>unknown</td>
<td>hg18</td>
<td>ELAND</td>
<td>32</td>
<td>'((CHASTITY>=0.6))'</td>
<td><a href="#Lane7">Lane 7</a></td>
</tr>
<tr>
<td>8</td>
<td>unknown</td>
<td>hg18</td>
<td>ELAND</td>
<td>32</td>
<td>'((CHASTITY>=0.6))'</td>
<td><a href="#Lane8">Lane 8</a></td>
</tr>
</table>
<h2><br></br>Lane Results Summary<br></br></h2>
<table border="1" cellpadding="5">
<tr>

<td>Lane </td>
<td>Clusters </td>
<td>Av 1st Cycle Int </td>
<td>% intensity after 20 cycles </td>
<td>% PF Clusters </td>
<td>% Align (PF) </td>
<td>Av Alignment Score (PF) </td>
<td> % Error Rate (PF) </td>
</tr>
<tr>
<td>1</td>
<td>17421 +/- 2139</td>
<td>7230 +/- 801</td>
<td>23.73 +/- 10.79</td>
<td>13.00 +/- 22.91</td>
<td>32.03 +/- 18.45</td>
<td>6703.57 +/- 3753.85</td>
<td>4.55 +/- 4.81</td>
</tr>
<tr>
<td>2</td>
<td>20311 +/- 2402</td>
<td>7660 +/- 678</td>
<td>17.03 +/- 4.40</td>
<td>40.74 +/- 30.33</td>
<td>29.54 +/- 9.03</td>
<td>5184.02 +/- 1631.54</td>
<td>3.27 +/- 3.94</td>
</tr>
<tr>
<td>3</td>
<td>20193 +/- 2399</td>
<td>7700 +/- 797</td>
<td>15.75 +/- 3.30</td>
<td>56.56 +/- 17.16</td>
<td>27.33 +/- 7.48</td>
<td>4803.49 +/- 1313.31</td>
<td>3.07 +/- 2.86</td>
</tr>
<tr>
<td>4</td>
<td>15537 +/- 2531</td>
<td>7620 +/- 1392</td>
<td>15.37 +/- 3.79</td>
<td>63.05 +/- 18.30</td>
<td>15.88 +/- 4.99</td>
<td>3162.13 +/- 962.59</td>
<td>3.11 +/- 2.22</td>
</tr>
<tr>
<td>5</td>
<td>32047 +/- 3356</td>
<td>8093 +/- 831</td>
<td>23.79 +/- 6.18</td>
<td>53.36 +/- 18.06</td>
<td>48.04 +/- 13.77</td>
<td>9866.23 +/- 2877.30</td>
<td>2.26 +/- 1.16</td>
</tr>
<tr>
<td>6</td>
<td>32946 +/- 4753</td>
<td>8227 +/- 736</td>
<td>24.07 +/- 4.69</td>
<td>54.65 +/- 12.57</td>
<td>50.98 +/- 10.54</td>
<td>10468.86 +/- 2228.53</td>
<td>2.21 +/- 2.33</td>
</tr>
<tr>
<td>7</td>
<td>39504 +/- 4171</td>
<td>8401 +/- 785</td>
<td>22.55 +/- 4.56</td>
<td>45.22 +/- 10.34</td>
<td>48.41 +/- 9.67</td>
<td>9829.40 +/- 1993.20</td>
<td>2.26 +/- 1.11</td>
</tr>
<tr>
<td>8</td>
<td>37998 +/- 3792</td>
<td>8443 +/- 1211</td>
<td>39.03 +/- 7.52</td>
<td>42.16 +/- 12.35</td>
<td>40.98 +/- 14.89</td>
<td>8128.87 +/- 3055.34</td>
<td>3.57 +/- 2.77</td>
</tr>
</table>
</body>
</html>
"""
    pathname = os.path.join(gerald_dir, 'Summary.htm')
    f = open(pathname, 'w')
    f.write(summary_htm)
    f.close()

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
                     
class RunfolderTests(unittest.TestCase):
    """
    Test components of the runfolder processing code
    which includes firecrest, bustard, and gerald
    """
    def setUp(self):
        # make a fake runfolder directory
        self.temp_dir = tempfile.mkdtemp(prefix='tmp_runfolder_')

        self.runfolder_dir = os.path.join(self.temp_dir, 
                                          '080102_HWI-EAS229_0010_207BTAAXX')
        os.mkdir(self.runfolder_dir)

        self.data_dir = os.path.join(self.runfolder_dir, 'Data')
        os.mkdir(self.data_dir)

        self.firecrest_dir = os.path.join(self.data_dir, 
                               'C1-33_Firecrest1.8.28_12-04-2008_diane'
                             )
        os.mkdir(self.firecrest_dir)
        self.matrix_dir = os.path.join(self.firecrest_dir, 'Matrix')
        os.mkdir(self.matrix_dir)
        make_matrix(self.matrix_dir)

        self.bustard_dir = os.path.join(self.firecrest_dir, 
                                        'Bustard1.8.28_12-04-2008_diane')
        os.mkdir(self.bustard_dir)
        make_phasing_params(self.bustard_dir)
        
        self.gerald_dir = os.path.join(self.bustard_dir,
                                       'GERALD_12-04-2008_diane')
        os.mkdir(self.gerald_dir)
        make_gerald_config(self.gerald_dir)
        make_summary_htm(self.gerald_dir)
        make_eland_results(self.gerald_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_firecrest(self):
        """
        Construct a firecrest object
        """
        f = firecrest.firecrest(self.firecrest_dir)
        self.failUnlessEqual(f.version, '1.8.28')
        self.failUnlessEqual(f.start, 1)
        self.failUnlessEqual(f.stop, 33)
        self.failUnlessEqual(f.user, 'diane')
        self.failUnlessEqual(f.date, date(2008,4,12))

        xml = f.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)

        f2 = firecrest.Firecrest(xml=xml)
        self.failUnlessEqual(f.version, f2.version)
        self.failUnlessEqual(f.start,   f2.start)
        self.failUnlessEqual(f.stop,    f2.stop)
        self.failUnlessEqual(f.user,    f2.user)
        self.failUnlessEqual(f.date,    f2.date)

    def test_bustard(self):
        """
        construct a bustard object
        """
        b = bustard.bustard(self.bustard_dir)
        self.failUnlessEqual(b.version, '1.8.28')
        self.failUnlessEqual(b.date,    date(2008,4,12))
        self.failUnlessEqual(b.user,    'diane')
        self.failUnlessEqual(len(b.phasing), 8)
        self.failUnlessAlmostEqual(b.phasing[8].phasing, 0.0099)
        
        xml = b.get_elements()
        b2 = bustard.Bustard(xml=xml)
        self.failUnlessEqual(b.version, b2.version)
        self.failUnlessEqual(b.date,    b2.date )
        self.failUnlessEqual(b.user,    b2.user)
        self.failUnlessEqual(len(b.phasing), len(b2.phasing))
        for key in b.phasing.keys():
            self.failUnlessEqual(b.phasing[key].lane, 
                                 b2.phasing[key].lane)
            self.failUnlessEqual(b.phasing[key].phasing, 
                                 b2.phasing[key].phasing)
            self.failUnlessEqual(b.phasing[key].prephasing, 
                                 b2.phasing[key].prephasing)

    def test_gerald(self):
        # need to update gerald and make tests for it
        g = gerald.gerald(self.gerald_dir) 

        self.failUnlessEqual(g.version, 
            '@(#) Id: GERALD.pl,v 1.68.2.2 2007/06/13 11:08:49 km Exp')
        self.failUnlessEqual(g.date, datetime(2008,4,19,19,8,30))
        self.failUnlessEqual(len(g.lanes), len(g.lanes.keys()))
        self.failUnlessEqual(len(g.lanes), len(g.lanes.items()))

        
        # list of genomes, matches what was defined up in 
        # make_gerald_config.
        # the first None is to offset the genomes list to be 1..9
        # instead of pythons default 0..8
        genomes = [None, '/g/dm3', '/g/equcab1', '/g/equcab1', '/g/canfam2',
                         '/g/hg18', '/g/hg18', '/g/hg18', '/g/hg18', ]

        # test lane specific parameters from gerald config file
        for i in range(1,9):
            cur_lane = g.lanes[str(i)]
            self.failUnlessEqual(cur_lane.analysis, 'eland')
            self.failUnlessEqual(cur_lane.eland_genome, genomes[i])
            self.failUnlessEqual(cur_lane.read_length, '32')
            self.failUnlessEqual(cur_lane.use_bases, 'Y'*32)

        # test data extracted from summary file
        clusters = [None, 
                    (17421, 2139), (20311, 2402), (20193, 2399), (15537, 2531),
                    (32047, 3356), (32946, 4753), (39504, 4171), (37998, 3792)]

        for i in range(1,9):
            summary_lane = g.summary[str(i)]
            self.failUnlessEqual(summary_lane.cluster, clusters[i])
            self.failUnlessEqual(summary_lane.lane, str(i))

        xml = g.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        g2 = gerald.Gerald(xml=xml)

        # do it all again after extracting from the xml file
        self.failUnlessEqual(g.version, g2.version)
        self.failUnlessEqual(g.date, g2.date)
        self.failUnlessEqual(len(g.lanes.keys()), len(g2.lanes.keys()))
        self.failUnlessEqual(len(g.lanes.items()), len(g2.lanes.items()))

        # test lane specific parameters from gerald config file
        for i in range(1,9):
            g_lane = g.lanes[str(i)]
            g2_lane = g2.lanes[str(i)]
            self.failUnlessEqual(g_lane.analysis, g2_lane.analysis)
            self.failUnlessEqual(g_lane.eland_genome, g2_lane.eland_genome)
            self.failUnlessEqual(g_lane.read_length, g2_lane.read_length)
            self.failUnlessEqual(g_lane.use_bases, g2_lane.use_bases)

        # test (some) summary elements
        for i in range(1,9):
            g_summary = g.summary[str(i)]
            g2_summary = g2.summary[str(i)]
            self.failUnlessEqual(g_summary.cluster, g2_summary.cluster)
            self.failUnlessEqual(g_summary.lane, g2_summary.lane)

            g_eland = g.eland_results
            g2_eland = g2.eland_results
            for lane in g_eland.keys():
                self.failUnlessEqual(g_eland[lane].reads, 
                                     g2_eland[lane].reads)
                self.failUnlessEqual(len(g_eland[lane].mapped_reads), 
                                     len(g2_eland[lane].mapped_reads))
                for k in g_eland[lane].mapped_reads.keys():
                    self.failUnlessEqual(g_eland[lane].mapped_reads[k],
                                         g2_eland[lane].mapped_reads[k])

                self.failUnlessEqual(len(g_eland[lane].match_codes), 
                                     len(g2_eland[lane].match_codes))
                for k in g_eland[lane].match_codes.keys():
                    self.failUnlessEqual(g_eland[lane].match_codes[k],
                                         g2_eland[lane].match_codes[k])


    def test_eland(self):
        dm3_map = { 'chrUextra.fa' : 'dm3/chrUextra.fa',
                    'chr2L.fa': 'dm3/chr2L.fa',
                    'Lambda.fa': 'Lambda.fa'}
        genome_maps = { '1':dm3_map, '2':dm3_map, '3':dm3_map, '4':dm3_map,
                        '5':dm3_map, '6':dm3_map, '7':dm3_map, '8':dm3_map }
        eland = gerald.eland(self.gerald_dir, genome_maps=genome_maps)
        
        for i in range(1,9):
            lane = eland[str(i)]
            self.failUnlessEqual(lane.reads, 4)
            self.failUnlessEqual(len(lane.mapped_reads), 3)
            self.failUnlessEqual(lane.mapped_reads['Lambda.fa'], 1)
            self.failUnlessEqual(lane.mapped_reads['dm3/chr2L.fa'], 1)
            self.failUnlessEqual(lane.match_codes['U1'], 2)
            self.failUnlessEqual(lane.match_codes['NM'], 1)

        xml = eland.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        e2 = gerald.ELAND(xml=xml)

        for i in range(1,9):
            l1 = eland[str(i)]
            l2 = e2[str(i)]
            self.failUnlessEqual(l1.reads, l2.reads)
            self.failUnlessEqual(len(l1.mapped_reads), len(l2.mapped_reads))
            self.failUnlessEqual(len(l1.mapped_reads), 3)
            for k in l1.mapped_reads.keys():
                self.failUnlessEqual(l1.mapped_reads[k],
                                     l2.mapped_reads[k])

            self.failUnlessEqual(len(l1.match_codes), 9)
            self.failUnlessEqual(len(l1.match_codes), len(l2.match_codes))
            for k in l1.match_codes.keys():
                self.failUnlessEqual(l1.match_codes[k], 
                                     l2.match_codes[k])

    def test_runfolder(self):
        runs = runfolder.get_runs(self.runfolder_dir)
        
        # do we get the flowcell id from the filename?
        self.failUnlessEqual(len(runs), 1)
        self.failUnlessEqual(runs[0].name, 'run_207BTAAXX_2008-04-19.xml')

        # do we get the flowcell id from the FlowcellId.xml file
        make_flowcell_id(self.runfolder_dir, '207BTAAXY')
        runs = runfolder.get_runs(self.runfolder_dir)
        self.failUnlessEqual(len(runs), 1)
        self.failUnlessEqual(runs[0].name, 'run_207BTAAXY_2008-04-19.xml')
        
        r1 = runs[0]
        xml = r1.get_elements()
        xml_str = ElementTree.tostring(xml)

        r2 = runfolder.PipelineRun(xml=xml)
        self.failUnlessEqual(r1.name, r2.name)
        self.failIfEqual(r2.firecrest, None)
        self.failIfEqual(r2.bustard, None)
        self.failIfEqual(r2.gerald, None)
        

def suite():
    return unittest.makeSuite(RunfolderTests,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
    
