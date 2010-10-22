from setuptools import setup
from version import get_git_version

setup(
    name="htsworkflow",
    version=get_git_version(),
    description="Utilities to help manage high-through-put sequencing",
    author="Diane Trout, Brandon King",
    author_email="diane@caltech.edu",
    packages=["htsworkflow", 
              "htsworkflow.automation",
              "htsworkflow.pipelines",
              "htsworkflow.util",
              # django site
              "htsworkflow.frontend",
              "htsworkflow.frontend.analysis",
              "htsworkflow.frontend.eland_config",
              "htsworkflow.frontend.experiments",
              "htsworkflow.frontend.inventory",
              "htsworkflow.frontend.reports",
              "htsworkflow.frontend.samples",
              ],
    scripts=[
        'scripts/copier',
        'scripts/library.py',
        'scripts/makebed',
        'scripts/make-library-tree',
        'scripts/mark_archived_data',
        'scripts/qseq2fastq',
        'scripts/retrieve_config',
        'scripts/runfolder',
        'scripts/runner',
        'scripts/spoolwatcher', 
        'scripts/srf',
        'scripts/srf2fastq'
        ],
    )
