"""
Create simulated solexa/illumina runfolders for testing
"""

import os


def make_ipar_dir(data_dir):
    """
    Construct an artificial ipar parameter file and directory
    """
    params = """<?xml version="1.0"?>
<ImageAnalysis>
  <Run Name="IPAR_1.01">
    <Software Name="IPAR" Version="2.01.192.0" />
    <Cycles First="1" Last="37" Number="37" />
    <RunParameters>
      <ImagingReads Index="1">
        <FirstCycle>1</FirstCycle>
        <LastCycle>37</LastCycle>
        <RunFolder>081021_HWI-EAS229_0063_30HKUAAXX</RunFolder>
      </ImagingReads>
      <Reads Index="1">
        <FirstCycle>1</FirstCycle>
        <LastCycle>37</LastCycle>
        <RunFolder>081021_HWI-EAS229_0063_30HKUAAXX</RunFolder>
      </Reads>
      <Compression>gzip</Compression>
      <CompressionSuffix>.p.gz</CompressionSuffix>
      <Instrument>HWI-EAS229</Instrument>
      <RunFolder>081021_HWI-EAS229_0063_30HKUAAXX</RunFolder>
    </RunParameters>
    <ImageParameters>
      <AutoOffsetFlag>1</AutoOffsetFlag>
      <Fwhm>2.7</Fwhm>
      <RemappingDistance>1.5</RemappingDistance>
      <Threshold>4</Threshold>
    </ImageParameters>
    <TileSelection>
      <Lane Index="1">
        <Sample>s</Sample>
        <TileRange Max="100" Min="1" />
      </Lane>
      <Lane Index="2">
        <Sample>s</Sample>
        <TileRange Max="100" Min="1" />
      </Lane>
      <Lane Index="3">
        <Sample>s</Sample>
        <TileRange Max="100" Min="1" />
      </Lane>
      <Lane Index="4">
        <Sample>s</Sample>
        <TileRange Max="100" Min="1" />
      </Lane>
      <Lane Index="5">
        <Sample>s</Sample>
        <TileRange Max="100" Min="1" />
      </Lane>
      <Lane Index="6">
        <Sample>s</Sample>
        <TileRange Max="100" Min="1" />
      </Lane>
      <Lane Index="7">
        <Sample>s</Sample>
        <TileRange Max="100" Min="1" />
      </Lane>
      <Lane Index="8">
        <Sample>s</Sample>
        <TileRange Max="100" Min="1" />
      </Lane>
    </TileSelection>
  </Run>
</ImageAnalysis>
"""
    f = open(os.path.join(data_dir, '.params'),'w')
    f.write(params)
    f.close()
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

