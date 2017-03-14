Introduction
============

HTSWorkflow is a set of tools that our lab has been using to
tracking libraries and flowcells and to submit the resulting fastqs to
a few data repositories.

One large portion of the repository is a Django web application that
is tracks flowcells and libraries. These modules are in:

.. code-block:: python

   samples
   experiments
   htsworkflow.frontend
   htsworkflow.settings
   htsworkflow.static
   htsworkflow.templates
   htsworkflow.util
   bcmagic
   eland_config
   inventory
   labels

Another collection of tools is scripts we use to submit things to the
ENCODE DCC.

.. code-block:: python

   encoode_submission
   htsworkflow.submission

There was a time where we were trying to add tools to automatically
detect when the sequencer was done and start running the Illumina
tools to generate the fastq files.

The main thing that's still being used is htsw-get-config to generate
the sample sheet for demultiplexing.

.. code-block:: python

   scripts
   htsworkflow.automation
   htsworkflow.pipeline
