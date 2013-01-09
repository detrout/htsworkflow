#!/usr/bin/env python

from datetime import datetime, date
import os
import tempfile
import shutil
from unittest2 import TestCase

from htsworkflow.pipelines import firecrest
from htsworkflow.pipelines import bustard
from htsworkflow.pipelines import gerald
from htsworkflow.pipelines import runfolder
from htsworkflow.pipelines import ElementTree

from htsworkflow.pipelines.test.simulate_runfolder import *


def make_summary_htm(gerald_dir):
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

def make_runfolder(obj=None):
    """
    Make a fake runfolder, attach all the directories to obj if defined
    """
    # make a fake runfolder directory
    temp_dir = tempfile.mkdtemp(prefix='tmp_runfolder_')

    runfolder_dir = os.path.join(temp_dir,
                                 '080102_HWI-EAS229_0010_207BTAAXX')
    os.mkdir(runfolder_dir)

    data_dir = os.path.join(runfolder_dir, 'Data')
    os.mkdir(data_dir)

    firecrest_dir = os.path.join(data_dir,
                                 'C1-33_Firecrest1.8.28_12-04-2008_diane'
                                 )
    os.mkdir(firecrest_dir)
    matrix_dir = os.path.join(firecrest_dir, 'Matrix')
    os.mkdir(matrix_dir)
    matrix_filename = os.path.join(matrix_dir, 's_matrix.txt')
    make_matrix(matrix_filename)

    bustard_dir = os.path.join(firecrest_dir,
                               'Bustard1.8.28_12-04-2008_diane')
    os.mkdir(bustard_dir)
    make_phasing_params(bustard_dir)

    gerald_dir = os.path.join(bustard_dir,
                              'GERALD_12-04-2008_diane')
    os.mkdir(gerald_dir)
    make_gerald_config_026(gerald_dir)
    make_summary_htm(gerald_dir)
    make_eland_results(gerald_dir)

    if obj is not None:
        obj.temp_dir = temp_dir
        obj.runfolder_dir = runfolder_dir
        obj.data_dir = data_dir
        obj.firecrest_dir = firecrest_dir
        obj.matrix_dir = matrix_dir
        obj.bustard_dir = bustard_dir
        obj.gerald_dir = gerald_dir