def make_summary100_htm(gerald_dir):
    summary_htm="""<!--RUN_TIME Wed Jul  2 06:47:44 2008 -->
<!--SOFTWARE_VERSION @(#) $Id: jerboa.pl,v 1.94 2007/12/04 09:59:07 rshaw Exp $-->
<html>
<body>

<a name="Top"><h2><title>080627_HWI-EAS229_0036_3055HAXX Summary</title></h2></a>
<h1>Summary Information For Experiment 080627_HWI-EAS229_0036_3055HAXX on Machine HWI-EAS229</h1>
<h2><br></br>Chip Summary<br></br></h2>
<table border="1" cellpadding="5">
<tr><td>Machine</td><td>HWI-EAS229</td></tr>
<tr><td>Run Folder</td><td>080627_HWI-EAS229_0036_3055HAXX</td></tr>
<tr><td>Chip ID</td><td>unknown</td></tr>
</table>
<h2><br></br>Chip Results Summary<br></br></h2>
<table border="1" cellpadding="5">
<tr>
<td>Clusters</td>
<td>Clusters (PF)</td>
<td>Yield (kbases)</td>
</tr>
<tr><td>80933224</td>
<td>43577803</td>
<td>1133022</td>
</tr>
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
<td>Num Tiles</td>
<td>Tiles</td>
</tr>
<tr>
<td>1</td>
<td>unknown</td>
<td>mm9</td>
<td>ELAND</td>
<td>26</td>
<td>'((CHASTITY>=0.6))'</td>
<td>100</td>
<td><a href="#Lane1">Lane 1</a></td>
</tr>
<tr>
<td>2</td>
<td>unknown</td>
<td>mm9</td>
<td>ELAND</td>
<td>26</td>
<td>'((CHASTITY>=0.6))'</td>
<td>100</td>
<td><a href="#Lane2">Lane 2</a></td>
</tr>
<tr>
<td>3</td>
<td>unknown</td>
<td>mm9</td>
<td>ELAND</td>
<td>26</td>
<td>'((CHASTITY>=0.6))'</td>
<td>100</td>
<td><a href="#Lane3">Lane 3</a></td>
</tr>
<tr>
<td>4</td>
<td>unknown</td>
<td>elegans170</td>
<td>ELAND</td>
<td>26</td>
<td>'((CHASTITY>=0.6))'</td>
<td>100</td>
<td><a href="#Lane4">Lane 4</a></td>
</tr>
<tr>
<td>5</td>
<td>unknown</td>
<td>elegans170</td>
<td>ELAND</td>
<td>26</td>
<td>'((CHASTITY>=0.6))'</td>
<td>100</td>
<td><a href="#Lane5">Lane 5</a></td>
</tr>
<tr>
<td>6</td>
<td>unknown</td>
<td>elegans170</td>
<td>ELAND</td>
<td>26</td>
<td>'((CHASTITY>=0.6))'</td>
<td>100</td>
<td><a href="#Lane6">Lane 6</a></td>
</tr>
<tr>
<td>7</td>
<td>unknown</td>
<td>elegans170</td>
<td>ELAND</td>
<td>26</td>
<td>'((CHASTITY>=0.6))'</td>
<td>100</td>
<td><a href="#Lane7">Lane 7</a></td>
</tr>
<tr>
<td>8</td>
<td>unknown</td>
<td>elegans170</td>
<td>ELAND</td>
<td>26</td>
<td>'((CHASTITY>=0.6))'</td>
<td>100</td>
<td><a href="#Lane8">Lane 8</a></td>
</tr>
</table>
<h2><br></br>Lane Results Summary<br></br></h2>
<table border="1" cellpadding="5">
<tr>
<td colspan="2">Lane Info</td>
<td colspan="8">Tile Mean +/- SD for Lane</td>
</tr>
<tr>
<td>Lane </td>
<td>Lane Yield (kbases) </td>
<td>Clusters (raw)</td>
<td>Clusters (PF) </td>
<td>1st Cycle Int (PF) </td>
<td>% intensity after 20 cycles (PF) </td>
<td>% PF Clusters </td>
<td>% Align (PF) </td>
<td>Alignment Score (PF) </td>
<td> % Error Rate (PF) </td>
</tr>
<tr>
<td>1</td>
<td>158046</td>
<td>96483 +/- 9074</td>
<td>60787 +/- 4240</td>
<td>329 +/- 35</td>
<td>101.88 +/- 6.03</td>
<td>63.21 +/- 3.29</td>
<td>70.33 +/- 0.24</td>
<td>9054.08 +/- 59.16</td>
<td>0.46 +/- 0.18</td>
</tr>
<tr>
<td>2</td>
<td>156564</td>
<td>133738 +/- 7938</td>
<td>60217 +/- 1926</td>
<td>444 +/- 39</td>
<td>92.62 +/- 7.58</td>
<td>45.20 +/- 3.31</td>
<td>51.98 +/- 0.74</td>
<td>6692.04 +/- 92.49</td>
<td>0.46 +/- 0.09</td>
</tr>
<tr>
<td>3</td>
<td>185818</td>
<td>152142 +/- 10002</td>
<td>71468 +/- 2827</td>
<td>366 +/- 36</td>
<td>91.53 +/- 8.66</td>
<td>47.19 +/- 3.80</td>
<td>82.24 +/- 0.44</td>
<td>10598.68 +/- 64.13</td>
<td>0.41 +/- 0.04</td>
</tr>
<tr>
<td>4</td>
<td>34953</td>
<td>15784 +/- 2162</td>
<td>13443 +/- 1728</td>
<td>328 +/- 40</td>
<td>97.53 +/- 9.87</td>
<td>85.29 +/- 1.91</td>
<td>80.02 +/- 0.53</td>
<td>10368.82 +/- 71.08</td>
<td>0.15 +/- 0.05</td>
</tr>
<tr>
<td>5</td>
<td>167936</td>
<td>119735 +/- 8465</td>
<td>64590 +/- 2529</td>
<td>417 +/- 37</td>
<td>88.69 +/- 14.79</td>
<td>54.10 +/- 2.59</td>
<td>76.95 +/- 0.32</td>
<td>9936.47 +/- 65.75</td>
<td>0.28 +/- 0.02</td>
</tr>
<tr>
<td>6</td>
<td>173463</td>
<td>152177 +/- 8146</td>
<td>66716 +/- 2493</td>
<td>372 +/- 39</td>
<td>87.06 +/- 9.86</td>
<td>43.98 +/- 3.12</td>
<td>78.80 +/- 0.43</td>
<td>10162.28 +/- 49.65</td>
<td>0.38 +/- 0.03</td>
</tr>
<tr>
<td>7</td>
<td>149287</td>
<td>84649 +/- 7325</td>
<td>57418 +/- 3617</td>
<td>295 +/- 28</td>
<td>89.40 +/- 8.23</td>
<td>67.97 +/- 1.82</td>
<td>33.38 +/- 0.25</td>
<td>4247.92 +/- 32.37</td>
<td>1.00 +/- 0.03</td>
</tr>
<tr>
<td>8</td>
<td>106953</td>
<td>54622 +/- 4812</td>
<td>41136 +/- 3309</td>
<td>284 +/- 37</td>
<td>90.21 +/- 9.10</td>
<td>75.39 +/- 2.27</td>
<td>48.33 +/- 0.29</td>
<td>6169.21 +/- 169.50</td>
<td>0.86 +/- 1.22</td>
</tr>
<tr><td colspan="13">Tile mean across chip</td></tr>
<tr>
<td>Av.</td>
<td></td>
<td>101166</td>
<td>54472</td>
<td>354</td>
<td>92.36</td>
<td>60.29</td>
<td>65.25</td>
<td>8403.69</td>
<td>0.50</td>
</tr>
</table>
<h2><br></br>Expanded Lane Summary<br></br></h2>
<table border="1" cellpadding="5">
<tr>

<tr><td colspan="2">Lane Info</td>
<td colspan="2">Phasing Info</td>
<td colspan="2">Raw Data (tile mean)</td>
<td colspan="7">Filtered Data (tile mean)</td></tr>
<td>Lane </td>
<td>Clusters (tile mean) (raw)</td>
<td>% Phasing </td>
<td>% Prephasing </td>
<td>% Error Rate (raw) </td>
<td> Equiv Perfect Clusters (raw) </td>
<td>% retained </td>
<td>Cycle 2-4 Av Int (PF) </td>
<td>Cycle 2-10 Av % Loss (PF) </td>
<td>Cycle 10-20 Av % Loss (PF) </td>
<td>% Align (PF) </td>
<td>% Error Rate (PF) </td>
<td> Equiv Perfect Clusters (PF) </td>
</tr>
<tr>
<td>1</td>
<td>96483</td>
<td>0.7700</td>
<td>0.3100</td>
<td>1.00</td>
<td>49676</td>
<td>63.21</td>
<td>317 +/- 32</td>
<td>0.13 +/- 0.44</td>
<td>-1.14 +/- 0.34</td>
<td>70.33</td>
<td>0.46</td>
<td>41758</td>
</tr>
<tr>
<td>2</td>
<td>133738</td>
<td>0.7700</td>
<td>0.3100</td>
<td>1.22</td>
<td>40467</td>
<td>45.20</td>
<td>415 +/- 33</td>
<td>0.29 +/- 0.40</td>
<td>-0.79 +/- 0.35</td>
<td>51.98</td>
<td>0.46</td>
<td>30615</td>
</tr>
<tr>
<td>3</td>
<td>152142</td>
<td>0.7700</td>
<td>0.3100</td>
<td>1.30</td>
<td>78588</td>
<td>47.19</td>
<td>344 +/- 26</td>
<td>0.68 +/- 0.51</td>
<td>-0.77 +/- 0.42</td>
<td>82.24</td>
<td>0.41</td>
<td>57552</td>
</tr>
<tr>
<td>4</td>
<td>15784</td>
<td>0.7700</td>
<td>0.3100</td>
<td>0.29</td>
<td>11095</td>
<td>85.29</td>
<td>306 +/- 34</td>
<td>0.20 +/- 0.69</td>
<td>-1.28 +/- 0.66</td>
<td>80.02</td>
<td>0.15</td>
<td>10671</td>
</tr>
<tr>
<td>5</td>
<td>119735</td>
<td>0.7700</td>
<td>0.3100</td>
<td>0.85</td>
<td>60335</td>
<td>54.10</td>
<td>380 +/- 32</td>
<td>0.34 +/- 0.49</td>
<td>-1.55 +/- 4.69</td>
<td>76.95</td>
<td>0.28</td>
<td>49015</td>
</tr>
<tr>
<td>6</td>
<td>152177</td>
<td>0.7700</td>
<td>0.3100</td>
<td>1.21</td>
<td>70905</td>
<td>43.98</td>
<td>333 +/- 27</td>
<td>0.57 +/- 0.50</td>
<td>-0.91 +/- 0.39</td>
<td>78.80</td>
<td>0.38</td>
<td>51663</td>
</tr>
<tr>
<td>7</td>
<td>84649</td>
<td>0.7700</td>
<td>0.3100</td>
<td>1.38</td>
<td>21069</td>
<td>67.97</td>
<td>272 +/- 20</td>
<td>1.15 +/- 0.52</td>
<td>-0.84 +/- 0.58</td>
<td>33.38</td>
<td>1.00</td>
<td>18265</td>
</tr>
<tr>
<td>8</td>
<td>54622</td>
<td>0.7700</td>
<td>0.3100</td>
<td>1.17</td>
<td>21335</td>
<td>75.39</td>
<td>262 +/- 31</td>
<td>1.10 +/- 0.59</td>
<td>-1.01 +/- 0.47</td>
<td>48.33</td>
<td>0.86</td>
<td>19104</td>
</tr>
</table>
<b><br></br>IVC Plots</b>
<p> <a href='IVC.htm' target="_blank"> IVC.htm
 </a></p>
<b><br></br>All Intensity Plots</b>
<p> <a href='All.htm' target="_blank"> All.htm
 </a></p>
<b><br></br>Error graphs: </b>
<p> <a href='Error.htm' target="_blank"> Error.htm
 </a></p>
<td><a href="#Top">Back to top</a></td>
<a name="Lane1"><h2><br></br>Lane 1<br></br></h2></a>
<table border="1" cellpadding="5">
<tr>
<td>Lane </td>
<td>Tile </td>
<td>Clusters (raw)</td>
<td>Av 1st Cycle Int (PF) </td>
<td>Av % intensity after 20 cycles (PF) </td>
<td>% PF Clusters </td>
<td>% Align (PF) </td>
<td>Av Alignment Score (PF) </td>
<td>% Error Rate (PF) </td>
</tr>
<tr>
<td>1</td>
<td>0001</td>
<td>114972</td>
<td>326.48</td>
<td>94.39</td>
<td>57.44</td>
<td>70.2</td>
<td>9038.6</td>
<td>0.44</td>
</tr>
</table>
<td><a href="#Top">Back to top</a></td>
<a name="Lane2"><h2><br></br>Lane 2<br></br></h2></a>
<table border="1" cellpadding="5">
<tr>
<td>Lane </td>
<td>Tile </td>
<td>Clusters (raw)</td>
<td>Av 1st Cycle Int (PF) </td>
<td>Av % intensity after 20 cycles (PF) </td>
<td>% PF Clusters </td>
<td>% Align (PF) </td>
<td>Av Alignment Score (PF) </td>
<td>% Error Rate (PF) </td>
</tr>
<tr>
<td>2</td>
<td>0001</td>
<td>147793</td>
<td>448.12</td>
<td>83.68</td>
<td>38.57</td>
<td>53.7</td>
<td>6905.4</td>
<td>0.54</td>
</tr>
</table>
<td><a href="#Top">Back to top</a></td>
<a name="Lane3"><h2><br></br>Lane 3<br></br></h2></a>
<table border="1" cellpadding="5">
<tr>
<td>Lane </td>
<td>Tile </td>
<td>Clusters (raw)</td>
<td>Av 1st Cycle Int (PF) </td>
<td>Av % intensity after 20 cycles (PF) </td>
<td>% PF Clusters </td>
<td>% Align (PF) </td>
<td>Av Alignment Score (PF) </td>
<td>% Error Rate (PF) </td>
</tr>
<tr>
<td>3</td>
<td>0001</td>
<td>167904</td>
<td>374.05</td>
<td>86.91</td>
<td>40.36</td>
<td>81.3</td>
<td>10465.0</td>
<td>0.47</td>
</tr>
</table>
<td><a href="#Top">Back to top</a></td>
<a name="Lane4"><h2><br></br>Lane 4<br></br></h2></a>
<table border="1" cellpadding="5">
<tr>
<td>Lane </td>
<td>Tile </td>
<td>Clusters (raw)</td>
<td>Av 1st Cycle Int (PF) </td>
<td>Av % intensity after 20 cycles (PF) </td>
<td>% PF Clusters </td>
<td>% Align (PF) </td>
<td>Av Alignment Score (PF) </td>
<td>% Error Rate (PF) </td>
</tr>
<tr>
<td>4</td>
<td>0001</td>
<td>20308</td>
<td>276.85</td>
<td>92.87</td>
<td>84.26</td>
<td>80.4</td>
<td>10413.8</td>
<td>0.16</td>
</tr>
</table>
<td><a href="#Top">Back to top</a></td>
<a name="Lane5"><h2><br></br>Lane 5<br></br></h2></a>
<table border="1" cellpadding="5">
<tr>
<td>Lane </td>
<td>Tile </td>
<td>Clusters (raw)</td>
<td>Av 1st Cycle Int (PF) </td>
<td>Av % intensity after 20 cycles (PF) </td>
<td>% PF Clusters </td>
<td>% Align (PF) </td>
<td>Av Alignment Score (PF) </td>
<td>% Error Rate (PF) </td>
</tr>
</table>
<td><a href="#Top">Back to top</a></td>
<a name="Lane6"><h2><br></br>Lane 6<br></br></h2></a>
<table border="1" cellpadding="5">
<tr>
<td>Lane </td>
<td>Tile </td>
<td>Clusters (raw)</td>
<td>Av 1st Cycle Int (PF) </td>
<td>Av % intensity after 20 cycles (PF) </td>
<td>% PF Clusters </td>
<td>% Align (PF) </td>
<td>Av Alignment Score (PF) </td>
<td>% Error Rate (PF) </td>
</tr>
<tr>
<td>6</td>
<td>0001</td>
<td>166844</td>
<td>348.12</td>
<td>77.59</td>
<td>38.13</td>
<td>79.7</td>
<td>10264.4</td>
<td>0.44</td>
</tr>
</table>
<td><a href="#Top">Back to top</a></td>
<a name="Lane7"><h2><br></br>Lane 7<br></br></h2></a>
<table border="1" cellpadding="5">
<tr>
<td>Lane </td>
<td>Tile </td>
<td>Clusters (raw)</td>
<td>Av 1st Cycle Int (PF) </td>
<td>Av % intensity after 20 cycles (PF) </td>
<td>% PF Clusters </td>
<td>% Align (PF) </td>
<td>Av Alignment Score (PF) </td>
<td>% Error Rate (PF) </td>
</tr>
<tr>
<td>7</td>
<td>0001</td>
<td>98913</td>
<td>269.90</td>
<td>86.66</td>
<td>64.55</td>
<td>33.2</td>
<td>4217.5</td>
<td>1.02</td>
</tr>
</table>
<td><a href="#Top">Back to top</a></td>
<a name="Lane8"><h2><br></br>Lane 8<br></br></h2></a>
<table border="1" cellpadding="5">
<tr>
<td>Lane </td>
<td>Tile </td>
<td>Clusters (raw)</td>
<td>Av 1st Cycle Int (PF) </td>
<td>Av % intensity after 20 cycles (PF) </td>
<td>% PF Clusters </td>
<td>% Align (PF) </td>
<td>Av Alignment Score (PF) </td>
<td>% Error Rate (PF) </td>
</tr>
<tr>
<td>8</td>
<td>0001</td>
<td>64972</td>
<td>243.60</td>
<td>89.40</td>
<td>73.17</td>
<td>48.3</td>
<td>6182.8</td>
<td>0.71</td>
</tr>
</table>
<td><a href="#Top">Back to top</a></td>
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
