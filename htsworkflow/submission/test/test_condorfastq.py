#!/usr/bin/env python

import copy
import os
from pprint import pprint
import shutil
import tempfile
import unittest

from htsworkflow.submission.condorfastq import CondorFastqExtract
from htsworkflow.submission.results import ResultMap
from htsworkflow.util.rdfhelp import \
     add_default_schemas, load_string_into_model, dump_model
from htsworkflow.util.rdfinfer import Infer

FCDIRS = [
    'C02F9ACXX',
    'C02F9ACXX/C1-202',
    'C02F9ACXX/C1-202/Project_11154',
    'C02F9ACXX/C1-202/Project_12342_Index1',
    'C02F9ACXX/C1-202/Project_12342_Index2',
    'C02F9ACXX/C1-202/Project_12345',
    '42JUYAAXX',
    '42JUYAAXX/C1-76',
    '30221AAXX',
    '30221AAXX/C1-33',
    '30DY0AAXX',
    '30DY0AAXX/C1-151',
    '61MJTAAXX',
    '61MJTAAXX/C1-76',
]

DATAFILES = [
    'C02F9ACXX/C1-202/Project_11154/11154_NoIndex_L003_R1_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_11154/11154_NoIndex_L003_R1_002.fastq.gz',
    'C02F9ACXX/C1-202/Project_11154/11154_NoIndex_L003_R2_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_11154/11154_NoIndex_L003_R2_002.fastq.gz',
    'C02F9ACXX/C1-202/Project_12342_Index1/12342_GCCAAT_L004_R1_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_12342_Index1/12342_GCCAAT_L004_R2_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_12342_Index2/12342_CGATGT_L007_R1_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_12342_Index2/12342_CGATGT_L007_R2_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_12342_Index2/12342_CGATGT_L005_R1_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_12342_Index2/12342_CGATGT_L005_R2_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_12345/12345_CGATGT_L003_R1_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_12345/12345_CGATGT_L003_R1_002.fastq.gz',
    'C02F9ACXX/C1-202/Project_12345/12345_CGATGT_L003_R1_003.fastq.gz',
    'C02F9ACXX/C1-202/Project_12345/12345_CGATGT_L003_R2_001.fastq.gz',
    'C02F9ACXX/C1-202/Project_12345/12345_CGATGT_L003_R2_002.fastq.gz',
    'C02F9ACXX/C1-202/Project_12345/12345_CGATGT_L003_R2_003.fastq.gz',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l1_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l2_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l3_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l4_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l6_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l7_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l8_r1.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l1_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l1_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l2_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l3_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l4_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l6_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l7_r2.tar.bz2',
    '42JUYAAXX/C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l8_r2.tar.bz2',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_1.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_2.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_3.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_4.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_5.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_6.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_7.srf',
    '30221AAXX/C1-33/woldlab_090425_HWI-EAS229_0110_30221AAXX_8.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_1.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_2.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_3.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_4.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_5.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_6.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_7.srf',
    '30DY0AAXX/C1-151/woldlab_090725_HWI-EAS229_0110_30DY0AAXX_8.srf',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l1_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l2_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l3_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l4_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l5_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l6_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l7_r1.tar.bz2',
    '61MJTAAXX/C1-76/woldlab_100826_HSI-123_0001_61MJTAAXX_l8_r1.tar.bz2',
]