class RunfolderTests(TestCase):
    """
    Test components of the runfolder processing code
    which includes firecrest, bustard, and gerald
    """
    def setUp(self):
        # attaches all the directories to the object passed in
        make_runfolder(self)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_firecrest(self):
        """
        Construct a firecrest object
        """
        f = firecrest.firecrest(self.firecrest_dir)
        self.failUnlessEqual(f.software, 'Firecrest')
        self.failUnlessEqual(f.version, '1.8.28')
        self.failUnlessEqual(f.start, 1)
        self.failUnlessEqual(f.stop, 33)
        self.failUnlessEqual(f.user, 'diane')
        self.failUnlessEqual(f.date, date(2008,4,12))

        xml = f.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)

        f2 = firecrest.Firecrest(xml=xml)
        self.failUnlessEqual(f.software, f2.software)
        self.failUnlessEqual(f.version,  f2.version)
        self.failUnlessEqual(f.start,    f2.start)
        self.failUnlessEqual(f.stop,     f2.stop)
        self.failUnlessEqual(f.user,     f2.user)
        self.failUnlessEqual(f.date,     f2.date)

    def test_bustard(self):
        """
        construct a bustard object
        """
        b = bustard.bustard(self.bustard_dir)
        self.failUnlessEqual(b.software, 'Bustard')
        self.failUnlessEqual(b.version, '1.8.28')
        self.failUnlessEqual(b.date,    date(2008,4,12))
        self.failUnlessEqual(b.user,    'diane')
        self.failUnlessEqual(len(b.phasing), 8)
        self.failUnlessAlmostEqual(b.phasing[8].phasing, 0.0099)

        xml = b.get_elements()
        b2 = bustard.Bustard(xml=xml)
        self.failUnlessEqual(b.software, b2.software)
        self.failUnlessEqual(b.version,  b2.version)
        self.failUnlessEqual(b.date,     b2.date )
        self.failUnlessEqual(b.user,     b2.user)
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

        self.failUnlessEqual(g.software, 'GERALD')
        self.failUnlessEqual(g.version, '1.68.2.2')
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
            cur_lane = g.lanes[i]
            self.failUnlessEqual(cur_lane.analysis, 'eland')
            self.failUnlessEqual(cur_lane.eland_genome, genomes[i])
            self.failUnlessEqual(cur_lane.read_length, '32')
            self.failUnlessEqual(cur_lane.use_bases, 'Y'*32)

        # test data extracted from summary file
        clusters = [None,
                    (96483, 9074), (133738, 7938),
                    (152142, 10002), (15784, 2162),
                    (119735, 8465), (152177, 8146),
                    (84649, 7325), (54622, 4812),]

        self.failUnlessEqual(len(g.summary), 1)
        for i in range(1,9):
            summary_lane = g.summary[0][i]
            self.failUnlessEqual(summary_lane.cluster, clusters[i])
            self.failUnlessEqual(summary_lane.lane, i)

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
            g_lane = g.lanes[i]
            g2_lane = g2.lanes[i]
            self.failUnlessEqual(g_lane.analysis, g2_lane.analysis)
            self.failUnlessEqual(g_lane.eland_genome, g2_lane.eland_genome)
            self.failUnlessEqual(g_lane.read_length, g2_lane.read_length)
            self.failUnlessEqual(g_lane.use_bases, g2_lane.use_bases)

        # test (some) summary elements
        self.failUnlessEqual(len(g.summary), 1)
        for i in range(1,9):
            g_summary = g.summary[0][i]
            g2_summary = g2.summary[0][i]
            self.failUnlessEqual(g_summary.cluster, g2_summary.cluster)
            self.failUnlessEqual(g_summary.lane, g2_summary.lane)

            g_eland = g.eland_results
            g2_eland = g2.eland_results
            for key in g_eland:
                g_results = g_eland[key]
                g2_results = g2_eland[key]
                self.failUnlessEqual(g_results.reads,
                                     g2_results.reads)
                self.failUnlessEqual(len(g_results.mapped_reads),
                                     len(g2_results.mapped_reads))
                for k in g_results.mapped_reads.keys():
                    self.failUnlessEqual(g_results.mapped_reads[k],
                                         g2_results.mapped_reads[k])

                self.failUnlessEqual(len(g_results.match_codes),
                                     len(g2_results.match_codes))
                for k in g_results.match_codes.keys():
                    self.failUnlessEqual(g_results.match_codes[k],
                                         g2_results.match_codes[k])


    def test_eland(self):
        dm3_map = { 'chrUextra.fa' : 'dm3/chrUextra.fa',
                    'chr2L.fa': 'dm3/chr2L.fa',
                    'Lambda.fa': 'Lambda.fa'}
        genome_maps = { 1:dm3_map, 2:dm3_map, 3:dm3_map, 4:dm3_map,
                        5:dm3_map, 6:dm3_map, 7:dm3_map, 8:dm3_map }
        eland = gerald.eland(self.gerald_dir, genome_maps=genome_maps)

        for key in eland:
            lane = eland[key]
            self.failUnlessEqual(lane.reads, 4)
            self.failUnlessEqual(lane.sample_name, "s")
            self.failUnlessEqual(lane.lane_id, key.lane)
            self.failUnlessEqual(len(lane.mapped_reads), 3)
            self.failUnlessEqual(lane.mapped_reads['Lambda.fa'], 1)
            self.failUnlessEqual(lane.mapped_reads['dm3/chr2L.fa'], 1)
            self.failUnlessEqual(lane.match_codes['U1'], 2)
            self.failUnlessEqual(lane.match_codes['NM'], 1)

        xml = eland.get_elements()
        # just make sure that element tree can serialize the tree
        xml_str = ElementTree.tostring(xml)
        e2 = gerald.ELAND(xml=xml)

        for key in eland:
            l1 = eland[key]
            l2 = e2[key]
            self.failUnlessEqual(l1.reads, l2.reads)
            self.failUnlessEqual(l1.sample_name, l2.sample_name)
            self.failUnlessEqual(l1.lane_id, l2.lane_id)
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
        self.failIfEqual(r2.image_analysis, None)
        self.failIfEqual(r2.bustard, None)
        self.failIfEqual(r2.gerald, None)


def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(RunfolderTests))
    return suite

if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
