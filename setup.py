from setuptools import setup, find_packages
from version import get_git_version

setup(
    name="htsworkflow",
    version=get_git_version(),
    description="Utilities to help manage high-through-put sequencing",
    author="Diane Trout, Brandon King",
    author_email="diane@caltech.edu",
    packages=find_packages(),
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
        "scripts/htsw-validate",
        ],
    package_data = {
        '': ['*.turtle']
        },
    install_requires=['django >=1.1, <1.4',
                      'lxml >= 2.2.4',
                      'numpy >= 1.3',
                      'librdf >= 1.0.14',
                      'benderjab >= 0.2',
                      'httplib2',
                      'keyring',
                      ],
    include_package_data=True,

    )