lib_turtle = """@prefix : <http://www.w3.org/1999/xhtml> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#> .
@prefix seqns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#> .
@prefix invns: <http://jumpgate.caltech.edu/wiki/InventoryOntology#> .

<http://localhost/library/10000/> a libns:Library .
<http://localhost/library/1331/> a libns:Library .
<http://localhost/library/1421/> a libns:Library .
<http://localhost/library/1661/> a libns:Library .

<http://localhost/flowcell/30221AAXX/>
        a libns:IlluminaFlowcell ;
        libns:read_length 33 ;
        libns:flowcell_type "Single"@en ;
        libns:date "2012-01-19T20:23:26"^^xsd:dateTime;
        libns:has_lane <http://localhost/lane/3401> ;
        libns:has_lane <http://localhost/lane/3402> ;
        libns:has_lane <http://localhost/lane/3403> ;
        libns:has_lane <http://localhost/lane/3404> ;
        libns:has_lane <http://localhost/lane/3405> ;
        libns:has_lane <http://localhost/lane/3406> ;
        libns:has_lane <http://localhost/lane/3407> ;
        libns:has_lane <http://localhost/lane/3408> ;
        libns:flowcell_id "30221AAXX"@en .

<http://localhost/lane/3401>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30221AAXX/> ;
        libns:library <http://localhost/library/10000/> ;
        libns:lane_number 1 .
<http://localhost/lane/3402>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30221AAXX/> ;
        libns:library <http://localhost/library/10000/> ;
        libns:lane_number 2 .
<http://localhost/lane/3403>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30221AAXX/> ;
        libns:library <http://localhost/library/10000/> ;
        libns:lane_number 3 .
<http://localhost/lane/3404>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30221AAXX/> ;
        libns:library <http://localhost/library/11154/> ;
        libns:lane_number 4 .
        # paired_end 1;
        # read_length 33;
        # status "Unknown"@en .
<http://localhost/lane/3405>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30221AAXX/> ;
        libns:library <http://localhost/library/10000/> ;
        libns:lane_number 5 .
<http://localhost/lane/3406>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30221AAXX/> ;
        libns:library <http://localhost/library/10000/> ;
        libns:lane_number 6 .
<http://localhost/lane/3407>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30221AAXX/> ;
        libns:library <http://localhost/library/10000/> ;
        libns:lane_number 7 .
<http://localhost/lane/3408>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30221AAXX/> ;
        libns:library <http://localhost/library/10000/> ;
        libns:lane_number 8 .

<http://localhost/flowcell/42JUYAAXX/>
        a libns:IlluminaFlowcell ;
        libns:read_length 76 ;
        libns:flowcell_type "Paired"@en ;
        libns:date "2012-01-19T20:23:26"^^xsd:dateTime;
        libns:has_lane <http://localhost/lane/4201> ;
        libns:has_lane <http://localhost/lane/4202> ;
        libns:has_lane <http://localhost/lane/4203> ;
        libns:has_lane <http://localhost/lane/4204> ;
        libns:has_lane <http://localhost/lane/4205> ;
        libns:has_lane <http://localhost/lane/4206> ;
        libns:has_lane <http://localhost/lane/4207> ;
        libns:has_lane <http://localhost/lane/4208> ;
        libns:flowcell_id "42JUYAAXX"@en .

<http://localhost/lane/4201>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/42JUYAAXX/> ;
        libns:library <http://localhost/library/1421/> ;
        libns:lane_number 1 .
<http://localhost/lane/4202>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/42JUYAAXX/> ;
        libns:library <http://localhost/library/1421/> ;
        libns:lane_number 2 .
<http://localhost/lane/4203>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/42JUYAAXX/> ;
        libns:library <http://localhost/library/1421/> ;
        libns:lane_number 3 .
<http://localhost/lane/4204>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/42JUYAAXX/> ;
        libns:library <http://localhost/library/1421/> ;
        libns:lane_number 4 .
<http://localhost/lane/4205>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/42JUYAAXX/> ;
        libns:library <http://localhost/library/11154/> ;
        libns:lane_number 5 .
        # paired_end 1;
        # read_length 76;
        # status "Unknown"@en .
<http://localhost/lane/4206>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/42JUYAAXX/> ;
        libns:library <http://localhost/library/1421/> ;
        libns:lane_number 6 .
<http://localhost/lane/4207>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/42JUYAAXX/> ;
        libns:library <http://localhost/library/1421/> ;
        libns:lane_number 7 .
<http://localhost/lane/4208>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/42JUYAAXX/> ;
        libns:library <http://localhost/library/1421/> ;
        libns:lane_number 8 .

<http://localhost/flowcell/61MJTAAXX/>
        a libns:IlluminaFlowcell ;
        libns:read_length 76 ;
        libns:flowcell_type "Single"@en ;
        libns:date "2012-01-19T20:23:26"^^xsd:dateTime;
        libns:has_lane <http://localhost/lane/6601> ;
        libns:has_lane <http://localhost/lane/6602> ;
        libns:has_lane <http://localhost/lane/6603> ;
        libns:has_lane <http://localhost/lane/6604> ;
        libns:has_lane <http://localhost/lane/6605> ;
        libns:has_lane <http://localhost/lane/6606> ;
        libns:has_lane <http://localhost/lane/6607> ;
        libns:has_lane <http://localhost/lane/6608> ;
        libns:flowcell_id "61MJTAAXX"@en .

<http://localhost/lane/6601>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/61MJTAAXX/> ;
        libns:library <http://localhost/library/1661/> ;
        libns:lane_number 1 .
<http://localhost/lane/6602>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/61MJTAAXX/> ;
        libns:library <http://localhost/library/1661/> ;
        libns:lane_number 2 .
<http://localhost/lane/6603>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/61MJTAAXX/> ;
        libns:library <http://localhost/library/1661/> ;
        libns:lane_number 3 .
<http://localhost/lane/6604>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/61MJTAAXX/> ;
        libns:library <http://localhost/library/1661/> ;
        libns:lane_number 4 .
<http://localhost/lane/6605>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/61MJTAAXX/> ;
        libns:library <http://localhost/library/1661/> ;
        libns:lane_number 5 .
<http://localhost/lane/6606>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/61MJTAAXX/> ;
        libns:library <http://localhost/library/11154/> ;
        libns:lane_number 6 .
        # paired_end 1;
        # read_length 76;
        # status "Unknown"@en .
<http://localhost/lane/6607>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/61MJTAAXX/> ;
        libns:library <http://localhost/library/1661/> ;
        libns:lane_number 7 .
<http://localhost/lane/6608>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/61MJTAAXX/> ;
        libns:library <http://localhost/library/1661/> ;
        libns:lane_number 8 .

<http://localhost/flowcell/30DY0AAXX/>
        a libns:IlluminaFlowcell ;
        libns:read_length 76 ;
        libns:flowcell_type "Paired"@en ;
        libns:date "2012-01-19T20:23:26"^^xsd:dateTime;
        libns:has_lane <http://localhost/lane/3801> ;
        libns:has_lane <http://localhost/lane/3802> ;
        libns:has_lane <http://localhost/lane/3803> ;
        libns:has_lane <http://localhost/lane/3804> ;
        libns:has_lane <http://localhost/lane/3805> ;
        libns:has_lane <http://localhost/lane/3806> ;
        libns:has_lane <http://localhost/lane/3807> ;
        libns:has_lane <http://localhost/lane/3808> ;
        libns:flowcell_id "30DY0AAXX"@en .

<http://localhost/lane/3801>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30DY0AAXX/> ;
        libns:library <http://localhost/library/1331/> ;
        libns:lane_number 1 .
<http://localhost/lane/3802>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30DY0AAXX/> ;
        libns:library <http://localhost/library/1331/> ;
        libns:lane_number 2 .
<http://localhost/lane/3803>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30DY0AAXX/> ;
        libns:library <http://localhost/library/1331/> ;
        libns:lane_number 3 .
<http://localhost/lane/3804>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30DY0AAXX/> ;
        libns:library <http://localhost/library/1331/> ;
        libns:lane_number 4 .
<http://localhost/lane/3805>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30DY0AAXX/> ;
        libns:library <http://localhost/library/1331/> ;
        libns:lane_number 5 .
<http://localhost/lane/3806>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30DY0AAXX/> ;
        libns:library <http://localhost/library/1331/> ;
        libns:lane_number 6 .
<http://localhost/lane/3807>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30DY0AAXX/> ;
        libns:library <http://localhost/library/1331/> ;
        libns:lane_number 7 .
<http://localhost/lane/3808>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/30DY0AAXX/> ;
        libns:library <http://localhost/library/11154/> ;
        libns:lane_number 8 .
        # paired_end 1;
        # read_length 76;
        # status "Unknown"@en .

<http://localhost/flowcell/C02F9ACXX/>
        a libns:IlluminaFlowcell ;
        libns:read_length 101 ;
        libns:flowcell_type "Paired"@en ;
        libns:date "2012-01-19T20:23:26"^^xsd:dateTime;
        libns:has_lane <http://localhost/lane/12300> ;
        libns:has_lane <http://localhost/lane/12500> ;
        libns:flowcell_id "C02F9ACXX"@en .

<http://localhost/lane/12300>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/C02F9ACXX/> ;
        libns:library <http://localhost/library/12345/> ;
        libns:lane_number 3 .
        # paired_end 1;
        # read_length 101;
        # status "Unknown"@en .

<http://localhost/lane/12500>
        a libns:IlluminaLane ;
        libns:flowcell <http://localhost/flowcell/C02F9ACXX/> ;
        libns:library <http://localhost/library/11154/> ;
        libns:lane_number 3 .
        # paired_end 1;
        # read_length 101;
        # status "Unknown"@en .

<http://localhost/library/11154/>
        a libns:Library ;
        libns:affiliation "TSR"@en;
        libns:concentration "29.7";
        libns:date "2012-12-28T00:00:00"^^xsd:dateTime ;
        libns:experiment_type "RNA-seq"@en ;
        libns:gel_cut 300 ;
        libns:has_lane <http://localhost/lane/3404> ;
        libns:has_lane <http://localhost/lane/4205> ;
        libns:has_lane <http://localhost/lane/6606> ;
        libns:has_lane <http://localhost/lane/3808> ;
        libns:has_lane <http://localhost/lane/12500> ;
        libns:insert_size 2000 ;
        libns:library_id "11154"@en ;
        libns:library_type "Paired End (Multiplexed)"@en ;
        libns:made_by "Gary Gygax"@en ;
        libns:name "Paired Ends ASDF"@en ;
        libns:replicate "1"@en;
        libns:species "Mus musculus"@en ;
        libns:stopping_point "Completed"@en ;
        libns:total_unique_locations 8841201 .
        # cell_line


<http://localhost/library/12345/>
        a libns:Library ;
        libns:affiliation "TSR"@en;
        libns:concentration "12.345";
        libns:cell_line "Unknown"@en ;
        libns:date "2012-12-28T00:00:00"^^xsd:dateTime ;
        libns:experiment_type "RNA-seq"@en ;
        libns:gel_cut 300 ;
        libns:has_lane <http://localhost/lane/12300> ;
        libns:insert_size 2000 ;
        libns:library_id "12345"@en ;
        libns:library_type "Paired End (Multiplexed)"@en ;
        libns:made_by "Gary Gygax"@en ;
        libns:name "Paired Ends THING"@en ;
        libns:replicate "1"@en;
        libns:species "Mus musculus"@en ;
        libns:stopping_point "Completed"@en ;
        libns:total_unique_locations 8841201 .
        # cell_line
"""
HOST = "http://localhost"

