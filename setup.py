from setuptools import setup

setup(
  name="gaworkflow",
  description="some bots and other utilities to help deal with data from an illumina sequencer",
  author="Diane Trout & Brandon King",
  author_email="diane@caltech.edu",
  packages=["gaworkflow", 
            "gaworkflow.pipeline",
            "gaworkflow.frontend",
            "gaworkflow.frontend.fctracker",
            "gaworkflow.frontend.eland_config"           
             ],
  scripts=['scripts/spoolwatcher', 
           'scripts/copier',
           'scripts/runner',
           'scripts/retrieve_config',
           'scripts/configure_pipeline',
           'scripts/runfolder'],
)
