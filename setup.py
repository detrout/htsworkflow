from setuptools import setup

setup(
  name="htsworkflow",
  description="some bots and other utilities to help deal with data from an illumina sequencer",
  author="Diane Trout & Brandon King",
  author_email="diane@caltech.edu",
  packages=["htsworkflow", 
            "htsworkflow.pipeline",
            "htsworkflow.frontend",
            "htsworkflow.frontend.fctracker",
            "htsworkflow.frontend.eland_config"           
             ],
  scripts=[
        'scripts/configure_pipeline',
        'scripts/copier',
        'scripts/gerald2bed.py',
        'scripts/library.py',
        'scripts/makebed',
        'scripts/spoolwatcher', 
        'scripts/rerun_eland.py',
        'scripts/retrieve_config',
        'scripts/runfolder',
        'scripts/runner',
        ],
)
