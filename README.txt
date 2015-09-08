Introduction
============

This contains our LIMS system and a collections of utilities
to help manage curation and submission of data.

Fastq Conversion
----------------

Over time there were several different attempts to capture
and store "fastq-like" data. HTS-Workflow has at one time or
another supported NCBI srf files, Illumina qseq files, and 
fastq files.

Because all of the current submitting agencies want fastq files.
There are some utilities to convert whatever is stored in our sequence 
archive to fastq files.

The current ENCODE submission script is encode_submission/encode3.py
and it has a --fastq option that given a mapping file will try to 
go find all the flowcells and generate condor scripts using
the lower level conversion utilities 

 * htsworkflow/pipelines/desplit_fastq.py
 * htsworkflow/pipelines/qseq2fastq.py
 * htsworkflow/pipelines/srf2fastq.py

desplit_fastq converts a list of fastq files into a single fastq file.
qseq2fastq takes a collection of qseq files or a tar-file containing 
qseq files and converts it into a fastq file. and srf2fastq converts
the NCBI srf files. 

Note: srf2fastq depends on the stadenio tools.

The encode3.py --fastq mode reads a mapping file that contains

library_id destination_directory

encode3.py has a '--compression gzip'  option for if you want the
resulting fastq file to be compressed as a gzip file.