class TestCondorFastq(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()

        self.tempdir = tempfile.mkdtemp(prefix='condorfastq_test')
        self.flowcelldir = os.path.join(self.tempdir, 'flowcells')
        os.mkdir(self.flowcelldir)

        self.logdir = os.path.join(self.tempdir, 'log')
        os.mkdir(self.logdir)

        for d in FCDIRS:
            os.mkdir(os.path.join(self.flowcelldir, d))

        for f in DATAFILES:
            filename = os.path.join(self.flowcelldir, f)
            with open(filename, 'w') as stream:
                stream.write('testfile')

        self.result_map = ResultMap()
        for lib_id in [u'11154', u'12345']:
            subname = 'sub-%s' % (lib_id,)
            sub_dir = os.path.join(self.tempdir, subname)
            os.mkdir(sub_dir)
            self.result_map[lib_id] =  sub_dir

        self.extract = CondorFastqExtract(HOST,
                                          self.flowcelldir,
                                          self.logdir)
        load_string_into_model(self.extract.model, 'turtle', lib_turtle)
        add_default_schemas(self.extract.model)
        inference = Infer(self.extract.model)
        errmsgs = list(inference.run_validation())
        self.assertEqual(len(errmsgs), 0)

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        os.chdir(self.cwd)

    def test_find_relavant_flowcell_ids(self):
        expected = set(('30221AAXX',
                        '42JUYAAXX',
                        '61MJTAAXX',
                        '30DY0AAXX',
                        'C02F9ACXX'))
        flowcell_ids = self.extract.find_relavant_flowcell_ids()
        self.assertEqual(flowcell_ids, expected)

    def test_find_archive_sequence(self):
        seqs = self.extract.find_archive_sequence_files(self.result_map)

        expected = set([
            (u'11154', u'42JUYAAXX', 5, 1, 76, True, 'qseq'),
            (u'11154', u'42JUYAAXX', 5, 2, 76, True, 'qseq'),
            (u'11154', u'61MJTAAXX', 6, 1, 76, False, 'qseq'),
            (u'11154', u'C02F9ACXX', 3, 2, 202, True, 'split_fastq'),
            (u'11154', u'C02F9ACXX', 3, 1, 202, True, 'split_fastq'),
            (u'11154', u'C02F9ACXX', 3, 1, 202, True, 'split_fastq'),
            (u'11154', u'C02F9ACXX', 3, 2, 202, True, 'split_fastq'),
            (u'12345', u'C02F9ACXX', 3, 1, 202, True, 'split_fastq'),
            (u'12345', u'C02F9ACXX', 3, 2, 202, True, 'split_fastq'),
            (u'12345', u'C02F9ACXX', 3, 2, 202, True, 'split_fastq'),
            (u'12345', u'C02F9ACXX', 3, 1, 202, True, 'split_fastq'),
            (u'12345', u'C02F9ACXX', 3, 1, 202, True, 'split_fastq'),
            (u'12345', u'C02F9ACXX', 3, 2, 202, True, 'split_fastq'),
            (u'11154', u'30221AAXX', 4, 1, 33, False, 'srf'),
            (u'11154', u'30DY0AAXX', 8, 1, 151, True, 'srf')
        ])
        found = set([(l.library_id, l.flowcell_id, l.lane_number, l.read, l.cycle, l.ispaired, l.filetype) for l in seqs])
        self.assertEqual(expected, found)

    def test_find_needed_targets(self):
        lib_db = self.extract.find_archive_sequence_files(self.result_map)

        needed_targets = self.extract.update_fastq_targets(self.result_map,
                                                           lib_db)
        self.assertEqual(len(needed_targets), 9)
        srf_30221 = needed_targets[
            self.result_map['11154'] + u'/11154_30221AAXX_c33_l4.fastq']
        qseq_42JUY_r1 = needed_targets[
            self.result_map['11154'] + u'/11154_42JUYAAXX_c76_l5_r1.fastq']
        qseq_42JUY_r2 = needed_targets[
            self.result_map['11154'] + u'/11154_42JUYAAXX_c76_l5_r2.fastq']
        qseq_61MJT = needed_targets[
            self.result_map['11154'] + u'/11154_61MJTAAXX_c76_l6.fastq']
        split_C02F9_r1 = needed_targets[
            self.result_map['11154'] + u'/11154_C02F9ACXX_c202_l3_r1.fastq']
        split_C02F9_r2 = needed_targets[
            self.result_map['11154'] + u'/11154_C02F9ACXX_c202_l3_r2.fastq']

        self.assertEqual(len(srf_30221['srf']), 1)
        self.assertEqual(len(qseq_42JUY_r1['qseq']), 1)
        self.assertEqual(len(qseq_42JUY_r2['qseq']), 1)
        self.assertEqual(len(qseq_61MJT['qseq']), 1)
        self.assertEqual(len(split_C02F9_r1['split_fastq']), 2)
        self.assertEqual(len(split_C02F9_r2['split_fastq']), 2)

    def test_generate_fastqs(self):
        commands = self.extract.build_condor_arguments(self.result_map)

        srf = commands['srf']
        qseq = commands['qseq']
        split = commands['split_fastq']

        self.assertEqual(len(srf), 2)
        self.assertEqual(len(qseq), 3)
        self.assertEqual(len(split), 4)

        srf_data = {
            os.path.join(self.result_map['11154'],
                         '11154_30221AAXX_c33_l4.fastq'): {
                'mid': None,
                'ispaired': False,
                'sources': [u'woldlab_090425_HWI-EAS229_0110_30221AAXX_4.srf'],
                'flowcell': u'30221AAXX',
                'target': os.path.join(self.result_map['11154'],
                                       u'11154_30221AAXX_c33_l4.fastq'),
            },
            os.path.join(self.result_map['11154'],
                         '11154_30DY0AAXX_c151_l8_r1.fastq'): {
                'mid': None,
                'ispaired': True,
                'flowcell': u'30DY0AAXX',
                'sources': [u'woldlab_090725_HWI-EAS229_0110_30DY0AAXX_8.srf'],
                'mid': 76,
                'target':
                    os.path.join(self.result_map['11154'],
                                 u'11154_30DY0AAXX_c151_l8_r1.fastq'),
                'target_right':
                    os.path.join(self.result_map['11154'],
                                 u'11154_30DY0AAXX_c151_l8_r2.fastq'),
            }
        }
        for args in srf:
            expected = srf_data[args['target']]
            self.assertEqual(args['ispaired'], expected['ispaired'])
            self.assertEqual(len(args['sources']), 1)
            _, source_filename = os.path.split(args['sources'][0])
            self.assertEqual(source_filename, expected['sources'][0])
            self.assertEqual(args['target'], expected['target'])
            if args['ispaired']:
                self.assertEqual(args['target_right'],
                                     expected['target_right'])
            if 'mid' in expected:
                self.assertEqual(args['mid'], expected['mid'])

        qseq_data = {
            os.path.join(self.result_map['11154'],
                         '11154_42JUYAAXX_c76_l5_r1.fastq'): {
                'istar': True,
                'ispaired': True,
                'sources': [
                    u'woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r1.tar.bz2']
            },
            os.path.join(self.result_map['11154'],
                         '11154_42JUYAAXX_c76_l5_r2.fastq'): {
                'istar': True,
                'ispaired': True,
                'sources': [
                    u'woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r2.tar.bz2']
            },
            os.path.join(self.result_map['11154'],
                         '11154_61MJTAAXX_c76_l6.fastq'): {
                'istar': True,
                'ispaired': False,
                'sources': [
                    u'woldlab_100826_HSI-123_0001_61MJTAAXX_l6_r1.tar.bz2'],
            },
        }
        for args in qseq:
            expected = qseq_data[args['target']]
            self.assertEqual(args['istar'], expected['istar'])
            self.assertEqual(args['ispaired'], expected['ispaired'])
            for i in range(len(expected['sources'])):
                _, filename = os.path.split(args['sources'][i])
                self.assertEqual(filename, expected['sources'][i])


        split_test = dict((( x['target'], x) for x in
            [{'sources': [u'11154_NoIndex_L003_R1_001.fastq.gz',
                         u'11154_NoIndex_L003_R1_002.fastq.gz'],
             'pyscript': 'desplit_fastq.pyc',
             'target': u'11154_C02F9ACXX_c202_l3_r1.fastq'},
            {'sources': [u'11154_NoIndex_L003_R2_001.fastq.gz',
                         u'11154_NoIndex_L003_R2_002.fastq.gz'],
             'pyscript': 'desplit_fastq.pyc',
             'target': u'11154_C02F9ACXX_c202_l3_r2.fastq'},
            {'sources': [u'12345_CGATGT_L003_R1_001.fastq.gz',
                         u'12345_CGATGT_L003_R1_002.fastq.gz',
                         u'12345_CGATGT_L003_R1_003.fastq.gz',
                         ],
             'pyscript': 'desplit_fastq.pyc',
             'target': u'12345_C02F9ACXX_c202_l3_r1.fastq'},
            {'sources': [u'12345_CGATGT_L003_R2_001.fastq.gz',
                         u'12345_CGATGT_L003_R2_002.fastq.gz',
                         u'12345_CGATGT_L003_R2_003.fastq.gz',
                         ],
             'pyscript': 'desplit_fastq.pyc',
             'target': u'12345_C02F9ACXX_c202_l3_r2.fastq'}
             ]
         ))
        for arg in split:
            _, target = os.path.split(arg['target'])
            pyscript = split_test[target]['pyscript']
            self.assertTrue(arg['pyscript'].endswith(pyscript))
            filename = split_test[target]['target']
            self.assertTrue(arg['target'].endswith(filename))
            for s_index in range(len(arg['sources'])):
                s1 = arg['sources'][s_index]
                s2 = split_test[target]['sources'][s_index]
                self.assertTrue(s1.endswith(s2))

    def test_create_scripts(self):
        self.extract.create_scripts(self.result_map)

        self.assertTrue(os.path.exists('srf.condor'))
        with open('srf.condor', 'r') as srf:
            arguments = [ l for l in srf if l.startswith('argument') ]
            arguments.sort()
            self.assertEqual(len(arguments), 2)
            self.assertTrue('sub-11154/11154_30221AAXX_c33_l4.fastq'
                            in arguments[0])
            self.assertTrue(
                'sub-11154/11154_30DY0AAXX_c151_l8_r2.fastq' in
                arguments[1])

        self.assertTrue(os.path.exists('qseq.condor'))
        with open('qseq.condor', 'r') as srf:
            arguments = [ l for l in srf if l.startswith('argument') ]
            arguments.sort()
            self.assertEqual(len(arguments), 3)
            self.assertTrue('sub-11154/11154_42JUYAAXX_c76_l5_r1.fastq ' in
                            arguments[0])
            self.assertTrue(
                'C1-76/woldlab_100826_HSI-123_0001_42JUYAAXX_l5_r2.tar.bz2' in
                arguments[1])
            self.assertTrue('61MJTAAXX_c76_l6.fastq -f 61MJTAAXX' in
                            arguments[2])

        self.assertTrue(os.path.exists('split_fastq.condor'))
        with open('split_fastq.condor', 'r') as split:
            arguments = [ l for l in split if l.startswith('argument') ]
            arguments.sort()
            self.assertEqual(len(arguments), 4)
            # Lane 3 Read 1
            self.assertTrue('11154_NoIndex_L003_R1_001.fastq.gz' in \
                            arguments[0])
            # Lane 3 Read 2
            self.assertTrue('11154_NoIndex_L003_R2_002.fastq.gz' in \
                            arguments[1])
            # Lane 3 Read 1
            self.assertTrue('12345_CGATGT_L003_R1_001.fastq.gz' in arguments[2])
            self.assertTrue('12345_CGATGT_L003_R1_002.fastq.gz' in arguments[2])
            self.assertTrue('12345_CGATGT_L003_R1_003.fastq.gz' in arguments[2])
            self.assertTrue('12345_C02F9ACXX_c202_l3_r1.fastq' in arguments[2])

            # Lane 3 Read 2
            self.assertTrue('12345_CGATGT_L003_R2_001.fastq.gz' in arguments[3])
            self.assertTrue('12345_CGATGT_L003_R2_002.fastq.gz' in arguments[3])
            self.assertTrue('12345_CGATGT_L003_R2_003.fastq.gz' in arguments[3])
            self.assertTrue('12345_C02F9ACXX_c202_l3_r2.fastq' in arguments[3])


def suite():
    suite = unittest.makeSuite(TestCondorFastq, 'test')
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')

