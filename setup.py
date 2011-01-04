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
        "scripts/htsw-copier",
        "scripts/htsw-eland2bed",
        "scripts/htsw-elandseq",
        "scripts/htsw-gerald2bed",
        "scripts/htsw-get-config",
        "scripts/htsw-qseq2fastq",
        "scripts/htsw-record-runfolder",
        "scripts/htsw-runfolder",
        "scripts/htsw-runner",
        "scripts/htsw-spoolwatcher",
        "scripts/htsw-srf",
        "scripts/htsw-srf2fastq",
        "scripts/htsw-update-archive",
        ],
    )
